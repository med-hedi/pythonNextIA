"""Fixtures partagées : chaque test obtient une application et une base neuves."""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from app.core.config import Settings
from app.db.models import Base
from app.main import create_app
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService

PASSWORD = "correct-horse-battery"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,  # les tests ne doivent jamais dépendre du .env local
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
    )


@pytest.fixture
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    application = create_app(settings)
    async with application.state.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield application
    await application.state.engine.dispose()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Client anonyme."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def create_user(app: FastAPI, email: str, *, is_superuser: bool = False) -> User:
    async with app.state.session_factory() as session:
        data = UserCreate(email=email, password=SecretStr(PASSWORD))
        user: User = await UserService(session).create(data, is_superuser=is_superuser)
        return user


async def login(client: AsyncClient, email: str, password: str = PASSWORD) -> dict[str, str]:
    """Se connecte et retourne l'en-tête `Authorization` à envoyer."""
    response = await client.post(
        "/api/v1/auth/token", data={"username": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
async def user(app: FastAPI) -> User:
    return await create_user(app, "user@example.com")


@pytest.fixture
async def auth_client(app: FastAPI, user: User) -> AsyncIterator[AsyncClient]:
    """Client authentifié en tant qu'utilisateur standard."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        ac.headers.update(await login(ac, user.email))
        yield ac


@pytest.fixture
async def admin_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Client authentifié en tant qu'administrateur."""
    admin = await create_user(app, "admin@example.com", is_superuser=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        ac.headers.update(await login(ac, admin.email))
        yield ac
