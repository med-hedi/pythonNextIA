from httpx import AsyncClient

from app.core.config import Settings
from app.main import create_app


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["environment"] == "test"


async def test_readiness_checks_database(client: AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_docs_are_disabled_in_production(settings: Settings) -> None:
    app = create_app(settings.model_copy(update={"environment": "production"}))

    assert app.openapi_url is None
    assert app.docs_url is None


async def test_lifespan_runs_startup_and_shutdown(settings: Settings) -> None:
    app = create_app(settings)

    async with app.router.lifespan_context(app):
        pass  # ne doit lever aucune exception ; le moteur est libéré à la sortie
