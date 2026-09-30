from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_is_hashed_and_verifiable() -> None:
    hashed = hash_password("s3cret-password")

    assert hashed != "s3cret-password"
    assert hashed.startswith("$argon2id$")
    assert verify_password("s3cret-password", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip(settings: Settings) -> None:
    access = create_access_token("42", settings)

    assert decode_access_token(access.token, settings) == "42"
    assert access.expires_in == settings.access_token_expire_minutes * 60


def test_token_signed_with_another_secret_is_rejected(settings: Settings) -> None:
    other = settings.model_copy(update={"jwt_secret_key": SecretStr("x" * 32)})
    access = create_access_token("42", other)

    with pytest.raises(InvalidTokenError):
        decode_access_token(access.token, settings)


def _encode(settings: Settings, **claims: object) -> str:
    now = datetime.now(UTC)
    payload = {"sub": "42", "type": "access", "iat": now, "exp": now + timedelta(minutes=5)}
    return jwt.encode(
        payload | claims, settings.jwt_secret_key.get_secret_value(), algorithm="HS256"
    )


@pytest.mark.parametrize(
    "claims",
    [
        {"exp": datetime.now(UTC) - timedelta(seconds=1)},  # expiré
        {"type": "refresh"},  # mauvais type
    ],
)
def test_invalid_tokens_are_rejected(settings: Settings, claims: dict[str, object]) -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token(_encode(settings, **claims), settings)


def test_unsigned_token_is_rejected(settings: Settings) -> None:
    token = jwt.encode({"sub": "42", "type": "access"}, key=None, algorithm="none")

    with pytest.raises(InvalidTokenError):
        decode_access_token(token, settings)
