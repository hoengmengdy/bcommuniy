"""Models mirror the fields in the existing Pinia stores and Vue forms."""
from datetime import datetime, timezone
from urllib.parse import quote
from backend.extensions import db


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(value):
    return value.isoformat(timespec="seconds") + "Z" if value else None


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.Text, nullable=False, default="")
    phone = db.Column(db.String(40), nullable=False, default="")
    bio = db.Column(db.Text, nullable=False, default="")
    role = db.Column(db.String(20), nullable=False, default="Beginner")
    account_role = db.Column(db.String(10), nullable=False, default="User")
    skills = db.Column(db.JSON, nullable=False, default=list)
    reputation = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="Active")
    joined_at = db.Column(db.DateTime, nullable=False, default=now)
    auth_version = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self, private=False, admin=False):
        result = {"id": self.id, "name": self.name,
                  "avatar": self.avatar or f"https://api.dicebear.com/7.x/initials/svg?seed={quote(self.name)}",
                  "bio": self.bio, "role": self.account_role if admin else self.role,
                  "profileRole": self.role, "skills": self.skills,
                  "reputation": self.reputation, "joinDate": iso(self.joined_at),
                  "isAdmin": self.account_role == "Admin"}
        if private or admin:
            result.update(email=self.email, phone=self.phone, accountRole=self.account_role, status=self.status)
        return result


class AuthSession(db.Model):
    __tablename__ = "auth_sessions"
    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = db.relationship(User)
    created_at = db.Column(db.DateTime, nullable=False, default=now)


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    author = db.relationship(User)
    title = db.Column(db.String(240), nullable=False, default="")
    content = db.Column(db.Text, nullable=False, default="")
    tag = db.Column(db.String(40), nullable=False, default="#General")
    tags = db.Column(db.JSON, nullable=False, default=list)
    code_snippet = db.Column(db.Text)
    code_language = db.Column(db.String(40), nullable=False, default="javascript")
    image = db.Column(db.Text)
    project_url = db.Column(db.Text)
    is_question = db.Column(db.Boolean, nullable=False, default=False)
    is_solved = db.Column(db.Boolean, nullable=False, default=False)
    views = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    comments = db.relationship("Comment", cascade="all, delete-orphan", passive_deletes=True,
                               order_by="Comment.created_at", back_populates="post")
    likes = db.relationship("PostLike", cascade="all, delete-orphan", passive_deletes=True)

    def to_dict(self):
        return {"id": self.id, "author": self.author.to_dict(), "title": self.title,
                "content": self.content, "tag": self.tag, "tags": self.tags,
                "codeSnippet": self.code_snippet, "codeLanguage": self.code_language,
                "image": self.image, "projectUrl": self.project_url,
                "isQuestion": self.is_question, "isSolved": self.is_solved,
                "timestamp": iso(self.created_at), "likes": len(self.likes),
                "comments": [c.to_dict() for c in self.comments]}

    def question_dict(self):
        result = self.to_dict()
        result.update(excerpt=self.content, upvotes=len(self.likes), votes=len(self.likes),
                      answersCount=len(self.comments), answers=len(self.comments),
                      views=self.views, resolved=self.is_solved, createdAt=iso(self.created_at),
                      time=iso(self.created_at), avatar=self.author.to_dict()["avatar"])
        return result


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id", ondelete="CASCADE"))
    text = db.Column(db.Text, nullable=False, default="")
    code_snippet = db.Column(db.Text)
    code_language = db.Column(db.String(40), nullable=False, default="javascript")
    is_best_answer = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    author = db.relationship(User)
    post = db.relationship(Post, back_populates="comments")

    def to_dict(self):
        return {"id": self.id, "postId": self.post_id, "parentId": self.parent_id,
                "author": self.author.to_dict(), "text": self.text,
                "codeSnippet": self.code_snippet, "codeLanguage": self.code_language,
                "isBestAnswer": self.is_best_answer, "timestamp": iso(self.created_at)}


class PostLike(db.Model):
    __tablename__ = "post_likes"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)


