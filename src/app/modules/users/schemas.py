"""Schémas Pydantic des utilisateurs.

Le mot de passe est un `SecretStr` : il n'apparaît jamais en clair dans un
`repr()`, un log ou un message d'erreur de validation. Il n'est jamais rogné :
les espaces font partie du secret, et `/auth/token` le compare tel quel. C'est
pourquoi le rognage (`strip_whitespace`) est déclaré champ par champ plutôt que
via `str_strip_whitespace` dans `model_config`, qui s'appliquerait aussi à `SecretStr`.
"""

from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
    model_validator,
)

Password = Annotated[SecretStr, Field(min_length=8, max_length=128)]
Email = Annotated[EmailStr, StringConstraints(strip_whitespace=True)]
FullName = Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=100)]


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email
    password: Password
    full_name: FullName = None


class UserUpdate(BaseModel):
    """Modification de son propre profil (PATCH /users/me)."""

    model_config = ConfigDict(extra="forbid")

    full_name: FullName = None
    password: Password | None = None

    @model_validator(mode="after")
    def forbid_null_password(self) -> Self:
        if "password" in self.model_fields_set and self.password is None:
            raise ValueError("'password' ne peut pas être null.")
        return self


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
