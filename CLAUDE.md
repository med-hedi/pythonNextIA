# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Base d'API backend FastAPI (Python 3.14, gérée par **uv**), servant aussi de support
d'apprentissage : le code doit rester exemplaire et pédagogique. **Tout est en français** :
docstrings, commentaires, messages d'erreur de l'API, README, messages de la CLI.

## Commandes

```bash
make install                 # uv sync + hooks pre-commit
make dev                     # uvicorn app.main:create_app --factory --reload
make check                   # lint + typecheck + tests avec couverture (= la CI)
make format                  # ruff check --fix + ruff format
make migrate                 # alembic upgrade head
make migration m="message"   # alembic revision --autogenerate (relire le fichier généré !)
make superuser email=a@b.c   # python -m app.cli create-superuser

uv run pytest tests/api/test_auth.py                       # un fichier
uv run pytest tests/api/test_auth.py::test_register        # un test
uv run pytest -k "login and not inactive"                  # par motif
```

- La couverture minimale est de 90 % (`fail_under`), vérifiée par `make check` et la CI.
- mypy est en mode `strict` avec le plugin pydantic, sur `src` **et** `tests`.
- Ne jamais éditer les dépendances à la main : `uv add <pkg>` / `uv add --dev <pkg>` (le hook `uv lock --check` bloque un `uv.lock` désynchronisé).
- `docker compose up --build` lance API + PostgreSQL et applique les migrations au démarrage. Les ports 5432/5433 sont souvent déjà pris sur la machine : `POSTGRES_PORT=55432 API_PORT=58000 docker compose up --build -d`.

## Architecture

### Application factory, pas d'instance globale
Il n'existe **pas** de `app = FastAPI()` au niveau module : `create_app(settings)` dans
`src/app/main.py` construit l'application et range dans `app.state` le `settings`,
l'`engine` et la `session_factory`. Les dépendances (`api/deps.py`) les lisent depuis
`request.app.state`. C'est ce qui permet à chaque test de créer une application isolée.

### Modules fonctionnels en couches
Chaque fonctionnalité vit dans `src/app/modules/<nom>/` avec
`models.py` (SQLAlchemy) → `repository.py` (requêtes uniquement) → `service.py`
(règles métier) → `router.py` (HTTP uniquement) et `schemas.py` (Pydantic, distinct du modèle).
`items` est le module de référence à copier.

Conventions non évidentes :
- **Les services gèrent les transactions** (`await session.commit()` explicite). Ne pas
  committer dans la dépendance `get_session` : le code de sortie d'une dépendance `yield`
  s'exécute après l'envoi de la réponse.
- **Les services lèvent des exceptions métier** (`NotFoundError`, `ConflictError`,
  `UnauthorizedError`, `ForbiddenError` de `core/exceptions.py`), jamais `HTTPException`.
  Un gestionnaire unique les convertit au format `{"error": {"code", "message"}}`.
- Les routeurs retournent des schémas explicites (`ItemRead.model_validate(obj)`) plutôt
  que des objets ORM, et les listes utilisent `Page[T]` + `PaginationDep` (`core/pagination.py`).
- Schémas d'entrée : `extra="forbid"` (empêche par ex. `is_superuser` dans un PATCH).
  PATCH = `model_dump(exclude_unset=True)` + un `model_validator` qui refuse un `null`
  explicite sur les colonnes non nullables.

### Brancher un nouveau module
1. Importer le modèle dans `src/app/db/models.py` (sinon Alembic ne le voit pas).
2. Inclure le routeur dans `src/app/api/v1/router.py` (préfixe `API_V1_PREFIX`, constante
   dans `core/config.py` car l'URL du jeton OAuth2 en dépend).
3. Générer la migration. `tests/test_migrations.py` échoue si modèles et migrations divergent.

### Authentification
OAuth2 password flow + JWT. `core/security.py` (Argon2id via pwdlib, PyJWT) ne dépend ni
de la base ni de HTTP. `modules/auth/dependencies.py` fournit `CurrentUserDep`,
`SuperuserDep` et `get_current_user` (pour `dependencies=[Depends(...)]`).
`OAuth2PasswordBearer` est en `auto_error=False` afin que les 401 gardent le format d'erreur
de l'API. Les emails sont normalisés en minuscules dans `UserService`. Le secret JWT par défaut
n'est accepté qu'en `local`/`test` (validateur dans `Settings`).

### Configuration
`pydantic-settings`, variables préfixées `APP_`, fichier `.env`. `get_settings()` est
mis en cache (`lru_cache`) : appeler `get_settings.cache_clear()` après avoir modifié
l'environnement (voir `tests/test_migrations.py`). `migrations/env.py` lit l'URL de la base
depuis ces settings, pas depuis `alembic.ini`.

## Tests

- `pytest-asyncio` en mode `auto` : les tests `async def` n'ont pas besoin de marqueur.
- Chaque test a sa propre base SQLite (dans `tmp_path`) créée via `Base.metadata.create_all`,
  pas via les migrations. Les settings de test passent `_env_file=None` pour ignorer le `.env` local.
- Fixtures de `tests/conftest.py` : `client` (anonyme), `auth_client` (utilisateur `user`),
  `admin_client`, et les helpers `create_user(app, email)` / `login(client, email)`.
  Pour manipuler la base directement dans un test : `async with app.state.session_factory() as session`.
- Le transport ASGI de httpx n'exécute pas le lifespan : il est testé via `app.router.lifespan_context`.
- Du code qui appelle `asyncio.run()` (la CLI) se teste via `asyncio.to_thread(...)`.

## Style et lint

Ruff avec un jeu de règles large (dont `S` bandit, `T20`, `DTZ`, `ASYNC`, `FAST`), ligne de
100 caractères. Conséquences pratiques : pas de `print` (utiliser `sys.stdout.write` ou
`logging`), datetimes toujours avec timezone (`datetime.now(UTC)`), et tout `# noqa` doit
porter le code de la règle et une justification. Syntaxe moderne Python 3.12+ attendue
(`type X = ...`, génériques `class Page[T]`, `X | None`).

## Git

Le remote utilise l'alias SSH `github-perso` (compte GitHub personnel `med-hedi`, défini dans
`~/.ssh/config`) : `git@github-perso:med-hedi/pythonNextIA.git`. Ne pas le remplacer par
`github.com`, qui authentifie avec le compte professionnel sans accès au dépôt.
Travailler sur des branches (`feature/...`), pas directement sur `main`.
