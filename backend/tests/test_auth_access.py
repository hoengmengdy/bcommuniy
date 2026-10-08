import secrets
from unittest.mock import patch

import pytest
from itsdangerous import TimestampSigner

from backend.extensions import db
from backend.models import User


def protected_routes(app):
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api/"):
            continue
        for method in rule.methods - {"OPTIONS"}:
            if (method, rule.endpoint) == ("POST", "auth.login"):
                continue
            path = rule.rule
            for name in rule.arguments:
                path = path.replace(f"<int:{name}>", "1")
            yield method, path


def assert_all_protected(client, headers=None):
    for method, path in protected_routes(client.application):
        response = client.open(path, method=method, headers=headers, json={})
        assert response.status_code == 401, (method, path, response.status_code)
        assert response.headers["Cache-Control"] == "no-store"
        if method != "HEAD":
            assert "data" not in response.json
            assert response.json["error"]["status"] == 401


@pytest.mark.parametrize("authorization", [None, "Bearer forged", "Basic ignored", "Bearer "])
def test_every_api_requires_a_valid_session(client, authorization):
    assert_all_protected(client, {"Authorization": authorization} if authorization else None)


def test_new_api_routes_are_protected_automatically(app, client):
    app.add_url_rule("/api/future-content", "future_content", lambda: {"data": "private"})
    assert client.get("/api/future-content").status_code == 401


def test_login_access_refresh_logout_and_relogin(client, create_account):
    secret = secrets.token_urlsafe(18)
    credentials = {"email": "flow@example.com", "password": secret}
    assert client.get("/api/posts").status_code == 401
    create_account({"name": "Existing Flow Member", **credentials})
    login = client.post("/api/auth/login", json=credentials)
    assert login.status_code == 200
    data = login.json["data"]
    headers = {"Authorization": "Bearer " + data["token"]}
    assert client.get("/api/posts", headers=headers).status_code == 200
    # A fresh client represents a browser reload: only the stored token is needed.
    restored = client.application.test_client().get("/api/auth/me", headers=headers)
    assert restored.status_code == 200
    assert restored.json["meta"]["expiresAt"] == data["expiresAt"]
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    assert_all_protected(client, headers)
    assert client.post("/api/auth/login", json=credentials).status_code == 200


def test_expired_token_is_rejected_by_every_api(client, create_account):
    with patch.object(TimestampSigner, "get_timestamp", return_value=1):
        data = create_account({
            "name": "Expired", "email": "expired-access@example.com",
            "password": secrets.token_urlsafe(18),
        })
    assert_all_protected(client, {"Authorization": "Bearer " + data["token"]})


def test_disabled_account_cannot_read_content(client, app, accounts):
    with app.app_context():
        db.session.get(User, accounts["owner"]["id"]).status = "Inactive"
        db.session.commit()
    assert_all_protected(client, accounts["owner"]["headers"])


def test_cors_preflights_remain_data_free(client):
    response = client.options("/api/posts", headers={
        "Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization",
    })
    assert response.status_code == 200
    assert response.data == b""
    assert response.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5173"


@pytest.mark.parametrize("path", [
    "/api/auth/register", "/api/auth/signup", "/api/register", "/api/signup", "/api/create-account",
])
def test_self_registration_is_unavailable(client, app, accounts, path):
    with app.app_context():
        before = db.session.execute(db.select(User.id, User.password_hash).order_by(User.id)).all()
    data = {"name": "Uninvited", "email": "uninvited@example.com", "password": secrets.token_urlsafe(18)}
    for actor, expected in [(None, 401), (accounts["owner"]["headers"], 405),
                            (accounts["admin"]["headers"], 405)]:
        response = client.post(path, headers=actor, json=data)
        assert response.status_code == expected, (path, response.json)
        assert "data" not in response.json
    with app.app_context():
        after = db.session.execute(db.select(User.id, User.password_hash).order_by(User.id)).all()
        assert after == before, "Rejected registration cannot create users or change passwords"
    assert all(rule.endpoint != "auth.register" for rule in app.url_map.iter_rules())


def test_anonymous_and_ordinary_users_cannot_provision_accounts(client, app, accounts):
    data = {"name": "Uninvited", "email": "uninvited@example.com", "password": secrets.token_urlsafe(18)}
    assert client.post("/api/users", json=data).status_code == 401
    assert client.post("/api/users", headers=accounts["owner"]["headers"], json=data).status_code == 403
    assert client.post("/api/auth/login", json={"email": data["email"], "password": data["password"]}).status_code == 401
    with app.app_context():
        assert db.session.scalar(db.select(User).where(User.email == data["email"])) is None


@pytest.mark.parametrize("changes", [
    {"name": " "}, {"email": "not-an-email"}, {"password": "short", "confirmPassword": "short"},
    {"confirmPassword": "different-password"}, {"confirmPassword": None},
    {"role": "Admin"}, {"accountRole": "Admin"}, {"status": "Active"},
])
def test_invalid_registration_creates_nothing(client, app, changes):
    secret = secrets.token_urlsafe(18)
    response = client.post("/api/auth/register", json={"name": "Member", "email": "invalid@example.com",
        "password": secret, "confirmPassword": secret, **changes})
    assert response.status_code == 401
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 0


def test_duplicate_registration_preserves_existing_password(client, app, create_account):
    existing = create_account({"name": "Existing", "email": "duplicate@example.com",
                               "password": secrets.token_urlsafe(18)})
    with app.app_context():
        before = db.session.get(User, existing["user"]["id"]).password_hash
    secret = secrets.token_urlsafe(18)
    response = client.post("/api/auth/register", json={"name": "Replacement", "email": "DUPLICATE@example.com",
                                                       "password": secret, "confirmPassword": secret})
    assert response.status_code == 401
    with app.app_context():
        assert db.session.get(User, existing["user"]["id"]).password_hash == before
        assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 1


def test_public_member_profiles_hide_contact_information(client, accounts):
    response = client.get("/api/members", headers=accounts["owner"]["headers"])
    for user in response.json["data"]:
        assert not {"email", "phone", "password", "password_hash", "auth_version"} & user.keys()
