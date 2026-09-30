"""Sondes de santé, utilisées par Docker / Kubernetes / load balancers."""

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessionDep, SettingsDep

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Liveness : l'application répond")
async def liveness(settings: SettingsDep) -> dict[str, str]:
    return {"status": "ok", "version": settings.version, "environment": settings.environment}


@router.get("/ready", summary="Readiness : les dépendances (base de données) sont joignables")
async def readiness(session: SessionDep) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
