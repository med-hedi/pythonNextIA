"""Pagination générique réutilisable par tous les endpoints de liste."""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    offset: int = Field(default=0, ge=0, description="Nombre d'éléments à ignorer.")
    limit: int = Field(default=20, ge=1, le=100, description="Nombre maximum d'éléments.")


class Page[T](BaseModel):
    items: list[T]
    total: int
    offset: int
    limit: int
