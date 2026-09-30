import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize("secret", [None, "too-short"])
def test_production_requires_a_strong_jwt_secret(secret: str | None) -> None:
    overrides = {} if secret is None else {"jwt_secret_key": secret}

    with pytest.raises(ValidationError, match="APP_JWT_SECRET_KEY"):
        Settings(_env_file=None, environment="production", **overrides)  # type: ignore[arg-type]


def test_production_accepts_a_strong_jwt_secret() -> None:
    settings = Settings(
        _env_file=None,
        environment="production",
        jwt_secret_key="a" * 32,  # type: ignore[arg-type]
    )

    assert settings.is_production
