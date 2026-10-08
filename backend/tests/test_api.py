import secrets
from pathlib import Path
import pytest
from flask_migrate import upgrade, downgrade
from sqlalchemy import inspect
from werkzeug.security import check_password_hash
from backend.app import create_app
from backend.config import BASE_DIR
from backend.extensions import db
from backend.models import User

# Every declared method/path pair must be exercised by this suite.
COVERED = set()


def call(client, method, path, status=200, headers=None, data=None, **kwargs):
    response = client.open(path, method=method, headers=headers, json=data, **kwargs)
    assert response.status_code == status, (method, path, response.status_code, response.json)
    assert response.is_json, (method, path, response.data[:200])
    adapter = client.application.url_map.bind("localhost")
    rule, _ = adapter.match(path.split("?")[0], method=method, return_rule=True)
    COVERED.add((method, rule.rule))
    return response.json.get("data")


def test_auth_profile_users(client, app, accounts, create_account):
    owner, admin = accounts["owner"], accounts["admin"]
    secret = secrets.token_urlsafe(18)
    existing = create_account({"name": "Existing Member", "email": "NEW@example.com", "password": secret})
    user_id = existing["user"]["id"]
    assert existing["user"]["email"] == "new@example.com"
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.password_hash != secret and check_password_hash(user.password_hash, secret)
    logged_in = call(client, "POST", "/api/auth/login",
                     data={"email": "new@example.com", "password": secret})
    headers = {"Authorization": "Bearer " + logged_in["token"]}
    assert call(client, "GET", "/api/auth/me", headers=headers)["id"] == user_id
    assert call(client, "GET", "/api/profile", headers=headers)["id"] == user_id
    profile = call(client, "PUT", "/api/profile", headers=headers,
                   data={"name": "Updated", "bio": "Bio", "role": "Teacher", "skills": ["Python"]})
    assert profile["role"] == "Teacher" and profile["isAdmin"] is False
    assert call(client, "GET", f"/api/users/{user_id}", headers=owner["headers"])["name"] == "Updated"
    assert "email" not in call(client, "GET", f"/api/users/{user_id}", headers=owner["headers"])
    call(client, "GET", "/api/users", headers=admin["headers"])
    admin_created = call(client, "POST", "/api/users", 201, headers=admin["headers"],
                         data={"name": "Created", "email": "created@example.com",
                               "password": secrets.token_urlsafe(18), "role": "User"})
    changed = call(client, "PUT", f"/api/users/{admin_created['id']}", headers=admin["headers"],
                   data={"name": "Renamed", "email": "renamed@example.com", "status": "Active"})
    assert changed["name"] == "Renamed"
    call(client, "DELETE", f"/api/users/{admin_created['id']}", headers=admin["headers"])
    new_secret = secrets.token_urlsafe(18)
    call(client, "PUT", f"/api/users/{user_id}", headers=headers, data={"password": new_secret})
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    logged_in = call(client, "POST", "/api/auth/login",
                     data={"email": "new@example.com", "password": new_secret})
    headers = {"Authorization": "Bearer " + logged_in["token"]}
    call(client, "POST", "/api/auth/logout", headers=headers)
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    logged_in = call(client, "POST", "/api/auth/login",
                     data={"email": "new@example.com", "password": new_secret})
    call(client, "DELETE", f"/api/users/{user_id}",
         headers={"Authorization": "Bearer " + logged_in["token"]})


@pytest.mark.parametrize("resource", ["posts", "questions", "reviews"])
def test_post_crud(client, accounts, resource):
    owner, other = accounts["owner"]["headers"], accounts["other"]["headers"]
    body = {"content": "Content", "title": "Title", "tags": ["python"], "codeSnippet": "print(1)"}
    post = call(client, "POST", f"/api/{resource}", 201, headers=owner, data=body)
    assert call(client, "GET", f"/api/{resource}", headers=owner)
    assert call(client, "GET", f"/api/{resource}/{post['id']}", headers=owner)["id"] == post["id"]
    updated = call(client, "PUT", f"/api/{resource}/{post['id']}", headers=owner,
                   data={"content": "Updated"})
    assert updated["content"] == "Updated"
    assert client.put(f"/api/{resource}/{post['id']}", headers=other,
                      json={"content": "Steal"}).status_code == 403
    call(client, "DELETE", f"/api/{resource}/{post['id']}", headers=owner)
    assert client.get(f"/api/{resource}/{post['id']}", headers=owner).status_code == 404


