"""Alembic environment configuration."""

from __future__ import annotations

import logging
from logging.config import fileConfig

from alembic import context

from app import create_app
from app.extensions import db

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    app = create_app()
    with app.app_context():
        url = str(db.engine.url)
        context.configure(
            url=url,
            target_metadata=db.metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    app = create_app()
    with app.app_context():
        connectable = db.engine
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=db.metadata)
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
