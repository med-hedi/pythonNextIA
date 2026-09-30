from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pwdlib.hashers.argon2 import Argon2Hasher

from app.modules.users.models import User
from tests.conftest import PASSWORD, create_user, login

REGISTER_URL = "/api/v1/auth/register"
TOKEN_URL = "/api/v1/auth/token"
ME_URL = "/api/v1/users/me"


async def test_register(client: AsyncClient) -> None:
    response = await client.post(
        REGISTER_URL,
        json={"email": "New@Example.com", "password": PASSWORD, "full_name": "Ada"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"  # normalisé en minuscules
    assert body["is_superuser"] is False
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_with_existing_email_returns_409(client: AsyncClient, user: User) -> None:
    response = await client.post(
        REGISTER_URL, json={"email": user.email.upper(), "password": PASSWORD}
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": PASSWORD},
        {"email": "a@example.com", "password": "short"},
        {"email": "a@example.com", "password": PASSWORD, "is_superuser": True},
    ],
)
async def test_register_with_invalid_payload_returns_422(
    client: AsyncClient, payload: dict[str, Any]
) -> None:
    response = await client.post(REGISTER_URL, json=payload)

    assert response.status_code == 422
    assert PASSWORD not in response.text  # le mot de passe ne fuit pas dans l'erreur


async def test_login_returns_bearer_token(client: AsyncClient, user: User) -> None:
    response = await client.post(TOKEN_URL, data={"username": user.email, "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["access_token"]


@pytest.mark.parametrize(
    ("email", "password"),
    [("user@example.com", "wrong-password"), ("unknown@example.com", PASSWORD)],
)
async def test_login_with_bad_credentials_returns_401(
    client: AsyncClient, user: User, email: str, password: str
) -> None:
    response = await client.post(TOKEN_URL, data={"username": email, "password": password})

    assert response.status_code == 401
    # Même message dans les deux cas : on ne révèle pas si l'email existe.
    assert response.json()["error"]["message"] == "Email ou mot de passe incorrect."


async def test_login_is_case_insensitive_on_email(client: AsyncClient, user: User) -> None:
    await login(client, user.email.upper())


async def _deactivate(app: FastAPI, user: User) -> None:
    async with app.state.session_factory() as session:
        db_user = await session.get(User, user.id)
        db_user.is_active = False
        await session.commit()


async def test_inactive_user_cannot_login(app: FastAPI, client: AsyncClient, user: User) -> None:
    await _deactivate(app, user)

    response = await client.post(TOKEN_URL, data={"username": user.email, "password": PASSWORD})

    assert response.status_code == 403


async def test_token_of_deactivated_user_is_rejected(
    app: FastAPI, auth_client: AsyncClient, user: User
) -> None:
    await _deactivate(app, user)

    response = await auth_client.get(ME_URL)

    assert response.status_code == 401


async def test_protected_route_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"


async def test_protected_route_with_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.get(ME_URL, headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401


async def test_token_with_unknown_user_returns_401(app: FastAPI, client: AsyncClient) -> None:
    ghost = await create_user(app, "ghost@example.com")
    headers = await login(client, ghost.email)
    async with app.state.session_factory() as session:
        await session.delete(await session.get(User, ghost.id))
        await session.commit()

    response = await client.get(ME_URL, headers=headers)

    assert response.status_code == 401


async def test_outdated_password_hash_is_upgraded_on_login(
    app: FastAPI, client: AsyncClient, user: User
) -> None:
    weak_hasher = Argon2Hasher(time_cost=1, memory_cost=1024, parallelism=1)
    async with app.state.session_factory() as session:
        db_user = await session.get(User, user.id)
        db_user.hashed_password = weak_hasher.hash(PASSWORD)
        await session.commit()
        old_hash = db_user.hashed_password

    await login(client, user.email)

    async with app.state.session_factory() as session:
        db_user = await session.get(User, user.id)
        assert db_user.hashed_password != old_hash
        assert "m=1024," not in db_user.hashed_password
