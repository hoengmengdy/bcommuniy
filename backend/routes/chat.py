import re
from flask import Blueprint, g, jsonify
from backend.extensions import db
from backend.models import (Conversation, ConversationMember, Message, MessageReaction, PushSubscription, User,
                            now)
from backend.services.auth import login_required
from backend.services.notifications import notify
from backend.services.push import public_key, send_to_users
from backend.utils.validation import APIError, body, choice, integer, page, string

bp = Blueprint("chat", __name__)
# Reactions are emoji only: reject letters, digits, spaces and markup characters.
EMOJI_SAFE = re.compile(r"[A-Za-z0-9\s<>&\"'`]")
BLOB_URL = re.compile(r"https://[a-z0-9]+\.public\.blob\.vercel-storage\.com/chat/[\w.-]+")


def conversation_for_user(conversation_id):
    conversation = db.get_or_404(Conversation, conversation_id)
    if not db.session.get(ConversationMember, (conversation.id, g.user.id)):
        raise APIError("This conversation is private.", 403)
    return conversation


@bp.get("/conversations")
@login_required
def conversations():
    # Newest activity first, like Messenger: a chat with a new message jumps to the top.
    latest = db.select(db.func.max(Message.created_at)).where(
        Message.conversation_id == Conversation.id).correlate(Conversation).scalar_subquery()
    query = db.select(Conversation).join(ConversationMember).where(
        ConversationMember.user_id == g.user.id).order_by(
        db.func.coalesce(latest, Conversation.created_at).desc(), Conversation.id.desc())
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
    data = body(("text", "attachment", "replyToId"))
    attachment = data.get("attachment")
    kind = "text"
    reply_to_id = None
    if data.get("replyToId") is not None:
        reply_to_id = integer(data["replyToId"], "replyToId")
        replied = db.session.get(Message, reply_to_id)
        if replied is None or replied.conversation_id != conversation.id:
            raise APIError("replyToId must be a message in this conversation.")
    if attachment is not None:
        if not isinstance(attachment, dict) or set(attachment) not in (
                {"name", "size"}, {"name", "size", "url", "kind"}):
            raise APIError("attachment must contain name and size, plus url and kind for media.")
        clean = {"name": string(attachment["name"], "attachment.name", 240, True),
                 "size": string(attachment["size"], "attachment.size", 40, True)}
        if "url" in attachment:
            clean["kind"] = choice(attachment["kind"], "attachment.kind", ("image", "video"))
            clean["url"] = string(attachment["url"], "attachment.url", 500, True)
            # Only files uploaded to this app's Vercel Blob store, never arbitrary links.
            if not BLOB_URL.fullmatch(clean["url"]):
                raise APIError("attachment.url must be an uploaded chat file.")
            kind = clean["kind"]
        attachment = clean
    message = Message(conversation_id=conversation.id, sender_id=g.user.id, type=kind, attachment=attachment,
                      text=string(data.get("text"), "text", 10000, kind == "text") or "", reply_to_id=reply_to_id)
    db.session.add(message)
    for member in conversation.members:
        notify(member.user_id, "message", "sent you a message")
    db.session.commit()
    result = message.to_dict(g.user.id)
    send_to_users([m.user_id for m in conversation.members if m.user_id != g.user.id], g.user.name,
                  message.text or {"image": "📷 Photo", "video": "🎬 Video"}.get(kind, "New message"),
                  f"/messages?c={conversation.id}")
    return jsonify(data=result), 201


@bp.get("/push/key")
@login_required
def push_key():
    return jsonify(data={"publicKey": public_key()})


@bp.post("/push/subscriptions")
@login_required
def add_push_subscription():
    data = body(("endpoint", "keys", "expirationTime"))
    endpoint = string(data.get("endpoint"), "endpoint", 1000, True)
    if not endpoint.startswith("https://"):
        raise APIError("endpoint must be an https URL.")
    keys = data.get("keys")
    if not isinstance(keys, dict):
        raise APIError("keys must contain p256dh and auth.")
    p256dh = string(keys.get("p256dh"), "keys.p256dh", 200, True)
    auth = string(keys.get("auth"), "keys.auth", 100, True)
    # One device belongs to whoever signed in on it most recently.
    subscription = db.session.scalar(db.select(PushSubscription).where(PushSubscription.endpoint == endpoint))
    if subscription is None:
        subscription = PushSubscription(endpoint=endpoint)
        db.session.add(subscription)
    subscription.user_id, subscription.p256dh, subscription.auth = g.user.id, p256dh, auth
    db.session.commit()
    return jsonify(data={"subscribed": True}), 201


@bp.delete("/push/subscriptions")
@login_required
def delete_push_subscription():
    endpoint = string(body(("endpoint",)).get("endpoint"), "endpoint", 1000, True)
    db.session.execute(db.delete(PushSubscription).where(
        PushSubscription.endpoint == endpoint, PushSubscription.user_id == g.user.id))
    db.session.commit()
    return jsonify(data={"subscribed": False})


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
    text = string(data.get("text"), "text", 10000, True)
    if text != message.text:
        message.text, message.edited_at = text, now()
    db.session.commit()
    return jsonify(data=message.to_dict(g.user.id))


@bp.put("/messages/<int:message_id>/reaction")
@login_required
def react_to_message(message_id):
    """Set (or with emoji null/empty, remove) the signed-in member's single reaction."""
    message = db.get_or_404(Message, message_id)
    conversation_for_user(message.conversation_id)
    emoji = string(body(("emoji",)).get("emoji"), "emoji", 16)
    if emoji and EMOJI_SAFE.search(emoji):
        raise APIError("emoji must be an emoji.")
    reaction = db.session.get(MessageReaction, (message.id, g.user.id))
    if not emoji:
        if reaction:
            db.session.delete(reaction)
    elif reaction:
        reaction.emoji = emoji
    else:
        db.session.add(MessageReaction(message_id=message.id, user_id=g.user.id, emoji=emoji))
    db.session.commit()
    db.session.refresh(message)
    return jsonify(data=message.to_dict(g.user.id))