def test_comments_likes_answers(client, accounts):
    owner, other = accounts["owner"]["headers"], accounts["other"]["headers"]
    post = call(client, "POST", "/api/posts", 201, headers=owner,
                data={"content": "Question?", "isQuestion": True})
    pid = post["id"]
    comment = call(client, "POST", f"/api/posts/{pid}/comments", 201, headers=other,
                   data={"text": "Answer", "codeSnippet": "pass", "codeLanguage": "python"})
    cid = comment["id"]
    reply = call(client, "POST", f"/api/posts/{pid}/comments", 201, headers=owner,
                 data={"text": "Reply", "parentId": cid})
    assert len(call(client, "GET", f"/api/posts/{pid}/comments", headers=owner)) == 2
    assert call(client, "GET", f"/api/comments/{cid}", headers=owner)["text"] == "Answer"
    call(client, "PUT", f"/api/comments/{cid}", headers=other, data={"text": "Better answer"})
    assert client.put(f"/api/comments/{cid}", headers=owner, json={"text": "Steal"}).status_code == 403
    assert call(client, "POST", f"/api/posts/{pid}/like", headers=other)["likes"] == 1
    assert call(client, "POST", f"/api/posts/{pid}/like", headers=other)["likes"] == 1
    assert call(client, "DELETE", f"/api/posts/{pid}/like", headers=other)["likes"] == 0
    assert client.post(f"/api/posts/{pid}/solve", headers=other, json={"commentId": cid}).status_code == 403
    solved = call(client, "POST", f"/api/posts/{pid}/solve", headers=owner, data={"commentId": cid})
    assert solved["isSolved"] and solved["comments"][0]["isBestAnswer"]
    call(client, "DELETE", f"/api/comments/{cid}", headers=other)
    assert call(client, "GET", f"/api/posts/{pid}", headers=owner)["isSolved"] is False
    assert call(client, "GET", f"/api/posts/{pid}/comments", headers=owner) == []
    assert client.get(f"/api/comments/{reply['id']}", headers=owner).status_code == 404


def test_private_chat(client, accounts):
    owner, other, outsider = [accounts[key] for key in ("owner", "other", "outsider")]
    chat = call(client, "POST", "/api/conversations", 201, headers=owner["headers"],
                data={"participantId": other["id"]})
    cid = chat["id"]
    assert call(client, "POST", "/api/conversations", headers=other["headers"],
                data={"participantId": owner["id"]})["id"] == cid
    assert len(call(client, "GET", "/api/conversations", headers=owner["headers"])) == 1
    assert client.get(f"/api/conversations/{cid}", headers=outsider["headers"]).status_code == 403
    message = call(client, "POST", f"/api/conversations/{cid}/messages", 201,
                   headers=owner["headers"], data={"text": "Hello"})
    mid = message["id"]
    assert message["senderId"] == "me"
    assert call(client, "GET", f"/api/conversations/{cid}", headers=other["headers"])["unread"] == 1
    messages = call(client, "GET", f"/api/conversations/{cid}/messages", headers=other["headers"])
    assert messages[0]["senderId"] == owner["id"]
    assert client.post(f"/api/conversations/{cid}/messages", headers=outsider["headers"],
                       json={"text": "Intrude"}).status_code == 403
    assert client.put(f"/api/messages/{mid}", headers=other["headers"],
                      json={"text": "Steal"}).status_code == 403
    call(client, "PUT", f"/api/messages/{mid}", headers=owner["headers"], data={"text": "Edited"})
    call(client, "PUT", f"/api/conversations/{cid}/read", headers=other["headers"])
    assert call(client, "GET", f"/api/conversations/{cid}", headers=other["headers"])["unread"] == 0
    call(client, "DELETE", f"/api/messages/{mid}", headers=owner["headers"])
    call(client, "DELETE", f"/api/conversations/{cid}", headers=owner["headers"])
    assert call(client, "GET", "/api/conversations", headers=other["headers"]) == []


