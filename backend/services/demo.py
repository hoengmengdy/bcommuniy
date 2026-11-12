"""Shared public demo account. The login page is pre-filled with these credentials,
so they are public by design: keep this account a regular member, never an admin."""
from flask import g
from backend.extensions import db
from backend.models import User
from backend.utils.validation import APIError

DEMO_EMAIL = "hello@example.com"
DEMO_NAME = "Demo User"
DEMO_PASSWORD = "hello-demo-2026"  # must match src/views/AuthView.vue


def ensure_demo_account():
    """Create the demo member if it does not exist yet. The caller commits."""
    from backend.services.auth import create_user
    if not db.session.scalar(db.select(User.id).where(User.email == DEMO_EMAIL)):
        create_user({"name": DEMO_NAME, "email": DEMO_EMAIL, "password": DEMO_PASSWORD})


def guard_demo_account(user, changes=()):
    """Visitors sharing the demo login cannot lock others out of it; admins still can manage it."""
    if user.email == DEMO_EMAIL and g.user.account_role != "Admin" and (
            not changes or {"email", "password"} & set(changes)):
        raise APIError("The shared demo account cannot change its email or password, or be deleted.", 403)
