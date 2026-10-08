from flask import Blueprint, current_app, g, jsonify
from werkzeug.security import check_password_hash
from backend.extensions import db
from backend.models import User
from backend.services.auth import create_user, issue_token, login_required
from backend.utils.validation import APIError, body, email, string

bp = Blueprint("auth", __name__)


def response(user, status=200):
    token = issue_token(user)
    db.session.commit()
    return jsonify(data={"user": user.to_dict(private=True), "token": token,
                         "expiresIn": current_app.config["TOKEN_MAX_AGE"]}), status


@bp.post("/auth/register")
def register():
    return response(create_user(body(("name", "email", "password"))), 201)


@bp.post("/auth/login")
def login():
    data = body(("email", "password"))
    address = email(data.get("email"))
    secret = data.get("password")
    if not isinstance(secret, str) or len(secret) > 128:
        raise APIError("Invalid email or password.", 401)
    user = db.session.scalar(db.select(User).where(User.email == address))
    # Check a real hash only when an account exists; errors never disclose status.
    if not user or not check_password_hash(user.password_hash, secret) or user.status != "Active":
        raise APIError("Invalid email or password.", 401)
    return response(user)


@bp.get("/auth/me")
@login_required
def me():
    return jsonify(data=g.user.to_dict(private=True))


@bp.post("/auth/logout")
@login_required
def logout():
    db.session.delete(g.auth_session)
    db.session.commit()
    return jsonify(data={"message": "Signed out."})
