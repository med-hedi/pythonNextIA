"""Agrégation des routeurs de la version 1 de l'API."""

from fastapi import APIRouter

from app.modules.items.router import router as items_router

api_router = APIRouter()
api_router.include_router(items_router)
