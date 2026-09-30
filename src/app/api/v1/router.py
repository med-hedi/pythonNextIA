"""Agrégation des routeurs de la version 1 de l'API."""

from fastapi import APIRouter

from app.core.config import API_V1_PREFIX
from app.modules.auth.router import router as auth_router
from app.modules.items.router import router as items_router
from app.modules.users.router import router as users_router

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(items_router)
