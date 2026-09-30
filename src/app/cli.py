"""Commandes d'administration.

Usage : `uv run python -m app.cli create-superuser --email admin@example.com`
"""

import argparse
import asyncio
import getpass
import sys

from pydantic import SecretStr, ValidationError

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.db.session import create_engine, create_session_factory
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService


async def create_superuser(settings: Settings, data: UserCreate) -> User:
    engine = create_engine(settings.database_url)
    try:
        async with create_session_factory(engine)() as session:
            return await UserService(session).create(data, is_superuser=True)
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-superuser", help="Créer un administrateur")
    create.add_argument("--email", required=True)
    create.add_argument("--full-name")
    args = parser.parse_args(argv)

    # Le mot de passe est saisi sans écho, jamais passé en argument (historique du shell).
    password = getpass.getpass("Mot de passe : ")
    try:
        data = UserCreate(email=args.email, password=SecretStr(password), full_name=args.full_name)
        user = asyncio.run(create_superuser(get_settings(), data))
    except ValidationError as exc:
        sys.stderr.write(f"Données invalides :\n{exc}\n")
        return 1
    except AppError as exc:
        sys.stderr.write(f"Erreur : {exc.message}\n")
        return 1

    sys.stdout.write(f"Administrateur créé : {user.email} (id={user.id})\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
