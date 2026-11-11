"""Voice and video calls (WebRTC signalling).

The browsers do the real work: each side gathers its network candidates into one
session description, and this API just hands the offer to the callee and the answer
back to the caller. Both sides poll, the same way chat already does.
"""
from datetime import timedelta
from flask import Blueprint, g, jsonify
from backend.extensions import db
from backend.models import Call, Message, now
from backend.routes.chat import conversation_for_user
from backend.services.auth import login_required
from backend.services.push import send_to_users
from backend.utils.validation import APIError, body, choice, integer

bp = Blueprint("calls", __name__)
RING_SECONDS = 45
MAX_SDP = 30000
LABEL = {"audio": "សំឡេង", "video": "វីដេអូ"}


def session_description(value, field):
    """WebRTC SDP text, kept byte-for-byte: trimming its final line break breaks some browsers."""
    if not isinstance(value, str) or not value.startswith("v=0") or len(value) > MAX_SDP:
        raise APIError(f"{field} must be a WebRTC session description.")
    return value


def expire_if_unanswered(call):
    if call.status == "ringing" and now() - call.created_at > timedelta(seconds=RING_SECONDS):
        finish(call, "missed")


def finish(call, status):
    """Close the call once and leave a line in the chat, like Messenger does."""
    if call.status not in ("ringing", "active"):
        return
    call.status = status
    call.ended_at = now()
    icon = "🎥" if call.kind == "video" else "📞"
    if status == "ended" and call.answered_at:
        seconds = int((call.ended_at - call.answered_at).total_seconds())
        text = f"{icon} ការហៅ{LABEL[call.kind]} · {seconds // 60}:{seconds % 60:02d}"
    else:
        text = f"{icon} ខកខានការហៅ{LABEL[call.kind]}"
    db.session.add(Message(conversation_id=call.conversation_id, sender_id=call.caller_id, text=text))


def call_for_user(call_id):
    call = db.get_or_404(Call, call_id)
    if g.user.id not in (call.caller_id, call.callee_id):
        raise APIError("This call is private.", 403)
    expire_if_unanswered(call)
    return call


def already_ringing(user_id):
    """Only a ringing call blocks a new one. An "active" row can be left behind when a phone
    loses power mid-call, and must never lock that person out of calls."""
    calls = db.session.scalars(db.select(Call).where(
        Call.status == "ringing", (Call.caller_id == user_id) | (Call.callee_id == user_id))).all()
    for call in calls:
        expire_if_unanswered(call)
    return any(call.status == "ringing" for call in calls)


@bp.post("/calls")
@login_required
def start_call():
    data = body(("conversationId", "kind", "offer"))
    conversation = conversation_for_user(integer(data.get("conversationId"), "conversationId"))
    kind = choice(data.get("kind"), "kind", ("audio", "video"))
    offer = session_description(data.get("offer"), "offer")
    others = [m.user_id for m in conversation.members if m.user_id != g.user.id]
    if len(others) != 1:
        raise APIError("Calls are one-to-one.")
    callee_id = others[0]
    # Someone starting a call is not in another one: close anything they left open.
    for stale in db.session.scalars(db.select(Call).where(
            (Call.caller_id == g.user.id) | (Call.callee_id == g.user.id),
            Call.status.in_(("ringing", "active")))).all():
        finish(stale, "ended")
    if already_ringing(callee_id):
        db.session.commit()
        raise APIError("This member is on another call.", 409)
    call = Call(conversation_id=conversation.id, caller_id=g.user.id, callee_id=callee_id, kind=kind, offer=offer)
    db.session.add(call)
    db.session.commit()
    result = call.to_dict(g.user.id)
    send_to_users([callee_id], "📞 មានគេហៅមក",
                  f"{g.user.name}: ការហៅ{LABEL[kind]}", f"/messages?c={conversation.id}")
    return jsonify(data=result), 201


@bp.get("/calls/incoming")
@login_required
def incoming_call():
    """Polled by every signed-in page, so it is one small indexed query."""
    calls = db.session.scalars(db.select(Call).where(
        Call.callee_id == g.user.id, Call.status == "ringing").order_by(Call.id.desc())).all()
    for call in calls:
        expire_if_unanswered(call)
    db.session.commit()
    ringing = next((c for c in calls if c.status == "ringing"), None)
    return jsonify(data=ringing.to_dict(g.user.id) if ringing else None)


@bp.get("/calls/<int:call_id>")
@login_required
def read_call(call_id):
    call = call_for_user(call_id)
    db.session.commit()
    return jsonify(data=call.to_dict(g.user.id))


@bp.post("/calls/<int:call_id>/answer")
@login_required
def answer_call(call_id):
    call = call_for_user(call_id)
    data = body(("answer",))
    if call.callee_id != g.user.id:
        raise APIError("Only the person being called can answer.", 403)
    if call.status != "ringing":
        db.session.commit()
        raise APIError("This call has already finished.", 409)
    call.answer = session_description(data.get("answer"), "answer")
    call.status = "active"
    call.answered_at = now()
    db.session.commit()
    return jsonify(data=call.to_dict(g.user.id))


@bp.post("/calls/<int:call_id>/end")
@login_required
def end_call(call_id):
    call = call_for_user(call_id)
    if call.status == "ringing":
        finish(call, "declined" if g.user.id == call.callee_id else "missed")
    else:
        finish(call, "ended")
    db.session.commit()
    return jsonify(data=call.to_dict(g.user.id))
