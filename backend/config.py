import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent


def load_config():
    env_file = BASE_DIR / ".env"
    if not env_file.exists() and not os.environ.get("SECRET_KEY"):
        try:
            with env_file.open("x", encoding="utf-8") as stream:
                stream.write(f"SECRET_KEY={secrets.token_hex(32)}\n")
        except FileExistsError:
            pass
    load_dotenv(env_file)
    secret = os.environ.get("SECRET_KEY", "")
    if len(secret) < 32 or secret.startswith("replace-"):
        raise RuntimeError("Set SECRET_KEY to a random value of at least 32 characters in backend/.env.")
    return {
        "SECRET_KEY": secret,
        "SQLALCHEMY_DATABASE_URI": os.environ.get(
            "DATABASE_URL", f"sqlite:///{(BASE_DIR / 'database' / 'app.db').as_posix()}"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "MAX_CONTENT_LENGTH": 8 * 1024 * 1024,
        "TOKEN_MAX_AGE": int(os.environ.get("TOKEN_MAX_AGE", "86400")),
        "CORS_ORIGINS": [v.strip() for v in os.environ.get(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if v.strip()],
    }
