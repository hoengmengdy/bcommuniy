from flask import Blueprint, g, jsonify, request
from backend.extensions import db
from backend.models import Comment, Post, PostLike, User
from backend.services.auth import login_required, require_owner
from backend.services.notifications import notify
from backend.utils.validation import APIError, body, boolean, integer, page, string, strings, url

bp = Blueprint("posts", __name__)
POST_FIELDS = ("title", "content", "tag", "tags", "codeSnippet", "codeLanguage", "image",
               "projectUrl", "isQuestion")
COMMENT_FIELDS = ("text", "parentId", "codeSnippet", "codeLanguage")


def post_data(post, data):
    aliases = {"codeSnippet": "code_snippet", "codeLanguage": "code_language",
               "projectUrl": "project_url", "isQuestion": "is_question"}
    for key, value in data.items():
        if key == "isQuestion":
            value = boolean(value, key)
        elif key == "tags":
            value = strings(value, key)
        elif key in ("image", "projectUrl"):
            value = url(value, key, image=key == "image")
        else:
            value = string(value, key, {"title": 240, "tag": 40, "codeLanguage": 40}.get(key, 50000))
            if key in ("title", "content", "tag", "codeLanguage") and value is None:
                raise APIError(f"{key} cannot be null.")
        setattr(post, aliases.get(key, key), value)
    if post.is_question:
        post.tag = "#Q&A"
    if not any((post.content, post.code_snippet, post.image)):
        raise APIError("A post needs content, codeSnippet or an image.")


def get_post(post_id):
    post = db.get_or_404(Post, post_id)
    if request.path.startswith("/api/questions") and not post.is_question:
        raise APIError("Question not found.", 404)
    if request.path.startswith("/api/reviews") and post.tag != "#Review":
        raise APIError("Review not found.", 404)
    return post


def serialize(post):
    return post.question_dict() if request.path.startswith("/api/questions") else post.to_dict()


@bp.get("/posts")
@bp.get("/questions")
@bp.get("/reviews")
def list_posts():
    query = db.select(Post)
    if request.path.startswith("/api/questions"):
        query = query.where(Post.is_question.is_(True))
    if request.path.startswith("/api/reviews"):
        query = query.where(Post.tag == "#Review")
    if request.args.get("tag"):
        query = query.where(Post.tag == request.args["tag"])
    if request.args.get("author_id"):
        query = query.where(Post.author_id == integer(request.args["author_id"], "author_id"))
    if request.args.get("q"):
        search = request.args["q"][:200]
        query = query.where(db.or_(Post.content.contains(search), Post.title.contains(search)))
    rows, meta = page(query.order_by(Post.created_at.desc(), Post.id.desc()))
    return jsonify(data=[serialize(p) for p in rows], meta=meta)


@bp.post("/posts")
@bp.post("/questions")
@bp.post("/reviews")
@login_required
def add_post():
    data = body(POST_FIELDS)
    post = Post(author_id=g.user.id, content="", tag="#General", is_question=False)
    if request.path.startswith("/api/questions"):
        data["isQuestion"] = True
        string(data.get("title"), "title", 240, True)
    if request.path.startswith("/api/reviews"):
        data["tag"] = "#Review"
    post_data(post, data)
    db.session.add(post)
    db.session.commit()
    return jsonify(data=serialize(post)), 201


@bp.get("/posts/<int:post_id>")
@bp.get("/questions/<int:post_id>")
@bp.get("/reviews/<int:post_id>")
def read_post(post_id):
    return jsonify(data=serialize(get_post(post_id)))


@bp.put("/posts/<int:post_id>")
@bp.put("/questions/<int:post_id>")
@bp.put("/reviews/<int:post_id>")
@login_required
def edit_post(post_id):
    post = get_post(post_id)
    require_owner(post.author_id)
    data = body(POST_FIELDS)
    if request.path.startswith("/api/questions"):
        data["isQuestion"] = True
        if "title" in data:
            string(data["title"], "title", 240, True)
    if request.path.startswith("/api/reviews"):
        data["tag"] = "#Review"
    post_data(post, data)
    db.session.commit()
    return jsonify(data=serialize(post))


