"""Vercel serverless entry: serves the Flask API under /api and /healthz."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Values piped into `vercel env add` from a Windows shell can carry a trailing newline.
for key in ("APP_ENV", "TRUST_PROXY", "SECRET_KEY", "ADMIN_EMAIL", "ADMIN_NAME", "ADMIN_PASSWORD"):
    if key in os.environ:
        os.environ[key] = os.environ[key].strip()

# Keep people signed in on the installed phone app; sign-out, password changes and
# deactivation still revoke sessions immediately. A TOKEN_MAX_AGE env var overrides this.
os.environ.setdefault("TOKEN_MAX_AGE", str(365 * 24 * 60 * 60))

# Upstash for Redis (Vercel Marketplace) exposes REDIS_URL / KV_URL rather than
# RATELIMIT_STORAGE_URI; reuse it so login rate limits are shared across instances.
# Without Redis, fall back to per-instance memory limits instead of refusing to start.
if not os.environ.get("RATELIMIT_STORAGE_URI"):
    redis_url = os.environ.get("REDIS_URL") or os.environ.get("KV_URL")
    if redis_url:
        os.environ["RATELIMIT_STORAGE_URI"] = redis_url
    else:
        os.environ["RATELIMIT_STORAGE_URI"] = "memory://"
        os.environ["RATELIMIT_ALLOW_MEMORY"] = "1"

from flask_migrate import upgrade  # noqa: E402

from backend.app import create_app  # noqa: E402
from backend.config import BASE_DIR  # noqa: E402
from backend.extensions import db  # noqa: E402
from backend.models import User  # noqa: E402
from backend.services.auth import create_user  # noqa: E402

app = create_app()


def prepare_database():
    """Apply migrations, like backend.production does, and bootstrap the first admin.

    The admin is created only while the database has no users at all, from the
    ADMIN_EMAIL / ADMIN_NAME / ADMIN_PASSWORD environment variables. Concurrent cold
    starts may race; PostgreSQL DDL is transactional, so the loser rolls back cleanly.
    """
    with app.app_context():
        try:
            upgrade(directory=str(BASE_DIR / "migrations"))
        except Exception:
            app.logger.exception("Migration on cold start failed; continuing")
            return
        address, secret = os.environ.get("ADMIN_EMAIL"), os.environ.get("ADMIN_PASSWORD")
        if not (address and secret):
            return
        try:
            if db.session.scalar(db.select(db.func.count()).select_from(User)) == 0:
                create_user({"name": os.environ.get("ADMIN_NAME") or "Admin", "email": address,
                             "password": secret, "role": "Admin"}, admin=True)
                db.session.commit()
                app.logger.warning("Bootstrapped first administrator %s", address)
        except Exception:
            db.session.rollback()
            app.logger.exception("Admin bootstrap failed")


prepare_database()
