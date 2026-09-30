"""Endpoints des utilisateurs."""

from fastapi import APIRouter

from app.api.deps import PaginationDep, SessionDep
from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUserDep, SuperuserDep
from app.modules.users.schemas import UserRead, UserUpdate
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", summary="Mon profil")
async def read_me(user: CurrentUserDep) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", summary="Modifier mon profil")
async def update_me(session: SessionDep, user: CurrentUserDep, data: UserUpdate) -> UserRead:
    return UserRead.model_validate(await UserService(session).update(user, data))


@router.get("", summary="Lister les utilisateurs (administrateurs)")
async def list_users(
    session: SessionDep, _admin: SuperuserDep, pagination: PaginationDep
) -> Page[UserRead]:
    users, total = await UserService(session).list_page(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page[UserRead](
        items=[UserRead.model_validate(user) for user in users],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )
