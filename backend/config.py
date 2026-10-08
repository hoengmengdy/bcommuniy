import os
import secrets
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

BASE_DIR = Path(__file__).resolve().parent


def load_config():
    env_file = BASE_DIR / ".env"
    load_dotenv(env_file)
    environment = os.environ.get("APP_ENV", "development").lower()
    if environment not in ("development", "production"):
        raise RuntimeError("APP_ENV must be development or production.")
    production = environment == "production"
    secret = os.environ.get("SECRET_KEY", "")
    if not secret and not env_file.exists() and not production:
        secret = secrets.token_hex(32)
        try:
            with env_file.open("x", encoding="utf-8") as stream:
                stream.write(f"SECRET_KEY={secret}\n")
        except FileExistsError:
            load_dotenv(env_file)
            secret = os.environ.get("SECRET_KEY", "")
    if len(secret) < 32 or secret.startswith("replace-"):
        raise RuntimeError("Set SECRET_KEY to a stable random value of at least 32 characters.")
    database_url = os.environ.get("DATABASE_URL", "")
    if production and not database_url:
        raise RuntimeError("DATABASE_URL is required in production; use a persistent PostgreSQL database.")
    database_url = database_url or f"sqlite:///{(BASE_DIR / 'database' / 'app.db').as_posix()}"
    for prefix in ("postgres://", "postgresql://"):
        if database_url.startswith(prefix):
            database_url = "postgresql+psycopg://" + database_url[len(prefix):]
            break
    if production and make_url(database_url).get_backend_name() != "postgresql":
        raise RuntimeError("Production requires PostgreSQL; container-local SQLite is not persistent.")
    rate_storage = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    if production and not rate_storage.startswith(("redis://", "rediss://")):
        raise RuntimeError("Set RATELIMIT_STORAGE_URI to shared Redis storage in production.")
    token_age = int(os.environ.get("TOKEN_MAX_AGE", "86400"))
    if token_age <= 0:
        raise RuntimeError("TOKEN_MAX_AGE must be a positive number of seconds.")
    return {
        "APP_ENV": environment,
        "SECRET_KEY": secret,
        "SQLALCHEMY_DATABASE_URI": database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True},
        "MAX_CONTENT_LENGTH": 8 * 1024 * 1024,
        "TOKEN_MAX_AGE": token_age,
        "CORS_ORIGINS": [v.strip() for v in os.environ.get(
            "CORS_ORIGINS", "" if production else "http://localhost:5173,http://127.0.0.1:5173").split(",") if v.strip()],
        "FRONTEND_DIST": str(Path(os.environ.get("FRONTEND_DIST", BASE_DIR.parent / "dist")).resolve()),
        "TRUST_PROXY": os.environ.get("TRUST_PROXY", "0") == "1",
        "RATELIMIT_STORAGE_URI": rate_storage,
        "RATELIMIT_HEADERS_ENABLED": True,
        "AUTH_LOGIN_LIMIT": os.environ.get("AUTH_LOGIN_LIMIT", "10 per minute;100 per hour"),
    }
