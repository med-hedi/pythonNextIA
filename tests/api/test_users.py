from httpx import AsyncClient

from app.modules.users.models import User
from tests.conftest import login

ME_URL = "/api/v1/users/me"
USERS_URL = "/api/v1/users"


async def test_read_me(auth_client: AsyncClient, user: User) -> None:
    response = await auth_client.get(ME_URL)

    assert response.status_code == 200
    assert response.json()["email"] == user.email


async def test_update_my_full_name(auth_client: AsyncClient) -> None:
    response = await auth_client.patch(ME_URL, json={"full_name": "Grace Hopper"})

    assert response.status_code == 200
    assert response.json()["full_name"] == "Grace Hopper"


async def test_change_my_password(
    auth_client: AsyncClient, client: AsyncClient, user: User
) -> None:
    response = await auth_client.patch(ME_URL, json={"password": "a-brand-new-password"})
    assert response.status_code == 200

    await login(client, user.email, "a-brand-new-password")
    old = await client.post(
        "/api/v1/auth/token", data={"username": user.email, "password": "correct-horse-battery"}
    )
    assert old.status_code == 401


async def test_cannot_escalate_privileges_via_profile_update(auth_client: AsyncClient) -> None:
    response = await auth_client.patch(ME_URL, json={"is_superuser": True})

    assert response.status_code == 422


async def test_null_password_is_rejected(auth_client: AsyncClient) -> None:
    response = await auth_client.patch(ME_URL, json={"password": None})

    assert response.status_code == 422


async def test_list_users_is_forbidden_for_regular_users(auth_client: AsyncClient) -> None:
    response = await auth_client.get(USERS_URL)

    assert response.status_code == 403


async def test_list_users_as_admin(admin_client: AsyncClient) -> None:
    response = await admin_client.get(USERS_URL)

    assert response.status_code == 200
    assert response.json()["total"] == 1
