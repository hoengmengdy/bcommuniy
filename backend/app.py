"""Run from backend with python app.py, or import backend.app:create_app."""
import os
import sqlite3
import sys
from pathlib import Path

# Allow both python app.py and python -m flask --app backend.app.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import click
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_migrate import upgrade
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.config import BASE_DIR, load_config
from backend.extensions import db, migrate, limiter
from backend.models import User
from backend.routes import register_routes
from backend.services.auth import authenticate_request
from backend.utils.validation import APIError


@event.listens_for(Engine, "connect")
def sqlite_foreign_keys(connection, _):
    if isinstance(connection, sqlite3.Connection):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(load_config())
    if test_config:
        app.config.update(test_config)
    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=0, x_port=0, x_prefix=0)
    (BASE_DIR / "database").mkdir(exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db, directory=str(BASE_DIR / "migrations"), compare_type=True,
                     render_as_batch=True)
    if app.config["CORS_ORIGINS"]:
        CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
             allow_headers=["Authorization", "Content-Type"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    limiter.init_app(app)
    register_routes(app)

    @app.before_request
    def protect_api():
        # Deny by default, including future endpoints. OPTIONS carries no data
        # and must remain available for browser CORS preflight requests.
        if (request.path == "/api" or request.path.startswith("/api/")) and (
            request.method != "OPTIONS"
            and (request.method, request.endpoint) != ("POST", "auth.login")
        ):
            authenticate_request()

    @app.get("/api/health")
    def health():
        db.session.execute(db.text("SELECT 1"))
        return jsonify(data={"status": "ok", "database": "connected"})

    @app.get("/healthz")
    def liveness():
        # Hosting probes get only availability, never application or user data.
        db.session.execute(db.text("SELECT 1"))
        return jsonify(status="ok")

    @app.get("/")
    @app.get("/<path:frontend_path>")
    def frontend(frontend_path=""):
        if frontend_path == "api" or frontend_path.startswith("api/"):
            raise NotFound()
        directory = Path(app.config["FRONTEND_DIST"])
        candidate = (directory / frontend_path).resolve()
        if not candidate.is_relative_to(directory):
            raise NotFound()
        if frontend_path and candidate.is_file():
            return send_from_directory(directory, frontend_path)
        if frontend_path.startswith("assets/") or Path(frontend_path).suffix:
            raise NotFound()
        if not (directory / "index.html").is_file():
            raise NotFound("Frontend build is missing. Run npm run build.")
        # This is an empty SPA shell; protected data still requires API auth.
        return send_from_directory(directory, "index.html")

    @app.errorhandler(APIError)
    def validation_error(error):
        db.session.rollback()
        return jsonify(error={"message": error.message, "status": error.status}), error.status

    @app.errorhandler(IntegrityError)
    def conflict(error):
        db.session.rollback()
        return jsonify(error={"message": "A unique value already exists or a relationship is invalid.",
                              "status": 409}), 409

    @app.errorhandler(HTTPException)
    def http_error(error):
        db.session.rollback()
        return jsonify(error={"message": error.description, "status": error.code}), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled API error")
        return jsonify(error={"message": "An internal server error occurred.", "status": 500}), 500

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        if app.config["APP_ENV"] == "production" and request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.cli.command("create-admin")
    def create_admin():
        """Create an administrator from environment values or secure prompts."""
        from backend.services.auth import create_user
        address = os.environ.get("ADMIN_EMAIL") or click.prompt("Administrator email")
        name = os.environ.get("ADMIN_NAME") or click.prompt("Display name")
        secret = os.environ.get("ADMIN_PASSWORD") or click.prompt(
            "Password (8-128 characters)", hide_input=True, confirmation_prompt=True)
        with app.app_context():
            try:
                user = create_user({"name": name, "email": address, "password": secret,
                                    "role": "Admin"}, admin=True)
                db.session.commit()
                click.echo(f"Administrator created: {user.email}")
            except APIError as error:
                db.session.rollback()
                raise click.ClickException(error.message) from error

    return app


if __name__ == "__main__":
    application = create_app()
    with application.app_context():
        upgrade(directory=str(BASE_DIR / "migrations"))
    if len(sys.argv) > 1:
        with application.app_context():
            application.cli.main(args=sys.argv[1:], prog_name="python app.py")
    else:
        application.run(host=os.environ.get("HOST", "127.0.0.1"),
                        port=int(os.environ.get("PORT", "5000")),
                        debug=os.environ.get("FLASK_DEBUG", "0") == "1")
