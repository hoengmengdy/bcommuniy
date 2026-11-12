import secrets

from test_api import call  # records endpoint coverage for test_z_every_api_method_has_been_tested


def test_admin_tools_require_admin(client, accounts):
    for method, path in [("GET", "/api/admin/stats"), ("GET", "/api/admin/comments"),
                         ("POST", "/api/admin/broadcast"), ("POST", "/api/admin/users/bulk")]:
        response = client.open(path, method=method, headers=accounts["owner"]["headers"], json={})
        assert response.status_code == 403, path


def test_stats(client, accounts):
    admin = accounts["admin"]["headers"]
    client.post("/api/posts", headers=accounts["owner"]["headers"], json={"content": "hello"})
    data = call(client, "GET", "/api/admin/stats", headers=admin)
    assert data["totals"]["users"] == 4
    assert data["totals"]["posts"] == 1
    assert data["totals"]["admins"] == 1
    assert len(data["activity"]["signups"]) == 14
    assert data["activity"]["signups"][-1]["count"] == 4
    assert data["topContributors"][0]["name"] == "owner"


def test_reset_password_and_force_logout(client, accounts):
    admin, owner = accounts["admin"]["headers"], accounts["owner"]["headers"]
    uid = accounts["owner"]["id"]
    new = secrets.token_urlsafe(12)
    call(client, "POST", f"/api/admin/users/{uid}/password", headers=admin, data={"password": new})
    assert client.get("/api/auth/me", headers=owner).status_code == 401
    login = client.post("/api/auth/login", json={"email": "owner@example.com", "password": new})
    assert login.status_code == 200
    fresh = {"Authorization": "Bearer " + login.json["data"]["token"]}
    call(client, "POST", f"/api/admin/users/{uid}/logout", headers=admin)
    assert client.get("/api/auth/me", headers=fresh).status_code == 401
    me = accounts["admin"]["id"]
    assert client.post(f"/api/admin/users/{me}/logout", headers=admin).status_code == 400


def test_bulk_actions_protect_admin(client, accounts):
    admin = accounts["admin"]["headers"]
    ids = [accounts["owner"]["id"], accounts["other"]["id"]]
    assert call(client, "POST", "/api/admin/users/bulk", headers=admin,
                data={"ids": ids, "action": "deactivate"})["affected"] == 2
    assert client.get("/api/auth/me", headers=accounts["owner"]["headers"]).status_code == 401
    r = client.post("/api/admin/users/bulk", headers=admin,
                    json={"ids": [accounts["admin"]["id"]], "action": "delete"})
    assert r.status_code == 400
    r = client.post("/api/admin/users/bulk", headers=admin, json={"ids": ids, "action": "delete"})
    assert r.json["data"]["affected"] == 2
    assert client.get("/api/admin/stats", headers=admin).json["data"]["totals"]["users"] == 2


def test_reputation_broadcast_and_moderation(client, accounts):
    admin, owner = accounts["admin"]["headers"], accounts["owner"]["headers"]
    uid = accounts["owner"]["id"]
    assert call(client, "PUT", f"/api/admin/users/{uid}/reputation", headers=admin,
                data={"reputation": 250})["reputation"] == 250
    assert call(client, "POST", "/api/admin/broadcast", headers=admin,
                data={"message": "Maintenance tonight"})["recipients"] == 3
    notes = client.get("/api/notifications", headers=owner).json["data"]
    assert notes[0]["type"] == "system" and notes[0]["content"] == "Maintenance tonight"

    q = client.post("/api/questions", headers=owner, json={"title": "Why?", "content": "x"}).json["data"]
    client.post(f"/api/posts/{q['id']}/comments", headers=owner, json={"text": "because"})
    comments = call(client, "GET", "/api/admin/comments", headers=admin)
    assert comments[0]["text"] == "because" and comments[0]["postTitle"] == "Why?"
    assert call(client, "POST", f"/api/admin/posts/{q['id']}/solved", headers=admin)["isSolved"] is True
    assert call(client, "POST", "/api/admin/posts/bulk-delete", headers=admin, data={"ids": [q["id"]]})["affected"] == 1


def test_demo_account_is_member_and_protected(app, client, accounts):
    from backend.extensions import db
    from backend.services.demo import DEMO_EMAIL, DEMO_PASSWORD, ensure_demo_account
    with app.app_context():
        ensure_demo_account()
        ensure_demo_account()  # idempotent
        db.session.commit()
    login = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert login.status_code == 200
    user = login.json["data"]["user"] if "user" in login.json["data"] else client.get(
        "/api/auth/me", headers={"Authorization": "Bearer " + login.json["data"]["token"]}).json["data"]
    assert user["isAdmin"] is False
    demo = {"Authorization": "Bearer " + login.json["data"]["token"]}
    uid = user["id"]
    assert client.put(f"/api/users/{uid}", headers=demo, json={"password": "x" * 12}).status_code == 403
    assert client.put(f"/api/users/{uid}", headers=demo, json={"email": "mine@example.com"}).status_code == 403
    assert client.delete(f"/api/users/{uid}", headers=demo).status_code == 403
    assert client.put("/api/profile", headers=demo, json={"bio": "hi"}).status_code == 200
    assert client.put(f"/api/users/{uid}", headers=accounts["admin"]["headers"],
                      json={"password": "y" * 12}).status_code == 200
