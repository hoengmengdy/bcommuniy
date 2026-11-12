"""Administrator tools: statistics, account actions, moderation and broadcasts.

Every route here requires an active administrator session.
"""
from collections import Counter
from datetime import timedelta

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from werkzeug.security import generate_password_hash

from backend.extensions import db
from backend.models import (Article, AuthSession, Call, Comment, Conversation, ConversationMember,
                            Event, Job, Message, Notification, Post, PostLike, Task, User, iso, now)
from backend.routes.users import protect_last_admin
from backend.services.auth import admin_required
from backend.utils.validation import APIError, body, choice, integer, page, password, string

bp = Blueprint("admin", __name__)
BULK_ACTIONS = ("activate", "deactivate", "promote", "demote", "logout", "delete")


def count(model, *where):
    query = db.select(func.count()).select_from(model)
    if where:
        query = query.where(*where)
    return db.session.scalar(query) or 0


def daily(values, days):
    """Count datetimes per day for the last `days` days, oldest first."""
    today = now().date()
    buckets = Counter(value.date() for value in values if value)
    return [{"date": (today - timedelta(days=offset)).isoformat(),
             "count": buckets.get(today - timedelta(days=offset), 0)}
            for offset in range(days - 1, -1, -1)]


@bp.get("/admin/stats")
@admin_required
def stats():
    days = min(integer(request.args.get("days", "14"), "days"), 90)
    since = now() - timedelta(days=days)
    signups = db.session.scalars(db.select(User.joined_at).where(User.joined_at >= since)).all()
    posted = db.session.scalars(db.select(Post.created_at).where(Post.created_at >= since)).all()
    commented = db.session.scalars(db.select(Comment.created_at).where(Comment.created_at >= since)).all()
    messaged = db.session.scalars(db.select(Message.created_at).where(Message.created_at >= since)).all()

    tag_rows = db.session.execute(db.select(Post.tag, func.count()).group_by(Post.tag)
                                  .order_by(func.count().desc()).limit(8)).all()
    top_rows = db.session.execute(
        db.select(User, func.count(Post.id).label("posts")).join(Post, Post.author_id == User.id)
        .group_by(User.id).order_by(func.count(Post.id).desc()).limit(5)).all()
    recent_users = db.session.scalars(db.select(User).order_by(User.joined_at.desc()).limit(5)).all()

    return jsonify(data={
        "totals": {
            "users": count(User), "activeUsers": count(User, User.status == "Active"),
            "inactiveUsers": count(User, User.status != "Active"),
            "admins": count(User, User.account_role == "Admin"),
            "posts": count(Post), "questions": count(Post, Post.is_question.is_(True)),
            "solved": count(Post, Post.is_question.is_(True), Post.is_solved.is_(True)),
            "comments": count(Comment), "likes": count(PostLike),
            "conversations": count(Conversation), "messages": count(Message), "calls": count(Call),
            "articles": count(Article), "jobs": count(Job), "events": count(Event), "tasks": count(Task),
            "sessions": count(AuthSession),
        },
        "activity": {"signups": daily(signups, days), "posts": daily(posted, days),
                     "comments": daily(commented, days), "messages": daily(messaged, days)},
        "topTags": [{"tag": tag, "count": total} for tag, total in tag_rows],
        "topContributors": [dict(user.to_dict(), posts=posts) for user, posts in top_rows],
        "recentUsers": [user.to_dict(admin=True) for user in recent_users],
    })


def target_user(user_id):
    user = db.get_or_404(User, user_id)
    return user


def revoke_sessions(user):
    user.auth_version += 1
    db.session.execute(db.delete(AuthSession).where(AuthSession.user_id == user.id))


@bp.post("/admin/users/<int:user_id>/password")
@admin_required
def reset_password(user_id):
    user = target_user(user_id)
    user.password_hash = generate_password_hash(password(body(("password",)).get("password")), method="scrypt")
    revoke_sessions(user)
    db.session.commit()
    return jsonify(data=user.to_dict(admin=True))


@bp.post("/admin/users/<int:user_id>/logout")
@admin_required
def force_logout(user_id):
    user = target_user(user_id)
    if user.id == g.user.id:
        raise APIError("Use Sign Out to end your own session.")
    revoke_sessions(user)
    db.session.commit()
    return jsonify(data=user.to_dict(admin=True))


@bp.put("/admin/users/<int:user_id>/reputation")
@admin_required
def set_reputation(user_id):
    user = target_user(user_id)
    user.reputation = integer(body(("reputation",)).get("reputation"), "reputation", 0)
    db.session.commit()
    return jsonify(data=user.to_dict(admin=True))


def delete_account(user):
    if user.account_role == "Admin":
        protect_last_admin(user)
    conversations = db.session.scalars(db.select(Conversation).join(ConversationMember).where(
        ConversationMember.user_id == user.id)).all()
    for conversation in conversations:
        db.session.delete(conversation)
    db.session.delete(user)


@bp.post("/admin/users/bulk")
@admin_required
def bulk_users():
    data = body(("ids", "action"))
    action = choice(data.get("action"), "action", BULK_ACTIONS)
    ids = data.get("ids")
    if not isinstance(ids, list) or not ids or len(ids) > 500:
        raise APIError("ids must be a list of 1 to 500 user ids.")
    ids = {integer(value, "ids") for value in ids}
    if g.user.id in ids and action in ("deactivate", "demote", "logout", "delete"):
        raise APIError("You cannot apply this action to your own account.")
    users = db.session.scalars(db.select(User).where(User.id.in_(ids))).all()
    for user in users:
        if action == "activate":
            user.status = "Active"
        elif action == "deactivate":
            if user.account_role == "Admin":
                protect_last_admin(user)
            user.status = "Inactive"
            revoke_sessions(user)
        elif action == "promote":
            user.account_role = "Admin"
        elif action == "demote":
            if user.account_role == "Admin":
                protect_last_admin(user)
            user.account_role = "User"
        elif action == "logout":
            revoke_sessions(user)
        elif action == "delete":
            delete_account(user)
        db.session.flush()
    db.session.commit()
    return jsonify(data={"action": action, "affected": len(users)})


@bp.get("/admin/comments")
@admin_required
def list_comments():
    query = db.select(Comment).options(selectinload(Comment.author), selectinload(Comment.post))
    if request.args.get("q"):
        query = query.where(Comment.text.contains(request.args["q"][:200]))
    rows, meta = page(query.order_by(Comment.created_at.desc(), Comment.id.desc()))
    return jsonify(data=[dict(c.to_dict(), postTitle=c.post.title or (c.post.content or "")[:80])
                         for c in rows], meta=meta)


@bp.post("/admin/posts/bulk-delete")
@admin_required
def bulk_delete_posts():
    ids = body(("ids",)).get("ids")
    if not isinstance(ids, list) or not ids or len(ids) > 500:
        raise APIError("ids must be a list of 1 to 500 post ids.")
    posts = db.session.scalars(db.select(Post).where(Post.id.in_({integer(v, "ids") for v in ids}))).all()
    for post in posts:
        db.session.delete(post)
    db.session.commit()
    return jsonify(data={"affected": len(posts)})


@bp.post("/admin/posts/<int:post_id>/solved")
@admin_required
def toggle_solved(post_id):
    post = db.get_or_404(Post, post_id)
    if not post.is_question:
        raise APIError("Only questions can be marked as solved.")
    post.is_solved = not post.is_solved
    if not post.is_solved:
        for comment in post.comments:
            comment.is_best_answer = False
    db.session.commit()
    return jsonify(data=post.to_dict())


@bp.post("/admin/broadcast")
@admin_required
def broadcast():
    data = body(("message", "push"))
    message = string(data.get("message"), "message", 500, True)
    recipients = db.session.scalars(db.select(User.id).where(
        User.status == "Active", User.id != g.user.id)).all()
    db.session.add_all(Notification(recipient_id=uid, actor_id=g.user.id, type="system", content=message)
                       for uid in recipients)
    db.session.commit()
    pushed = False
    if data.get("push") is True and recipients:
        from backend.services.push import send_to_users
        send_to_users(recipients, "📢 " + g.user.name, message, "/")
        pushed = True
    return jsonify(data={"recipients": len(recipients), "pushed": pushed, "sentAt": iso(now())})
