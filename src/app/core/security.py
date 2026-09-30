"""Primitives de sécurité : hachage des mots de passe et jetons JWT.

Ce module ne connaît ni la base de données ni HTTP : il est testable isolément.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings

# Argon2id : l'algorithme recommandé par l'OWASP pour les mots de passe.
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def verify_and_update_password(password: str, hashed: str) -> tuple[bool, str | None]:
    """Vérifie le mot de passe et, si le hash est obsolète, en retourne un nouveau."""
    return password_hash.verify_and_update(password, hashed)


# Hash factice : permet de vérifier un mot de passe même quand l'utilisateur
# n'existe pas, pour que le temps de réponse ne révèle pas les emails inscrits.
DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-attacks")


class InvalidTokenError(Exception):
    """Jeton illisible, mal signé, expiré ou de mauvais type."""


@dataclass(frozen=True, slots=True)
class AccessToken:
    token: str
    expires_in: int  # secondes


def create_access_token(subject: str, settings: Settings) -> AccessToken:
    now = datetime.now(UTC)
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "type": "access", "iat": now, "exp": now + expires_delta}
    token = jwt.encode(
        payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    )
    return AccessToken(token=token, expires_in=int(expires_delta.total_seconds()))


def decode_access_token(token: str, settings: Settings) -> str:
    """Valide le jeton et retourne son sujet (l'identifiant de l'utilisateur)."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            # Liste explicite : ne jamais laisser le jeton choisir son algorithme.
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "iat", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    if payload["type"] != "access":
        raise InvalidTokenError("Type de jeton inattendu.")
    subject: str = payload["sub"]
    return subject
