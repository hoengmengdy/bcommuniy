from flask import Blueprint, g, jsonify, request
from werkzeug.security import generate_password_hash
from backend.extensions import db
from backend.models import Conversation, ConversationMember, User
from backend.services.auth import admin_required, create_user, login_required, require_owner
from backend.utils.validation import APIError, body, choice, email, page, password, string, strings, url

bp = Blueprint("users", __name__)
PROFILE_FIELDS = ("name", "bio", "role", "skills", "avatar", "phone")


def update_profile(user, data):
    for key, value in data.items():
        if key == "role":
            value = choice(value, key, ("Beginner", "Senior", "Teacher"))
        elif key == "skills":
            value = strings(value, key)
        elif key == "avatar":
            value = url(value, key) or ""
        else:
            value = string(value, key, {"name": 120, "phone": 40}.get(key, 2000), True if key == "name" else False)
            if value is None:
                raise APIError(f"{key} cannot be null.")
        setattr(user, key, value)


@bp.get("/users")
@admin_required
def list_users():
    rows, meta = page(db.select(User).order_by(User.id))
    return jsonify(data=[u.to_dict(admin=True) for u in rows], meta=meta)


@bp.post("/users")
@admin_required
def add_user():
    user = create_user(body(("name", "email", "password", "role")), admin=True)
    db.session.commit()
    return jsonify(data=user.to_dict(admin=True)), 201


@bp.get("/users/<int:user_id>")
@login_required
def get_user(user_id):
    user = db.get_or_404(User, user_id)
    return jsonify(data=user.to_dict(private=user.id == g.user.id, admin=g.user.account_role == "Admin"))


@bp.put("/users/<int:user_id>")
@login_required
def edit_user(user_id):
    user = db.get_or_404(User, user_id)
    require_owner(user.id)
    data = body(("name", "email", "password", "role", "status"))
    if g.user.account_role != "Admin" and ("role" in data or "status" in data):
        raise APIError("Only administrators may change account roles or status.", 403)
    if user.account_role == "Admin" and (
        data.get("role", "Admin") != "Admin" or data.get("status", "Active") != "Active"
    ):
        protect_last_admin(user)
    for key, value in data.items():
        if key == "name":
            user.name = string(value, key, 120, True)
        elif key == "email":
            user.email = email(value)
        elif key == "password":
            user.password_hash = generate_password_hash(password(value))
            user.auth_version += 1
        elif key == "role":
            user.account_role = choice(value, key, ("User", "Admin"))
        elif key == "status":
            user.status = choice(value, key, ("Active", "Inactive"))
            user.auth_version += 1
    db.session.commit()
    return jsonify(data=user.to_dict(private=True, admin=g.user.account_role == "Admin"))


def protect_last_admin(user):
    other = db.session.scalar(db.select(User.id).where(
        User.account_role == "Admin", User.status == "Active", User.id != user.id))
    if not other:
        raise APIError("The last active administrator cannot be removed or demoted.", 409)


@bp.delete("/users/<int:user_id>")
@login_required
def delete_user(user_id):
    user = db.get_or_404(User, user_id)
    require_owner(user.id)
    if user.account_role == "Admin":
        protect_last_admin(user)
    # Direct conversations must disappear for both participants when either account is deleted.
    conversations = db.session.scalars(db.select(Conversation).join(ConversationMember).where(
        ConversationMember.user_id == user.id)).all()
    for conversation in conversations:
        db.session.delete(conversation)
    db.session.delete(user)
    db.session.commit()
    return jsonify(data={"message": "User deleted."})


@bp.get("/profile")
@login_required
def profile():
    return jsonify(data=g.user.to_dict(private=True))


@bp.put("/profile")
@login_required
def edit_profile():
    update_profile(g.user, body(PROFILE_FIELDS))
    db.session.commit()
    return jsonify(data=g.user.to_dict(private=True))


@bp.get("/members")
def members():
    rows, meta = page(db.select(User).where(User.status == "Active").order_by(User.name))
    return jsonify(data=[u.to_dict() for u in rows], meta=meta)


@bp.get("/mentors")
def mentors():
    query = db.select(User).where(User.status == "Active", User.role.in_(("Senior", "Teacher")))
    skill = request.args.get("skill", "").strip().lower()
    rows, meta = page(query.order_by(User.reputation.desc(), User.id))
    return jsonify(data=[u.to_dict() for u in rows
                         if not skill or any(skill in s.lower() for s in u.skills)], meta=meta)


@bp.get("/leaderboard")
def leaderboard():
    rows, meta = page(db.select(User).where(User.status == "Active").order_by(
        User.reputation.desc(), User.id))
    return jsonify(data=[dict(u.to_dict(), rank=meta["perPage"] * (meta["page"] - 1) + i + 1)
                         for i, u in enumerate(rows)], meta=meta)
