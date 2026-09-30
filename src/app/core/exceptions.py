"""Exceptions métier et leur traduction en réponses HTTP.

Les services lèvent des exceptions métier (indépendantes de HTTP) ; c'est ici,
et uniquement ici, qu'elles sont converties en codes de statut.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Classe de base de toutes les erreurs métier de l'application."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    headers: dict[str, str] | None = None

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class UnauthorizedError(AppError):
    """Identité inconnue ou non prouvée (token absent, invalide, expiré…)."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"
    # Requis par la RFC 6750 pour indiquer au client le schéma attendu.
    headers = {"WWW-Authenticate": "Bearer"}  # noqa: RUF012


class ForbiddenError(AppError):
    """Identité connue, mais droits insuffisants."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)  # noqa: S101 - garanti par l'enregistrement ci-dessous
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
        headers=exc.headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
