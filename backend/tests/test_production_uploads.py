import base64
import secrets
from io import BytesIO

import pytest
from PIL import Image
from flask_migrate import upgrade
from backend.app import create_app
from backend.config import BASE_DIR, load_config
from backend.extensions import db
from backend.models import User
from backend.services.auth import create_user


def image_data(format="PNG", size=(40, 30)):
    output = BytesIO()
    Image.new("RGB", size, "purple").save(output, format=format)
    mime = "jpeg" if format == "JPEG" else format.lower()
    return f"data:image/{mime};base64," + base64.b64encode(output.getvalue()).decode()


@pytest.mark.parametrize("format", ["PNG", "JPEG", "GIF", "WEBP"])
def test_profile_photo_is_normalized_and_private(client, app, accounts, format):
    original = image_data(format)
    headers = accounts["owner"]["headers"]
    assert client.put("/api/profile", json={"avatar": original}).status_code == 401
    response = client.put("/api/profile", headers=headers, json={"avatar": original})
    assert response.status_code == 200
    photo = response.json["data"]["avatar"]
    assert photo.startswith("data:image/webp;base64,")
    with Image.open(BytesIO(base64.b64decode(photo.split(",", 1)[1]))) as normalized:
        assert normalized.size == (256, 256)
        assert normalized.format == "WEBP"
        assert not normalized.getexif()
    assert client.get("/api/profile", headers=headers).json["data"]["avatar"] == photo
    assert client.get("/api/users/" + str(accounts["owner"]["id"])).status_code == 401
    with app.app_context():
        assert db.session.get(User, accounts["owner"]["id"]).avatar == photo
        assert not db.session.get(User, accounts["other"]["id"]).avatar


@pytest.mark.parametrize("value", [
    "data:image/svg+xml;base64,PHN2Zy8+", "data:image/png;base64,invalid!",
    "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\ntruncated").decode(),
    "data:image/png;base64," + base64.b64encode(b"x" * (5 * 1024 * 1024 + 1)).decode(),
    "javascript:alert(1)",
], ids=["svg", "invalid-base64", "truncated-png", "over-5mb", "unsafe-url"])
def test_invalid_photo_does_not_replace_existing_avatar(client, app, accounts, value):
    with app.app_context():
        before = db.session.get(User, accounts["owner"]["id"]).avatar
    response = client.put("/api/profile", headers=accounts["owner"]["headers"], json={"avatar": value})
    assert response.status_code == 400
    with app.app_context():
        assert db.session.get(User, accounts["owner"]["id"]).avatar == before


def test_authentication_endpoints_are_rate_limited():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "RATELIMIT_ENABLED": True,
                      "RATELIMIT_STORAGE_URI": "memory://",
                      "AUTH_LOGIN_LIMIT": "2 per minute"})
    with app.app_context():
        db.create_all()
    client = app.test_client()
    for endpoint in ("login",):
        for _ in range(2):
            assert client.post("/api/auth/" + endpoint, json={}).status_code == 400
        response = client.post("/api/auth/" + endpoint, json={})
        assert response.status_code == 429
        assert "Retry-After" in response.headers
    assert client.get("/api/posts").status_code == 401
    assert client.post("/api/auth/register", json={}).status_code == 401
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_production_config_requires_persistent_database_and_shared_limits(monkeypatch):
    monkeypatch.setattr("backend.config.load_dotenv", lambda *_: None)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", secrets.token_hex(32))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        load_config()
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        load_config()
    monkeypatch.setenv("DATABASE_URL", "postgres://user:password@localhost/bcommunity")
    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "memory://")
    with pytest.raises(RuntimeError, match="Redis"):
        load_config()
    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "redis://localhost:6379")
    config = load_config()
    assert config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql+psycopg://")
    assert config["CORS_ORIGINS"] == []
    monkeypatch.setenv("SECRET_KEY", "short")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        load_config()


