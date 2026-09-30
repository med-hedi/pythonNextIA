"""Schémas Pydantic des utilisateurs.

Le mot de passe est un `SecretStr` : il n'apparaît jamais en clair dans un
`repr()`, un log ou un message d'erreur de validation.
"""

from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, model_validator

Password = Annotated[SecretStr, Field(min_length=8, max_length=128)]
FullName = Annotated[str | None, Field(max_length=100)]


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    password: Password
    full_name: FullName = None


class UserUpdate(BaseModel):
    """Modification de son propre profil (PATCH /users/me)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

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
