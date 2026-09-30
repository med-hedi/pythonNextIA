"""Création du moteur SQLAlchemy asynchrone et de la fabrique de sessions."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    return create_async_engine(database_url, echo=echo, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False : les objets restent lisibles après commit
    # (nécessaire en async, où le lazy-loading implicite est interdit).
    return async_sessionmaker(engine, expire_on_commit=False)
