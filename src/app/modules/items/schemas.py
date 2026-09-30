"""Schémas Pydantic : contrat d'entrée/sortie de l'API (distinct du modèle SQL)."""

from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Types annotés réutilisables : les contraintes sont déclarées une seule fois.
ItemName = Annotated[str, Field(min_length=1, max_length=100, examples=["Clavier mécanique"])]
ItemDescription = Annotated[str | None, Field(max_length=1000)]


class ItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: ItemName
    description: ItemDescription = None


class ItemUpdate(BaseModel):
    """Mise à jour partielle (PATCH) : seuls les champs envoyés sont modifiés."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: ItemName | None = None
    description: ItemDescription = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def forbid_explicit_null(self) -> Self:
        # Omettre un champ = ne pas le modifier ; l'envoyer à null n'a pas de sens ici.
        for field in ("name", "is_active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' ne peut pas être null.")
        return self


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
