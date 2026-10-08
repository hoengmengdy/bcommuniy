from flask import Blueprint, g, jsonify
from backend.extensions import db
from backend.models import Conversation, ConversationMember, Message, User
from backend.services.auth import login_required
from backend.services.notifications import notify
from backend.utils.validation import APIError, body, integer, page, string

bp = Blueprint("chat", __name__)


def conversation_for_user(conversation_id):
    conversation = db.get_or_404(Conversation, conversation_id)
    if not db.session.get(ConversationMember, (conversation.id, g.user.id)):
        raise APIError("This conversation is private.", 403)
    return conversation


@bp.get("/conversations")
@login_required
def conversations():
    query = db.select(Conversation).join(ConversationMember).where(
        ConversationMember.user_id == g.user.id).order_by(Conversation.id.desc())
    rows, meta = page(query)
    return jsonify(data=[c.to_dict(g.user.id) for c in rows], meta=meta)


@bp.post("/conversations")
@login_required
def add_conversation():
    data = body(("participantId",))
    other_id = integer(data.get("participantId"), "participantId")
    other = db.get_or_404(User, other_id)
    if other.id == g.user.id or other.status != "Active":
        raise APIError("Choose another active member.")
    # Direct conversations have exactly two participants, and are reused.
    existing = db.session.scalars(db.select(Conversation).join(ConversationMember).where(
        ConversationMember.user_id == g.user.id)).all()
    for conversation in existing:
        if {m.user_id for m in conversation.members} == {g.user.id, other.id}:
            return jsonify(data=conversation.to_dict(g.user.id))
    conversation = Conversation()
    conversation.members = [ConversationMember(user_id=g.user.id), ConversationMember(user_id=other.id)]
    db.session.add(conversation)
    db.session.commit()
    return jsonify(data=conversation.to_dict(g.user.id)), 201


@bp.get("/conversations/<int:conversation_id>")
@login_required
def read_conversation(conversation_id):
    return jsonify(data=conversation_for_user(conversation_id).to_dict(g.user.id))


@bp.delete("/conversations/<int:conversation_id>")
@login_required
def delete_conversation(conversation_id):
    conversation = conversation_for_user(conversation_id)
    db.session.delete(conversation)
    db.session.commit()
    return jsonify(data={"message": "Conversation and its messages deleted for both participants."})


@bp.get("/conversations/<int:conversation_id>/messages")
@login_required
def messages(conversation_id):
    conversation_for_user(conversation_id)
    rows, meta = page(db.select(Message).where(Message.conversation_id == conversation_id).order_by(
        Message.created_at, Message.id))
    return jsonify(data=[m.to_dict(g.user.id) for m in rows], meta=meta)


@bp.post("/conversations/<int:conversation_id>/messages")
@login_required
def add_message(conversation_id):
    conversation = conversation_for_user(conversation_id)
    data = body(("text", "attachment"))
    attachment = data.get("attachment")
    if attachment is not None:
        if not isinstance(attachment, dict) or set(attachment) != {"name", "size"}:
            raise APIError("attachment must contain only name and size.")
        attachment = {"name": string(attachment["name"], "attachment.name", 240, True),
                      "size": string(attachment["size"], "attachment.size", 40, True)}
    message = Message(conversation_id=conversation.id, sender_id=g.user.id,
                      text=string(data.get("text"), "text", 10000, True), attachment=attachment)
    db.session.add(message)
    for member in conversation.members:
        notify(member.user_id, "message", "sent you a message")
    db.session.commit()
    return jsonify(data=message.to_dict(g.user.id)), 201


@bp.put("/conversations/<int:conversation_id>/read")
@login_required
def mark_read(conversation_id):
    conversation_for_user(conversation_id)
    db.session.execute(db.update(Message).where(
        Message.conversation_id == conversation_id, Message.sender_id != g.user.id).values(is_read=True))
    db.session.commit()
    return jsonify(data={"message": "Messages marked as read."})


@bp.put("/messages/<int:message_id>")
@bp.delete("/messages/<int:message_id>")
@login_required
def edit_message(message_id):
    from flask import request
    message = db.get_or_404(Message, message_id)
    conversation_for_user(message.conversation_id)
    if message.sender_id != g.user.id:
        raise APIError("Only the sender may change a message.", 403)
    if request.method == "DELETE":
        db.session.delete(message)
        db.session.commit()
        return jsonify(data={"message": "Message deleted."})
    data = body(("text",))
    message.text = string(data.get("text"), "text", 10000, True)
    db.session.commit()
    return jsonify(data=message.to_dict(g.user.id))
