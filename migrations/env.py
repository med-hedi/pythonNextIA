"""Environnement Alembic asynchrone, branché sur la configuration de l'application."""

import asyncio
from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadonnées de tous les modèles : utilisées par `alembic revision --autogenerate`.
target_metadata = Base.metadata
database_url = get_settings().database_url


def configure(**kwargs: Any) -> None:
    context.configure(
        target_metadata=target_metadata,
        compare_type=True,
        # "batch mode" : nécessaire pour les ALTER TABLE sous SQLite, sans effet ailleurs.
        render_as_batch=database_url.startswith("sqlite"),
        **kwargs,
    )


def run_migrations_offline() -> None:
    """Génère le SQL sans se connecter (`alembic upgrade head --sql`)."""
    configure(url=database_url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(database_url, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