@bp.delete("/posts/<int:post_id>")
@bp.delete("/questions/<int:post_id>")
@bp.delete("/reviews/<int:post_id>")
@login_required
def delete_post(post_id):
    post = get_post(post_id)
    require_owner(post.author_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify(data={"message": "Post deleted."})


@bp.post("/posts/<int:post_id>/like")
@bp.delete("/posts/<int:post_id>/like")
@login_required
def like_post(post_id):
    post = db.get_or_404(Post, post_id)
    like = db.session.get(PostLike, (g.user.id, post.id))
    if request.method == "POST" and not like:
        db.session.add(PostLike(user_id=g.user.id, post_id=post.id))
        notify(post.author_id, "like", "liked your post")
    elif request.method == "DELETE" and like:
        db.session.delete(like)
    db.session.commit()
    return jsonify(data=post.to_dict())


@bp.get("/posts/<int:post_id>/comments")
def comments(post_id):
    post = db.get_or_404(Post, post_id)
    return jsonify(data=[c.to_dict() for c in post.comments])


@bp.post("/posts/<int:post_id>/comments")
@login_required
def add_comment(post_id):
    post = db.get_or_404(Post, post_id)
    data = body(COMMENT_FIELDS)
    parent = data.get("parentId")
    if parent is not None:
        parent = integer(parent, "parentId")
        parent_comment = db.get_or_404(Comment, parent)
        if parent_comment.post_id != post.id:
            raise APIError("A reply must belong to the same post.")
    comment = Comment(post_id=post.id, author_id=g.user.id, parent_id=parent, text="",
                      code_language="javascript")
    comment_data(comment, data)
    db.session.add(comment)
    notify(post.author_id, "comment", "commented on your post")
    if parent is not None:
        notify(parent_comment.author_id, "comment", "replied to your comment")
    db.session.commit()
    return jsonify(data=comment.to_dict()), 201


def comment_data(comment, data):
    for key, attr in (("text", "text"), ("codeSnippet", "code_snippet"),
                      ("codeLanguage", "code_language")):
        if key in data:
            value = string(data[key], key, 40 if key == "codeLanguage" else 50000)
            if key != "codeSnippet" and value is None:
                raise APIError(f"{key} cannot be null.")
            setattr(comment, attr, value)
    if not comment.text and not comment.code_snippet:
        raise APIError("A comment needs text or codeSnippet.")


@bp.get("/comments/<int:comment_id>")
def read_comment(comment_id):
    return jsonify(data=db.get_or_404(Comment, comment_id).to_dict())


@bp.put("/comments/<int:comment_id>")
@login_required
def edit_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)
    require_owner(comment.author_id)
    comment_data(comment, body(("text", "codeSnippet", "codeLanguage")))
    db.session.commit()
    return jsonify(data=comment.to_dict())


@bp.delete("/comments/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)
    require_owner(comment.author_id)
    post = comment.post
    # Include descendant replies when removing an accepted answer.
    children = {comment.id}
    while True:
        expanded = children | {c.id for c in post.comments if c.parent_id in children}
        if expanded == children:
            break
        children = expanded
    if any(c.is_best_answer for c in post.comments if c.id in children):
        post.is_solved = False
    db.session.delete(comment)
    db.session.commit()
    return jsonify(data={"message": "Comment deleted."})


@bp.post("/posts/<int:post_id>/solve")
@login_required
def solve(post_id):
    post = db.get_or_404(Post, post_id)
    require_owner(post.author_id)
    if not post.is_question:
        raise APIError("Only questions can have an accepted answer.")
    data = body(("commentId",))
    comment = db.get_or_404(Comment, integer(data.get("commentId"), "commentId"))
    if comment.post_id != post.id:
        raise APIError("The accepted answer must belong to this question.")
    for item in post.comments:
        item.is_best_answer = item.id == comment.id
    post.is_solved = True
    db.session.commit()
    return jsonify(data=post.to_dict())
