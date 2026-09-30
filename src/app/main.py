"""Point d'entrée : fabrique de l'application FastAPI.

Lancement : `uv run uvicorn app.main:create_app --factory --reload`
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.db.session import create_engine, create_session_factory

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construit l'application. Accepter `settings` en paramètre facilite les tests."""
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    engine = create_engine(settings.database_url, echo=settings.database_echo)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        logger.info("Démarrage de %s (%s)", settings.name, settings.environment)
        yield
        await engine.dispose()
        logger.info("Arrêt de %s", settings.name)

    # La documentation interactive n'est pas exposée en production.
    docs_enabled = not settings.is_production
    app = FastAPI(
        title=settings.name,
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app