class Conversation(db.Model):
    __tablename__ = "conversations"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    members = db.relationship("ConversationMember", cascade="all, delete-orphan",
                              passive_deletes=True, back_populates="conversation")
    messages = db.relationship("Message", cascade="all, delete-orphan",
                               passive_deletes=True, order_by="Message.created_at")

    def to_dict(self, viewer_id):
        others = [m.user for m in self.members if m.user_id != viewer_id]
        other = others[0] if others else next(m.user for m in self.members)
        last = self.messages[-1] if self.messages else None
        return {"id": self.id, "name": other.name, "avatar": other.to_dict()["avatar"], "phone": other.phone,
                "participantIds": [m.user_id for m in self.members],
                "lastMessage": last.text if last else "",
                "time": iso(last.created_at) if last else iso(self.created_at),
                "unread": sum(1 for m in self.messages if m.sender_id != viewer_id and not m.is_read),
                "messages": [m.to_dict(viewer_id) for m in self.messages]}


class ConversationMember(db.Model):
    __tablename__ = "conversation_members"
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id", ondelete="CASCADE"),
                                primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    user = db.relationship(User)
    conversation = db.relationship(Conversation, back_populates="members")


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id", ondelete="CASCADE"),
                                nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    attachment = db.Column(db.JSON, nullable=True)
    type = db.Column(db.String(20), nullable=False, default="text")
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now)

    def to_dict(self, viewer_id):
        return {"id": self.id, "senderId": "me" if self.sender_id == viewer_id else self.sender_id,
                "text": self.text, "type": self.type, "time": iso(self.created_at),
                "attachment": self.attachment, "status": "read" if self.is_read else "sent"}


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    title = db.Column(db.String(240), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default="todo")
    created_at = db.Column(db.DateTime, nullable=False, default=now)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "description": self.description,
                "assigneeId": self.assignee_id, "creatorId": self.creator_id,
                "status": self.status, "createdAt": iso(self.created_at)}


class Article(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    author = db.relationship(User)
    title = db.Column(db.String(240), nullable=False)
    excerpt = db.Column(db.Text, nullable=False, default="")
    content = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.Text)
    read_time = db.Column(db.String(40), nullable=False, default="")
    likes = db.relationship("ArticleLike", cascade="all, delete-orphan", passive_deletes=True)
    tags = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, nullable=False, default=now)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "excerpt": self.excerpt, "content": self.content,
                "coverImage": self.cover_image, "readTime": self.read_time, "tags": self.tags,
                "author": self.author.to_dict(), "likes": len(self.likes), "createdAt": iso(self.created_at)}


class ArticleLike(db.Model):
    __tablename__ = "article_likes"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)


class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(240), nullable=False)
    company = db.Column(db.String(160), nullable=False)
    location = db.Column(db.String(160), nullable=False)
    type = db.Column(db.String(60), nullable=False)
    salary = db.Column(db.String(100), nullable=False, default="")
    logo = db.Column(db.Text)
    description = db.Column(db.Text, nullable=False)
    tags = db.Column(db.JSON, nullable=False, default=list)
    posted_at = db.Column(db.DateTime, nullable=False, default=now)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "company": self.company,
                "location": self.location, "type": self.type, "salary": self.salary,
                "logo": self.logo, "description": self.description, "tags": self.tags,
                "postedAt": iso(self.posted_at)}


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(240), nullable=False)
    date = db.Column(db.String(60), nullable=False)
    time = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(160), nullable=False)
    type = db.Column(db.String(60), nullable=False)
    cover_image = db.Column(db.Text)
    description = db.Column(db.Text, nullable=False)
    attendees_count = db.Column(db.Integer, nullable=False, default=0)
    speakers = db.Column(db.JSON, nullable=False, default=list)
    price = db.Column(db.String(100), nullable=False, default="Free")

    def to_dict(self):
        return {"id": self.id, "title": self.title, "date": self.date, "time": self.time,
                "location": self.location, "type": self.type, "coverImage": self.cover_image,
                "description": self.description, "attendeesCount": self.attendees_count,
                "speakers": self.speakers, "price": self.price}


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    actor = db.relationship(User, foreign_keys=[actor_id])
    type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now)

    def to_dict(self):
        return {"id": self.id, "user": self.actor.to_dict(), "type": self.type,
                "content": self.content, "isRead": self.is_read, "time": iso(self.created_at)}
