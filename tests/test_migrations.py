"""Garde-fou : les migrations Alembic doivent refléter exactement les modèles."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.core.config import get_settings

ROOT = Path(__file__).parent.parent


@pytest.fixture
def alembic_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Config]:
    monkeypatch.setenv("APP_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'migrations.db'}")
    get_settings.cache_clear()
    yield Config(ROOT / "alembic.ini")
    get_settings.cache_clear()


def test_migrations_upgrade_and_downgrade(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")


def test_models_and_migrations_are_in_sync(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")

    # Échoue si `alembic revision --autogenerate` produirait une nouvelle migration.
    command.check(alembic_config)
