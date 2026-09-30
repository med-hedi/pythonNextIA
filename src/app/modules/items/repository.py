"""Accès aux données : uniquement des requêtes SQL, aucune règle métier."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.items.models import Item


class ItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, item_id: int) -> Item | None:
        return await self.session.get(Item, item_id)

    async def get_by_name(self, name: str) -> Item | None:
        result = await self.session.execute(select(Item).where(Item.name == name))
        return result.scalar_one_or_none()

    async def list_page(self, *, offset: int, limit: int) -> Sequence[Item]:
        result = await self.session.execute(
            select(Item).order_by(Item.id).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Item))
        return result.scalar_one()

    def add(self, item: Item) -> None:
        self.session.add(item)

    async def delete(self, item: Item) -> None:
        await self.session.delete(item)
