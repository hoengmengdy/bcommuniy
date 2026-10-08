import secrets
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app import create_app
from backend.extensions import db
from backend.models import User


@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "SECRET_KEY": secrets.token_hex(32),
                      "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def accounts(app, client):
    result = {}
    for name in ("owner", "other", "outsider", "admin"):
        response = client.post("/api/auth/register", json={
            "name": name, "email": f"{name}@example.com", "password": secrets.token_urlsafe(18)})
        assert response.status_code == 201, response.json
        data = response.json["data"]
        result[name] = {"id": data["user"]["id"],
                        "headers": {"Authorization": "Bearer " + data["token"]}}
    with app.app_context():
        db.session.get(User, result["admin"]["id"]).account_role = "Admin"
        db.session.commit()
    return result
