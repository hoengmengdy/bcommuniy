import secrets
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app import create_app
from backend.extensions import db
from backend.services.auth import create_user, issue_token


@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "SECRET_KEY": secrets.token_hex(32),
                      "SQLALCHEMY_DATABASE_URI": "sqlite://", "RATELIMIT_ENABLED": False})
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
def create_account(app):
    # Trusted fixtures also exercise administrator-only account provisioning.
    def provision(data, admin=False):
        with app.app_context():
            user = create_user(data, admin=admin)
            token = issue_token(user)
            db.session.commit()
            return {"user": user.to_dict(private=True), "token": token}
    return provision


@pytest.fixture()
def accounts(create_account):
    result = {}
    for name in ("owner", "other", "outsider", "admin"):
        data = create_account({"name": name, "email": f"{name}@example.com",
                               "password": secrets.token_urlsafe(18),
                               **({"role": "Admin"} if name == "admin" else {})},
                              admin=name == "admin")
        result[name] = {"id": data["user"]["id"],
                        "headers": {"Authorization": "Bearer " + data["token"]}}
    return result
