"""Configuration de l'application, chargée depuis l'environnement (et `.env`).

Toutes les variables sont préfixées par `APP_` : `APP_DEBUG=true`, `APP_DATABASE_URL=...`.
"""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

type Environment = Literal["local", "test", "staging", "production"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

API_V1_PREFIX = "/api/v1"

# Secret utilisable uniquement en local/test : refusé en staging et production.
INSECURE_JWT_SECRET = "change-me-insecure-local-secret-key-000"  # noqa: S105


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    name: str = "Python Next IA API"
    version: str = "0.1.0"
    environment: Environment = "local"
    debug: bool = False
    log_level: LogLevel = "INFO"

    cors_origins: list[str] = Field(default_factory=list)

    database_url: str = "sqlite+aiosqlite:///./app.db"
    database_echo: bool = False

    # Authentification JWT. Générer un secret : `openssl rand -hex 32`
    jwt_secret_key: SecretStr = SecretStr(INSECURE_JWT_SECRET)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)

    @model_validator(mode="after")
    def check_jwt_secret(self) -> Self:
        if self.environment in ("staging", "production"):
            secret = self.jwt_secret_key.get_secret_value()
            if secret == INSECURE_JWT_SECRET or len(secret) < 32:
                raise ValueError("APP_JWT_SECRET_KEY doit être défini (32 caractères minimum).")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance unique (mise en cache) des paramètres."""
    return Settings()
