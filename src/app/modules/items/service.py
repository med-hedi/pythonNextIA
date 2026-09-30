"""Logique métier des items : règles, validations transverses, transactions."""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.items.models import Item
from app.modules.items.repository import ItemRepository
from app.modules.items.schemas import ItemCreate, ItemUpdate


class ItemService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ItemRepository(session)

    async def get(self, item_id: int) -> Item:
        item = await self.repository.get(item_id)
        if item is None:
            raise NotFoundError(f"Item {item_id} introuvable.")
        return item

    async def list_page(self, *, offset: int, limit: int) -> tuple[Sequence[Item], int]:
        items = await self.repository.list_page(offset=offset, limit=limit)
        total = await self.repository.count()
        return items, total

    async def create(self, data: ItemCreate) -> Item:
        await self._ensure_name_available(data.name)
        item = Item(**data.model_dump())
        self.repository.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def update(self, item_id: int, data: ItemUpdate) -> Item:
        item = await self.get(item_id)
        changes = data.model_dump(exclude_unset=True)
        new_name = changes.get("name")
        if new_name is not None and new_name != item.name:
            await self._ensure_name_available(new_name)
        for field, value in changes.items():
            setattr(item, field, value)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, item_id: int) -> None:
        item = await self.get(item_id)
        await self.repository.delete(item)
        await self.session.commit()

    async def _ensure_name_available(self, name: str) -> None:
        if await self.repository.get_by_name(name) is not None:
            raise ConflictError(f"Un item nommé '{name}' existe déjà.")
