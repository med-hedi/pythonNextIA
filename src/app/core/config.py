"""Configuration de l'application, chargée depuis l'environnement (et `.env`).

Toutes les variables sont préfixées par `APP_` : `APP_DEBUG=true`, `APP_DATABASE_URL=...`.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

type Environment = Literal["local", "test", "staging", "production"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


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

    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=list)

    database_url: str = "sqlite+aiosqlite:///./app.db"
    database_echo: bool = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance unique (mise en cache) des paramètres."""
    return Settings()