def test_built_frontend_routes_and_probe_do_not_expose_api_data(app, client, tmp_path):
    (tmp_path / "index.html").write_text('<html><div id="app"></div></html>', encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('app')", encoding="utf-8")
    app.config["FRONTEND_DIST"] = str(tmp_path)
    for path in ("/", "/auth", "/register", "/questions", "/post/10", "/admin/users"):
        response = client.get(path)
        assert response.status_code == 200 and b'<div id="app">' in response.data
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/missing.js").status_code == 404
    assert client.get("/../backend/.env").status_code == 404
    assert client.get("/api/future-private-data").status_code == 401
    assert client.get("/healthz").json == {"status": "ok"}
    assert client.get("/api/health").status_code == 401


def test_account_photo_and_session_persist_after_application_restart(tmp_path):
    config = {"TESTING": True, "SECRET_KEY": secrets.token_hex(32), "RATELIMIT_ENABLED": False,
              "SQLALCHEMY_DATABASE_URI": "sqlite:///" + (tmp_path / "persistent.db").as_posix()}
    first = create_app(config)
    with first.app_context():
        upgrade(directory=str(BASE_DIR / "migrations"))
    secret = secrets.token_urlsafe(18)
    data = {"name": "Persisted", "email": "persisted@example.com", "password": secret}
    client = first.test_client()
    with first.app_context():
        create_user(data)
        db.session.commit()
    token = client.post("/api/auth/login", json={"email": data["email"], "password": secret}).json["data"]["token"]
    headers = {"Authorization": "Bearer " + token}
    photo = client.put("/api/profile", headers=headers, json={"avatar": image_data()}).json["data"]["avatar"]
    with first.app_context():
        db.session.remove()
        db.engine.dispose()
    second = create_app(config)
    with second.app_context():
        upgrade(directory=str(BASE_DIR / "migrations"))
    restored = second.test_client()
    response = restored.get("/api/auth/me", headers=headers)
    assert response.status_code == 200 and response.json["data"]["avatar"] == photo
    assert restored.post("/api/auth/login", json={"email": data["email"], "password": secret}).status_code == 200
    assert restored.post("/api/auth/logout", headers=headers).status_code == 200
    assert restored.get("/api/posts", headers=headers).status_code == 401
    with second.app_context():
        db.session.remove()
        db.engine.dispose()



def test_data_transfer_preserves_passwords_and_photos_and_refuses_overwrite(app, accounts, tmp_path):
    from sqlalchemy import create_engine
    from backend.transfer_data import transfer
    from backend.models import Post
    target = create_engine("sqlite:///" + (tmp_path / "target.db").as_posix())
    db.metadata.create_all(target)
    try:
        with app.app_context():
            owner = db.session.get(User, accounts["owner"]["id"])
            owner.avatar = image_data()
            db.session.add(Post(author_id=owner.id, content="Keep existing content"))
            db.session.commit()
            password_hash = owner.password_hash
            source = db.engine
            counts = transfer(source, target)
            assert counts["users"] == 4 and counts["posts"] == 1 and counts["auth_sessions"] == 4
            with target.connect() as reader:
                rows = reader.execute(db.select(User.__table__)).mappings().all()
                saved = next(row for row in rows if row["id"] == owner.id)
                assert saved["password_hash"] == password_hash and saved["avatar"] == owner.avatar
            with pytest.raises(RuntimeError, match="not empty"):
                transfer(source, target)
            assert db.session.get(User, owner.id).password_hash == password_hash
    finally:
        target.dispose()


def test_existing_users_survive_phone_column_migration(tmp_path):
    config = {"TESTING": True, "RATELIMIT_ENABLED": False,
              "SQLALCHEMY_DATABASE_URI": "sqlite:///" + (tmp_path / "legacy.db").as_posix()}
    app = create_app(config)
    with app.app_context():
        upgrade(directory=str(BASE_DIR / "migrations"), revision="c2737edae6ef")
        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash(secrets.token_urlsafe(18))
        db.session.execute(db.text("INSERT INTO users (id, name, email, password_hash, avatar, bio, role, "
            "account_role, skills, reputation, status, joined_at, auth_version) VALUES "
            "(1, 'Existing', 'legacy@example.com', :hashed, '', '', 'Beginner', 'User', '[]', 0, 'Active', "
            "'2026-10-08 00:00:00', 0)"), {"hashed": hashed})
        db.session.commit()
        upgrade(directory=str(BASE_DIR / "migrations"))
        user = db.session.get(User, 1)
        assert user.email == "legacy@example.com" and user.password_hash == hashed and user.phone == ""
        db.session.remove()
        db.engine.dispose()


def test_postgresql_migrations_compile_without_connecting(capsys):
    app = create_app({"TESTING": True, "RATELIMIT_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://user:password@localhost/bcommunity"})
    with app.app_context():
        upgrade(directory=str(BASE_DIR / "migrations"), sql=True)
        db.engine.dispose()
    sql = capsys.readouterr().out
    assert "CREATE TABLE users" in sql and "CREATE TABLE auth_sessions" in sql
    assert "ADD COLUMN phone" in sql and "DEFAULT '' NOT NULL" in sql
    assert "DROP TABLE users" not in sql
