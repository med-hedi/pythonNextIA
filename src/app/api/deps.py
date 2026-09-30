"""Dépendances FastAPI partagées (injectées via `Depends`)."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.pagination import PaginationParams


def get_settings_from_app(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Ouvre une session de base de données par requête, fermée automatiquement."""
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield session


SettingsDep = Annotated[Settings, Depends(get_settings_from_app)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
PaginationDep = Annotated[PaginationParams, Query()]
