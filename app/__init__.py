"""Flask application factory for the Lab API project."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .config import Settings, settings
from .extensions import close_db, init_extensions, limiter
from .utils.errors import register_error_handlers

PACKAGE_ROOT = Path(__file__).resolve().parent


def create_app(settings_override: Settings | None = None) -> Flask:
    """Application factory used by both CLI commands and WSGI servers."""

    app = Flask(__name__, template_folder="templates", static_folder="static")

    app_settings = settings_override or settings
    app.config.from_mapping(APP_SETTINGS=app_settings)

    init_extensions(app, app_settings)
    register_error_handlers(app)
    configure_logging(app)
    configure_cors(app, app_settings)
    register_blueprints(app)
    register_shellcontext(app)
    register_cli(app)
    close_db(app)

    @app.route("/healthz", methods=["GET"])
    @limiter.exempt
    def healthcheck() -> Any:
        return jsonify(status="ok"), 200

    return app


def configure_logging(app: Flask) -> None:
    """Set up structured or plain logging."""

    log_level = logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    app.logger.setLevel(log_level)


def configure_cors(app: Flask, app_settings: Settings) -> None:
    """Optionally enable CORS."""

    if app_settings.cors_allowed_origins:
        CORS(app, resources={r"/api/*": {"origins": app_settings.cors_allowed_origins}})


def register_blueprints(app: Flask) -> None:
    """Import and register application blueprints."""

    from flask_swagger_ui import get_swaggerui_blueprint

    from .routes import (
        auth_bp,
        crud_bp,
        docs_bp,
        files_bp,
        health_bp,
        labs_bp,
        samples_bp,
        web_bp,
    )

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(crud_bp, url_prefix="/api/v1")
    app.register_blueprint(docs_bp, url_prefix="/api/v1")
    app.register_blueprint(labs_bp, url_prefix="/api/v1")
    app.register_blueprint(samples_bp, url_prefix="/api/v1")
    app.register_blueprint(health_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(web_bp, url_prefix="/web")

    if app.config["APP_SETTINGS"].swagger_ui_enabled:
        swagger_bp = get_swaggerui_blueprint(
            "/docs",
            "/openapi.yaml",
            config={"app_name": "Lab API"},
        )
        app.register_blueprint(swagger_bp, url_prefix="/docs")

    @app.route("/openapi.yaml", methods=["GET"])
    def openapi_spec() -> Any:
        return send_from_directory(str(PACKAGE_ROOT.parent), "openapi.yaml")


def register_shellcontext(app: Flask) -> None:
    """Shell context for flask shell."""

    from . import models
    from .extensions import db

    @app.shell_context_processor
    def shell_context() -> dict[str, Any]:
        return {"db": db, "models": models}


def register_cli(app: Flask) -> None:
    """Custom CLI commands."""

    from .services.auth_service import create_user_cli

    create_user_cli(app)