@pytest.mark.parametrize("resource,data", [
    ("articles", {"title": "Guide", "content": "Guide body", "excerpt": "Overview",
                  "tags": ["vue"], "readTime": "5 min read", "coverImage": "https://example.com/a.png"}),
    ("jobs", {"title": "Developer", "company": "Company", "location": "Remote", "type": "Contract",
              "salary": "$100", "description": "Build software", "tags": ["python"]}),
    ("events", {"title": "Meetup", "date": "Nov 1, 2026", "time": "9:00 AM",
                "location": "Online", "type": "Meetup", "description": "Learn",
                "speakers": ["Speaker"], "attendeesCount": 0, "price": "Free"}),
])
def test_catalog(client, accounts, resource, data):
    owner = accounts["owner"]["headers"]
    admin = accounts["admin"]["headers"]
    actor = owner if resource == "articles" else admin
    if resource != "articles":
        assert client.post("/api/" + resource, headers=owner, json=data).status_code == 403
    item = call(client, "POST", "/api/" + resource, 201, headers=actor, data=data)
    path = f"/api/{resource}/{item['id']}"
    assert call(client, "GET", "/api/" + resource, headers=owner)[0]["id"] == item["id"]
    assert call(client, "GET", path, headers=owner)["title"] == data["title"]
    assert call(client, "PUT", path, headers=actor, data={"title": "Changed"})["title"] == "Changed"
    assert client.delete(path, headers=accounts["outsider"]["headers"]).status_code == 403
    if resource == "articles":
        assert call(client, "POST", path + "/like", headers=owner)["likes"] == 1
        assert call(client, "DELETE", path + "/like", headers=owner)["likes"] == 0
    call(client, "DELETE", path, headers=actor)


def test_tasks(client, accounts):
    owner, other, outsider = [accounts[key] for key in ("owner", "other", "outsider")]
    task = call(client, "POST", "/api/tasks", 201, headers=owner["headers"],
                data={"title": "Implement", "description": "Details", "assigneeId": str(other["id"]),
                      "status": "todo"})
    path = f"/api/tasks/{task['id']}"
    assert call(client, "GET", "/api/tasks", headers=owner["headers"])[0]["id"] == task["id"]
    assert call(client, "GET", path, headers=other["headers"])["title"] == "Implement"
    assert call(client, "PUT", path, headers=other["headers"],
                data={"status": "done"})["status"] == "done"
    assert client.put(path, headers=other["headers"], json={"title": "Steal"}).status_code == 403
    assert client.put(path, headers=outsider["headers"], json={"status": "done"}).status_code == 403
    call(client, "PUT", path, headers=owner["headers"], data={"description": "Updated"})
    call(client, "DELETE", path, headers=owner["headers"])


def test_notifications_and_directory(client, accounts):
    owner, other = accounts["owner"]["headers"], accounts["other"]["headers"]
    post = call(client, "POST", "/api/posts", 201, headers=owner, data={"content": "Post"})
    call(client, "POST", f"/api/posts/{post['id']}/like", headers=other)
    notification = call(client, "GET", "/api/notifications", headers=owner)[0]
    path = f"/api/notifications/{notification['id']}"
    assert client.put(path, headers=other, json={"isRead": True}).status_code == 403
    assert call(client, "PUT", path, headers=owner, data={"isRead": True})["isRead"]
    call(client, "PUT", "/api/notifications/read", headers=owner)
    call(client, "DELETE", path, headers=owner)
    assert len(call(client, "GET", "/api/members", headers=owner)) == 4
    call(client, "GET", "/api/mentors", headers=owner)
    call(client, "GET", "/api/leaderboard", headers=owner)
    assert call(client, "GET", "/api/health", headers=owner)["database"] == "connected"


@pytest.mark.parametrize("path,data", [
    ("/api/users", {"name": "Name", "email": "invalid", "password": "longenough"}),
    ("/api/users", {"name": "", "email": "valid@example.com", "password": "longenough"}),
    ("/api/users", {"name": "Name", "email": "valid@example.com", "password": "short"}),
    ("/api/users", {"name": "Name", "email": "valid@example.com", "password": "longenough", "role": "Invalid"}),
    ("/api/posts", {"content": ""}),
    ("/api/posts", {"content": 123}),
    ("/api/posts", {"content": "Text", "projectUrl": "javascript:alert(1)"}),
    ("/api/posts", {"image": "data:image/svg+xml;base64,PHN2Zz4="}),
    ("/api/posts", {"image": "data:image/png;base64,bm90LWFuLWltYWdl"}),
    ("/api/posts", {"content": "Text", "isQuestion": "false"}),
    ("/api/posts", {"content": "Text", "tags": "tag"}),
    ("/api/tasks", {"title": "Task"}),
])
def test_validation(client, accounts, path, data):
    actor = accounts["admin"] if path == "/api/users" else accounts["owner"]
    response = client.post(path, headers=actor["headers"], json=data)
    assert response.status_code == 400, response.json
    assert "message" in response.json["error"]


