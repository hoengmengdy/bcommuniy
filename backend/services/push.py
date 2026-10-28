"""Web Push: lock-screen notifications for new chat messages (iOS 16.4+ home-screen app, Android, desktop).

Needs VAPID_PRIVATE_KEY (raw base64url P-256 key). Without it, push is simply switched off.
"""
import base64
import json
import os
from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from flask import current_app, request
from py_vapid import Vapid02
from pywebpush import WebPushException, webpush

from backend.extensions import db
from backend.models import PushSubscription


@lru_cache(maxsize=1)
def _load(private_key):
    return Vapid02.from_string(private_key)


def vapid():
    key = os.environ.get("VAPID_PRIVATE_KEY", "").strip()
    return _load(key) if key else None


def public_key():
    """The applicationServerKey browsers need to subscribe, derived from the private key."""
    keys = vapid()
    if not keys:
        return None
    raw = keys.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def send_to_users(user_ids, title, body, url):
    """Best effort: a failed push never breaks the request; expired subscriptions are removed."""
    keys = vapid()
    if not keys or not user_ids:
        return
    payload = json.dumps({"title": title, "body": body[:180], "url": url})
    subscriptions = db.session.scalars(
        db.select(PushSubscription).where(PushSubscription.user_id.in_(user_ids))).all()
    for subscription in subscriptions:
        try:
            webpush(subscription.info(), payload, vapid_private_key=keys,
                    vapid_claims={"sub": request.host_url.rstrip("/")}, ttl=86400, timeout=5)
        except WebPushException as error:
            if error.response is not None and error.response.status_code in (404, 410):
                db.session.delete(subscription)
            else:
                current_app.logger.warning("Push to subscription %s failed: %s", subscription.id, error)
        except Exception:
            current_app.logger.exception("Push to subscription %s failed", subscription.id)
    db.session.commit()
