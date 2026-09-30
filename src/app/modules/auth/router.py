"""Endpoints d'authentification : inscription et obtention d'un jeton."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessionDep
from app.modules.auth.dependencies import AuthServiceDep
from app.modules.auth.schemas import Token
from app.modules.users.schemas import UserCreate, UserRead
from app.modules.users.service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Créer un compte")
async def register(session: SessionDep, data: UserCreate) -> UserRead:
    return UserRead.model_validate(await UserService(session).create(data))


@router.post("/token", summary="Se connecter (OAuth2 password flow)")
async def login(
    service: AuthServiceDep, form: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    # La spécification OAuth2 impose le nom de champ `username` : il contient l'email.
    return await service.login(form.username, form.password)
