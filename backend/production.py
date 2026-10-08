"""Production entry point: python -m backend.production."""
import os
from flask_migrate import upgrade
from waitress import serve
from backend.app import create_app
from backend.config import BASE_DIR


def main():
    app = create_app()
    with app.app_context():
        upgrade(directory=str(BASE_DIR / "migrations"))
    serve(app, host=os.environ.get("HOST", "0.0.0.0"),
          port=int(os.environ.get("PORT", "8080")),
          threads=int(os.environ.get("WAITRESS_THREADS", "4")),
          clear_untrusted_proxy_headers=not app.config["TRUST_PROXY"])


if __name__ == "__main__":
    main()
