"""Extension instances and registration helpers."""

from __future__ import annotations

from typing import Any

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

from .config import Settings

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


db = SQLAlchemy(metadata=metadata)
jwt = JWTManager()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


def init_extensions(app: Flask, settings: Settings) -> None:
    """Bind extensions to the Flask application."""

    app.config.update(
        SQLALCHEMY_DATABASE_URI=settings.database_uri,
        SQLALCHEMY_ENGINE_OPTIONS={"future": True},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=settings.secret_key,
        JWT_SECRET_KEY=settings.jwt_secret_key,
        JWT_ACCESS_TOKEN_EXPIRES=settings.jwt_access_delta,
        JWT_REFRESH_TOKEN_EXPIRES=settings.jwt_refresh_delta,
    )

    storage_uri = settings.rate_redis_url or "memory://"
    app.config.setdefault("RATELIMIT_STORAGE_URI", storage_uri)
    limiter.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db=db)
    jwt.init_app(app)


def close_db(app: Flask) -> None:
    """Ensure database sessions close on teardown."""

    @app.teardown_appcontext
    def shutdown_session(_: Any) -> None:
        db.session.remove()
