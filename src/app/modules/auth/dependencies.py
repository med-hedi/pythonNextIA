"""Dépendances d'authentification, à utiliser pour protéger les endpoints.

Exemples :
    async def endpoint(user: CurrentUserDep) -> ...          # utilisateur connecté
    async def endpoint(admin: SuperuserDep) -> ...           # administrateur
    @router.post(..., dependencies=[Depends(get_current_user)])  # sans utiliser l'objet
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.api.deps import SessionDep, SettingsDep
from app.core.config import API_V1_PREFIX
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.modules.auth.service import AuthService
from app.modules.users.models import User

# auto_error=False : on lève nos propres erreurs, au format uniforme de l'API.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/auth/token", auto_error=False)


def get_auth_service(session: SessionDep, settings: SettingsDep) -> AuthService:
    return AuthService(session, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    service: AuthServiceDep, token: Annotated[str | None, Depends(oauth2_scheme)]
) -> User:
    if token is None:
        raise UnauthorizedError("Authentification requise.")
    return await service.get_user_from_token(token)


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_superuser(user: CurrentUserDep) -> User:
    if not user.is_superuser:
        raise ForbiddenError("Droits administrateur requis.")
    return user


SuperuserDep = Annotated[User, Depends(get_current_superuser)]
