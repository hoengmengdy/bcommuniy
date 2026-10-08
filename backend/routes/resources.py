from flask import Blueprint, g, jsonify, request
from backend.extensions import db
from backend.models import Article, ArticleLike, Event, Job, Notification, Task, User
from backend.services.auth import admin_required, login_required, require_owner
from backend.utils.validation import APIError, body, boolean, choice, integer, page, string, strings, url

bp = Blueprint("resources", __name__)
# Explicit schemas mirror knowledge.js and opportunities.js; clients cannot set IDs or authors.
SCHEMAS = {
    "articles": (Article, {
        "title": ("title", 240, True), "excerpt": ("excerpt", 10000, False),
        "content": ("content", 100000, True), "coverImage": ("cover_image", "url", False),
        "readTime": ("read_time", 40, False), "tags": ("tags", "list", False)}),
    "jobs": (Job, {
        "title": ("title", 240, True), "company": ("company", 160, True),
        "location": ("location", 160, True), "type": ("type", 60, True),
        "salary": ("salary", 100, False), "logo": ("logo", "url", False),
        "description": ("description", 50000, True), "tags": ("tags", "list", False)}),
    "events": (Event, {
        "title": ("title", 240, True), "date": ("date", 60, True),
        "time": ("time", 100, True), "location": ("location", 160, True),
        "type": ("type", 60, True), "coverImage": ("cover_image", "url", False),
        "description": ("description", 50000, True), "attendeesCount": ("attendees_count", "int", False),
        "speakers": ("speakers", "list", False), "price": ("price", 100, False)}),
}


def catalog_routes(kind, model, schema):
    def listing():
        query = db.select(model)
        if request.args.get("q"):
            query = query.where(model.title.contains(request.args["q"][:200]))
        rows, meta = page(query.order_by(model.id.desc()))
        return jsonify(data=[item.to_dict() for item in rows], meta=meta)

    def reading(item_id):
        return jsonify(data=db.get_or_404(model, item_id).to_dict())

    @login_required
    def creating():
        if kind != "articles" and g.user.account_role != "Admin":
            raise APIError("Administrator access required.", 403)
        item = model()
        if kind == "articles":
            item.author_id = g.user.id
        apply(item, creating=True)
        db.session.add(item)
        db.session.commit()
        return jsonify(data=item.to_dict()), 201

    @login_required
    def changing(item_id):
        item = db.get_or_404(model, item_id)
        if kind == "articles":
            require_owner(item.author_id)
        elif g.user.account_role != "Admin":
            raise APIError("Administrator access required.", 403)
        if request.method == "DELETE":
            db.session.delete(item)
            db.session.commit()
            return jsonify(data={"message": "Resource deleted."})
        apply(item)
        db.session.commit()
        return jsonify(data=item.to_dict())

    def apply(item, creating=False):
        data = body(schema)
        for key, (attr, spec, required) in schema.items():
            if key not in data:
                if creating and required:
                    raise APIError(f"{key} is required.")
                continue
            value = data[key]
            if spec == "url":
                value = url(value, key)
            elif spec == "list":
                value = strings(value, key)
            elif spec == "int":
                value = integer(value, key, 0)
            else:
                value = string(value, key, spec, required)
                if value is None:
                    raise APIError(f"{key} cannot be null.")
            setattr(item, attr, value)

    bp.add_url_rule(f"/{kind}", f"{kind}_list", listing, methods=["GET"])
    bp.add_url_rule(f"/{kind}", f"{kind}_create", creating, methods=["POST"])
    bp.add_url_rule(f"/{kind}/<int:item_id>", f"{kind}_read", reading, methods=["GET"])
    bp.add_url_rule(f"/{kind}/<int:item_id>", f"{kind}_change", changing, methods=["PUT", "DELETE"])


for kind, (model, schema) in SCHEMAS.items():
    catalog_routes(kind, model, schema)


@bp.get("/tasks")
@login_required
def tasks():
    rows, meta = page(db.select(Task).order_by(Task.id.desc()))
    return jsonify(data=[t.to_dict() for t in rows], meta=meta)


@bp.get("/tasks/<int:task_id>")
@login_required
def read_task(task_id):
    return jsonify(data=db.get_or_404(Task, task_id).to_dict())


def apply_task(task, data):
    for key, value in data.items():
        if key == "assigneeId":
            value = integer(value, key)
            user = db.get_or_404(User, value)
            if user.status != "Active":
                raise APIError("Assign the task to an active member.")
            task.assignee_id = value
        elif key == "status":
            task.status = choice(value, key, ("todo", "in-progress", "done"))
        else:
            setattr(task, key, string(value, key, 240 if key == "title" else 10000,
                                      required=key == "title"))
    if task.description is None:
        raise APIError("description cannot be null.")


@bp.post("/tasks")
@login_required
def add_task():
    data = body(("title", "description", "assigneeId", "status"))
    string(data.get("title"), "title", 240, True)
    if "assigneeId" not in data:
        raise APIError("assigneeId is required.")
    task = Task(creator_id=g.user.id, description="", status="todo")
    apply_task(task, data)
    db.session.add(task)
    db.session.commit()
    return jsonify(data=task.to_dict()), 201


@bp.put("/tasks/<int:task_id>")
@bp.delete("/tasks/<int:task_id>")
@login_required
def change_task(task_id):
    task = db.get_or_404(Task, task_id)
    if request.method == "DELETE":
        require_owner(task.creator_id)
        db.session.delete(task)
        db.session.commit()
        return jsonify(data={"message": "Task deleted."})
    data = body(("title", "description", "assigneeId", "status"))
    if task.creator_id != g.user.id and g.user.account_role != "Admin":
        if task.assignee_id != g.user.id or set(data) - {"status"}:
            raise APIError("Only the creator or administrator may edit this task.", 403)
    apply_task(task, data)
    db.session.commit()
    return jsonify(data=task.to_dict())


@bp.get("/notifications")
@login_required
def notifications():
    rows, meta = page(db.select(Notification).where(Notification.recipient_id == g.user.id).order_by(
        Notification.created_at.desc(), Notification.id.desc()))
    return jsonify(data=[n.to_dict() for n in rows], meta=meta)


@bp.put("/notifications/read")
@login_required
def notifications_read():
    db.session.execute(db.update(Notification).where(
        Notification.recipient_id == g.user.id).values(is_read=True))
    db.session.commit()
    return jsonify(data={"message": "All notifications marked as read."})


@bp.put("/notifications/<int:notification_id>")
@bp.delete("/notifications/<int:notification_id>")
@login_required
def notification_change(notification_id):
    notification = db.get_or_404(Notification, notification_id)
    if notification.recipient_id != g.user.id:
        raise APIError("This notification is private.", 403)
    if request.method == "DELETE":
        db.session.delete(notification)
        db.session.commit()
        return jsonify(data={"message": "Notification deleted."})
    data = body(("isRead",))
    notification.is_read = boolean(data.get("isRead"), "isRead")
    db.session.commit()
    return jsonify(data=notification.to_dict())


@bp.post("/articles/<int:article_id>/like")
@bp.delete("/articles/<int:article_id>/like")
@login_required
def article_like(article_id):
    article = db.get_or_404(Article, article_id)
    like = db.session.get(ArticleLike, (g.user.id, article.id))
    if request.method == "POST" and not like:
        db.session.add(ArticleLike(user_id=g.user.id, article_id=article.id))
    elif request.method == "DELETE" and like:
        db.session.delete(like)
    db.session.commit()
    return jsonify(data=article.to_dict())
