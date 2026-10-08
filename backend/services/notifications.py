from flask import g
from backend.extensions import db
from backend.models import Notification


def notify(recipient_id, kind, content):
    if recipient_id != g.user.id:
        db.session.add(Notification(recipient_id=recipient_id, actor_id=g.user.id,
                                    type=kind, content=content[:500]))
