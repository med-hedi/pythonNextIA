"""Logique métier des utilisateurs."""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate


def normalize_email(email: str) -> str:
    return email.strip().lower()


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def get(self, user_id: int) -> User | None:
        return await self.repository.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.repository.get_by_email(normalize_email(email))

    async def list_page(self, *, offset: int, limit: int) -> tuple[Sequence[User], int]:
        users = await self.repository.list_page(offset=offset, limit=limit)
        total = await self.repository.count()
        return users, total

    async def create(self, data: UserCreate, *, is_superuser: bool = False) -> User:
        email = normalize_email(data.email)
        if await self.repository.get_by_email(email) is not None:
            raise ConflictError("Un compte existe déjà avec cet email.")
        user = User(
            email=email,
            hashed_password=hash_password(data.password.get_secret_value()),
            full_name=data.full_name,
            is_superuser=is_superuser,
        )
        self.repository.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, data: UserUpdate) -> User:
        changes = data.model_dump(exclude_unset=True, exclude={"password"})
        for field, value in changes.items():
            setattr(user, field, value)
        if data.password is not None:
            user.hashed_password = hash_password(data.password.get_secret_value())
        await self.session.commit()
        await self.session.refresh(user)
        return user
