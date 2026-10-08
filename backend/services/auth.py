import secrets
from functools import wraps
from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import generate_password_hash
from backend.extensions import db
from backend.models import AuthSession, User
from backend.utils.validation import APIError, choice, email, password, string


def serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="bcommunity-auth-v1")


def issue_token(user):
    session = AuthSession(id=secrets.token_hex(32), user_id=user.id)
    db.session.add(session)
    db.session.flush()
    return serializer().dumps({"sid": session.id, "v": user.auth_version})


def authenticate_request():
    # The global API guard and existing permission decorators share one check.
    if getattr(g, "user", None) is not None:
        return
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise APIError("Authentication required.", 401)
    try:
        payload, issued_at = serializer().loads(
            token, max_age=current_app.config["TOKEN_MAX_AGE"], return_timestamp=True)
        session = db.session.get(AuthSession, payload["sid"])
        user = session.user if session else None
        if not user or user.status != "Active" or payload["v"] != user.auth_version:
            raise APIError("Session is no longer valid. Please sign in again.", 401)
    except (BadSignature, KeyError, TypeError) as error:
        raise APIError("Invalid or expired authentication token.", 401) from error
    g.user, g.auth_session = user, session
    g.auth_expires_at = int((issued_at.timestamp() + current_app.config["TOKEN_MAX_AGE"]) * 1000)


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        authenticate_request()
        return fn(*args, **kwargs)
    return wrapped


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if g.user.account_role != "Admin":
            raise APIError("Administrator access required.", 403)
        return fn(*args, **kwargs)
    return wrapped


def require_owner(owner_id):
    if owner_id != g.user.id and g.user.account_role != "Admin":
        raise APIError("You do not have permission to change this resource.", 403)


def create_user(data, admin=False):
    user = User(name=string(data.get("name"), "name", 120, True), email=email(data.get("email")),
                password_hash=generate_password_hash(password(data.get("password"))))
    if db.session.scalar(db.select(User).where(User.email == user.email)):
        raise APIError("An account with this email already exists.", 409)
    if admin:
        user.account_role = choice(data.get("role", "User"), "role", ("User", "Admin"))
    db.session.add(user)
    db.session.flush()
    return user
