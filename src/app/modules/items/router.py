"""Endpoints HTTP des items : traduction HTTP <-> service, rien de plus."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import PaginationDep, SessionDep
from app.core.pagination import Page
from app.modules.items.schemas import ItemCreate, ItemRead, ItemUpdate
from app.modules.items.service import ItemService

router = APIRouter(prefix="/items", tags=["items"])


def get_item_service(session: SessionDep) -> ItemService:
    return ItemService(session)


ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]


@router.get("", summary="Lister les items (paginé)")
async def list_items(service: ItemServiceDep, pagination: PaginationDep) -> Page[ItemRead]:
    items, total = await service.list_page(offset=pagination.offset, limit=pagination.limit)
    return Page[ItemRead](
        items=[ItemRead.model_validate(item) for item in items],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Créer un item")
async def create_item(service: ItemServiceDep, data: ItemCreate) -> ItemRead:
    return ItemRead.model_validate(await service.create(data))


@router.get("/{item_id}", summary="Récupérer un item")
async def get_item(service: ItemServiceDep, item_id: int) -> ItemRead:
    return ItemRead.model_validate(await service.get(item_id))


@router.patch("/{item_id}", summary="Modifier partiellement un item")
async def update_item(service: ItemServiceDep, item_id: int, data: ItemUpdate) -> ItemRead:
    return ItemRead.model_validate(await service.update(item_id, data))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer un item")
async def delete_item(service: ItemServiceDep, item_id: int) -> None:
    await service.delete(item_id)