def test_security_and_errors(client, accounts):
    owner, admin = accounts["owner"], accounts["admin"]
    assert client.get("/api/users").status_code == 401
    assert client.get("/api/users", headers=owner["headers"]).status_code == 403
    assert client.put(f"/api/users/{owner['id']}", headers=owner["headers"],
                      json={"role": "Admin"}).status_code == 403
    assert client.put("/api/profile", headers=owner["headers"],
                      json={"role": "Admin"}).status_code == 400
    assert client.delete(f"/api/users/{admin['id']}", headers=admin["headers"]).status_code == 409
    assert client.post("/api/users", headers=admin["headers"], json={
        "name": "Duplicate", "email": "OWNER@example.com", "password": secrets.token_urlsafe(18)}
    ).status_code == 409
    assert client.post("/api/auth/login", json={
        "email": "owner@example.com", "password": "wrong"
    }).status_code == 401
    assert client.post("/api/posts", headers=owner["headers"], data="{",
                      content_type="application/json").status_code == 400
    assert client.post("/api/posts", headers=owner["headers"], json=[]).status_code == 400
    assert client.post("/api/posts", headers=owner["headers"], data="text").status_code == 415
    assert client.get("/api/posts?page=0", headers=owner["headers"]).status_code == 400
    assert client.get("/api/posts/999", headers=owner["headers"]).status_code == 404
    assert client.get("/api/missing").is_json
    assert client.patch("/api/posts", headers=owner["headers"]).status_code == 405
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer forged"}).status_code == 401
    allowed = client.options("/api/posts", headers={
        "Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization,Content-Type"})
    assert allowed.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5173"
    blocked = client.get("/api/posts", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in blocked.headers


def test_token_expiration(client, create_account):
    from itsdangerous import TimestampSigner
    from unittest.mock import patch
    with patch.object(TimestampSigner, "get_timestamp", return_value=1):
        data = create_account({
            "name": "Expired", "email": "expired@example.com", "password": secrets.token_urlsafe(18)
        })
    assert client.get("/api/auth/me", headers={
        "Authorization": "Bearer " + data["token"]}).status_code == 401


def test_migrations_on_new_database(tmp_path):
    database = tmp_path / "migration.db"
    app = create_app({"TESTING": True, "SECRET_KEY": secrets.token_hex(32),
                      "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.as_posix()}"})
    with app.app_context():
        upgrade(directory=str(BASE_DIR / "migrations"))
        tables = set(inspect(db.engine).get_table_names())
        assert set(db.metadata.tables) <= tables
        assert "alembic_version" in tables
        assert db.session.execute(db.text("PRAGMA foreign_keys")).scalar() == 1
        db.session.remove()
        downgrade(directory=str(BASE_DIR / "migrations"), revision="base")
        assert set(inspect(db.engine).get_table_names()) == {"alembic_version"}
    assert database.is_file()



def test_exact_startup_admin_command(tmp_path):
    import os
    import sqlite3
    import subprocess
    import sys
    environment = dict(os.environ)
    database = tmp_path / "cli.db"
    secret = secrets.token_urlsafe(18)
    environment.update(
        DATABASE_URL=f"sqlite:///{database.as_posix()}",
        SECRET_KEY=secrets.token_hex(32),
        ADMIN_EMAIL="cli-admin@example.com",
        ADMIN_NAME="CLI Admin",
        ADMIN_PASSWORD=secret,
    )
    result = subprocess.run(
        [sys.executable, "app.py", "create-admin"], cwd=BASE_DIR, env=environment,
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with sqlite3.connect(database) as connection:
        role, hashed = connection.execute(
            "SELECT account_role, password_hash FROM users WHERE email = ?",
            ("cli-admin@example.com",),
        ).fetchone()
    assert role == "Admin" and check_password_hash(hashed, secret)
    assert secret not in result.stdout + result.stderr



def test_account_deletion_cleans_direct_conversations(client, app, accounts):
    from backend.models import Conversation, ConversationMember, Message
    owner, other = accounts["owner"], accounts["other"]
    chat = call(client, "POST", "/api/conversations", 201, headers=owner["headers"],
                data={"participantId": other["id"]})
    call(client, "POST", f"/api/conversations/{chat['id']}/messages", 201,
         headers=owner["headers"], data={"text": "Temporary conversation"})
    call(client, "DELETE", f"/api/users/{owner['id']}", headers=owner["headers"])
    assert call(client, "GET", "/api/conversations", headers=other["headers"]) == []
    with app.app_context():
        assert db.session.get(Conversation, chat["id"]) is None
        assert db.session.scalar(db.select(db.func.count()).select_from(Message)) == 0
        assert db.session.scalar(db.select(db.func.count()).select_from(ConversationMember)) == 0


def test_z_every_api_method_has_been_tested(app):
    declared = {(method, rule.rule) for rule in app.url_map.iter_rules()
                if rule.rule.startswith("/api/")
                for method in rule.methods - {"HEAD", "OPTIONS"}}
    assert not declared - COVERED, f"Untested endpoints: {sorted(declared - COVERED)}"
