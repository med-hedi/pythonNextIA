"""Schémas de l'authentification (format de réponse OAuth2 standard)."""

from typing import Literal

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 - type de jeton, pas un secret
    expires_in: int  # durée de validité, en secondes
