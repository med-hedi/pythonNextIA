import asyncio

import pytest
from fastapi import FastAPI

from app import cli
from app.core.config import Settings
from app.modules.users.service import UserService
from tests.conftest import PASSWORD, create_user

# La CLI appelle asyncio.run() : les tests l'exécutent dans un thread
# séparé (asyncio.to_thread), hors de la boucle d'événements du test.


@pytest.fixture
def cli_env(monkeypatch: pytest.MonkeyPatch, settings: Settings, app: FastAPI) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: settings)
    monkeypatch.setattr("getpass.getpass", lambda _prompt: PASSWORD)


@pytest.mark.usefixtures("cli_env")
async def test_create_superuser(app: FastAPI) -> None:
    code = await asyncio.to_thread(cli.main, ["create-superuser", "--email", "Boss@Example.com"])

    assert code == 0
    async with app.state.session_factory() as session:
        admin = await UserService(session).get_by_email("boss@example.com")
    assert admin is not None
    assert admin.is_superuser


@pytest.mark.usefixtures("cli_env")
async def test_create_superuser_with_existing_email_fails(app: FastAPI) -> None:
    await create_user(app, "taken@example.com")

    code = await asyncio.to_thread(cli.main, ["create-superuser", "--email", "taken@example.com"])

    assert code == 1


@pytest.mark.usefixtures("cli_env")
async def test_create_superuser_with_invalid_email_fails() -> None:
    code = await asyncio.to_thread(cli.main, ["create-superuser", "--email", "not-an-email"])

    assert code == 1
