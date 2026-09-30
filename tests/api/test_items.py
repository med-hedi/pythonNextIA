from typing import Any

import pytest
from httpx import AsyncClient

URL = "/api/v1/items"


async def create_item(client: AsyncClient, **overrides: Any) -> dict[str, Any]:
    payload = {"name": "Clavier", "description": "Mécanique"} | overrides
    response = await client.post(URL, json=payload)
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


async def test_create_item(auth_client: AsyncClient) -> None:
    item = await create_item(auth_client, name="  Souris  ")

    assert item["id"] > 0
    assert item["name"] == "Souris"  # espaces supprimés par le schéma
    assert item["is_active"] is True
    assert "created_at" in item


async def test_create_item_with_duplicate_name_returns_409(auth_client: AsyncClient) -> None:
    await create_item(auth_client, name="Écran")

    response = await auth_client.post(URL, json={"name": "Écran"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "x" * 101},
        {"name": "ok", "unknown_field": 1},
    ],
)
async def test_create_item_with_invalid_payload_returns_422(
    auth_client: AsyncClient, payload: dict[str, Any]
) -> None:
    response = await auth_client.post(URL, json=payload)

    assert response.status_code == 422


async def test_get_item(auth_client: AsyncClient) -> None:
    created = await create_item(auth_client)

    response = await auth_client.get(f"{URL}/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


async def test_get_missing_item_returns_404(auth_client: AsyncClient) -> None:
    response = await auth_client.get(f"{URL}/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_list_items_is_paginated(auth_client: AsyncClient) -> None:
    for i in range(5):
        await create_item(auth_client, name=f"item-{i}")

    response = await auth_client.get(URL, params={"offset": 1, "limit": 2})

    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 5
    assert [item["name"] for item in page["items"]] == ["item-1", "item-2"]


async def test_list_items_rejects_invalid_limit(auth_client: AsyncClient) -> None:
    response = await auth_client.get(URL, params={"limit": 1000})

    assert response.status_code == 422


async def test_update_item_partially(auth_client: AsyncClient) -> None:
    created = await create_item(auth_client)

    response = await auth_client.patch(f"{URL}/{created['id']}", json={"is_active": False})

    assert response.status_code == 200
    updated = response.json()
    assert updated["is_active"] is False
    assert updated["name"] == created["name"]  # champ non envoyé = inchangé


async def test_update_item_with_taken_name_returns_409(auth_client: AsyncClient) -> None:
    await create_item(auth_client, name="A")
    item_b = await create_item(auth_client, name="B")

    response = await auth_client.patch(f"{URL}/{item_b['id']}", json={"name": "A"})

    assert response.status_code == 409


async def test_update_item_with_null_name_returns_422(auth_client: AsyncClient) -> None:
    created = await create_item(auth_client)

    response = await auth_client.patch(f"{URL}/{created['id']}", json={"name": None})

    assert response.status_code == 422


async def test_delete_item(auth_client: AsyncClient) -> None:
    created = await create_item(auth_client)

    response = await auth_client.delete(f"{URL}/{created['id']}")
    assert response.status_code == 204

    response = await auth_client.get(f"{URL}/{created['id']}")
    assert response.status_code == 404


async def test_items_are_publicly_readable(client: AsyncClient, auth_client: AsyncClient) -> None:
    created = await create_item(auth_client)

    assert (await client.get(URL)).status_code == 200
    assert (await client.get(f"{URL}/{created['id']}")).status_code == 200


async def test_item_writes_require_authentication(
    client: AsyncClient, auth_client: AsyncClient
) -> None:
    created = await create_item(auth_client)
    item_url = f"{URL}/{created['id']}"

    assert (await client.post(URL, json={"name": "Anonyme"})).status_code == 401
    assert (await client.patch(item_url, json={"name": "Anonyme"})).status_code == 401
    assert (await client.delete(item_url)).status_code == 401
