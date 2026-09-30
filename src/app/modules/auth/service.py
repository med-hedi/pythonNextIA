"""Authentification : vérification des identifiants et des jetons."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    verify_and_update_password,
    verify_password,
)
from app.modules.auth.schemas import Token
from app.modules.users.models import User
from app.modules.users.service import UserService


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.users = UserService(session)

    async def login(self, email: str, password: str) -> Token:
        user = await self.authenticate(email, password)
        access = create_access_token(str(user.id), self.settings)
        return Token(access_token=access.token, expires_in=access.expires_in)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None:
            # Même coût de calcul que pour un vrai compte : pas d'énumération des emails.
            verify_password(password, DUMMY_PASSWORD_HASH)
            raise UnauthorizedError("Email ou mot de passe incorrect.")

        is_valid, updated_hash = verify_and_update_password(password, user.hashed_password)
        if not is_valid:
            raise UnauthorizedError("Email ou mot de passe incorrect.")
        if not user.is_active:
            raise ForbiddenError("Ce compte est désactivé.")

        if updated_hash is not None:
            # Paramètres de hachage devenus obsolètes : on met à niveau de façon transparente.
            user.hashed_password = updated_hash
            await self.session.commit()
        return user

    async def get_user_from_token(self, token: str) -> User:
        try:
            subject = decode_access_token(token, self.settings)
        except InvalidTokenError as exc:
            raise UnauthorizedError("Jeton invalide ou expiré.") from exc

        user = await self.users.get(int(subject)) if subject.isdigit() else None
        if user is None or not user.is_active:
            raise UnauthorizedError("Jeton invalide ou expiré.")
        return user
