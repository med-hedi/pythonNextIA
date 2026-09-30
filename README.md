# Python Next IA

Base de projet pour construire des **API backend en Python**, avec les bonnes pratiques
et l'outillage professionnel en place dès le départ.

| Domaine            | Outil                                                            |
| ------------------ | ---------------------------------------------------------------- |
| Python & paquets   | [uv](https://docs.astral.sh/uv/) (Python 3.14, `uv.lock`)        |
| Framework web      | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn               |
| Validation         | [Pydantic v2](https://docs.pydantic.dev/) + pydantic-settings    |
| Base de données    | [SQLAlchemy 2](https://docs.sqlalchemy.org/) (async) + Alembic   |
| Qualité            | [Ruff](https://docs.astral.sh/ruff/) (lint + format), mypy strict |
| Tests              | pytest, pytest-asyncio, pytest-cov, httpx                        |
| Automatisation     | pre-commit, GitHub Actions, Makefile                             |
| Déploiement        | Docker multi-stage (non-root) + Docker Compose (PostgreSQL)      |

## Démarrage rapide

```bash
make install      # uv sync + hooks pre-commit
cp .env.example .env   # si pas déjà fait
make migrate      # crée la base SQLite locale (app.db)
make superuser email=admin@example.com   # premier administrateur
make dev          # http://localhost:8000/docs
```

`make help` liste toutes les commandes. Avant chaque push : `make check`
(exactement ce que lance la CI).

Avec PostgreSQL via Docker :

```bash
make docker-up    # API sur :8000, PostgreSQL sur :5432
# Ports occupés ? POSTGRES_PORT=5433 API_PORT=8080 docker compose up --build -d
```

## Architecture

```
src/app/
├── main.py              # create_app() : assemble l'application
├── core/                # transverse : config, logging, erreurs, pagination
├── db/                  # Base SQLAlchemy, moteur, registre des modèles
├── api/
│   ├── deps.py          # dépendances injectables (session DB, settings…)
│   ├── health.py        # /health (liveness) et /health/ready (readiness)
│   └── v1/router.py     # agrège les routeurs de la v1 (/api/v1)
├── cli.py               # commandes d'administration (create-superuser)
└── modules/             # une fonctionnalité métier = un dossier
    ├── auth/            # inscription, connexion, dépendances de protection
    ├── users/           # comptes utilisateurs
    └── items/           # exemple de ressource CRUD
        ├── models.py      # table SQL           (SQLAlchemy)
        ├── schemas.py     # contrat de l'API    (Pydantic)
        ├── repository.py  # requêtes SQL, rien d'autre
        ├── service.py     # règles métier + transactions
        └── router.py      # endpoints HTTP, fins et sans logique
tests/                   # miroir de l'API, une base SQLite neuve par test
migrations/              # migrations Alembic
```

Le flux d'une requête : **router → service → repository → base**. Chaque couche ne
connaît que celle du dessous, ce qui rend le code testable et facile à faire évoluer.

### Principes appliqués

- **Layout `src/`** : impossible d'importer le code sans l'installer, donc les tests
  testent le vrai paquet.
- **Configuration par variables d'environnement** (`APP_*`), validée et typée au démarrage ;
  aucun secret dans le code. `.env` est ignoré par git.
- **Application factory** (`create_app(settings)`) : aucun effet de bord à l'import,
  et chaque test construit son application avec sa propre configuration.
- **Schémas distincts du modèle SQL** : ce que l'API expose est découplé du stockage.
- **Erreurs métier** (`NotFoundError`, `ConflictError`) levées par les services et
  converties en HTTP à un seul endroit (`core/exceptions.py`), avec un format uniforme :
  `{"error": {"code": "...", "message": "..."}}`.
- **Migrations versionnées** : le schéma de la base n'est jamais créé « à la main ».
- **Typage strict** vérifié par mypy, et typage exploité par FastAPI pour la validation
  et la documentation OpenAPI.
- **Docs interactives désactivées en production.**

## Authentification

OAuth2 « password flow » avec jetons **JWT** (signés HS256, durée de vie courte),
mots de passe hachés en **Argon2id**.

| Endpoint                     | Accès          | Rôle                                   |
| ---------------------------- | -------------- | -------------------------------------- |
| `POST /api/v1/auth/register` | public         | Créer un compte                        |
| `POST /api/v1/auth/token`    | public         | Obtenir un jeton (formulaire `username` = email, `password`) |
| `GET/PATCH /api/v1/users/me` | connecté       | Lire / modifier son profil             |
| `GET /api/v1/users`          | administrateur | Lister les utilisateurs                |
| `GET /api/v1/items…`         | public         | Lire les items                         |
| `POST/PATCH/DELETE …/items`  | connecté       | Modifier les items                     |

Dans `/docs`, le bouton **Authorize** permet de se connecter puis de tester les routes protégées.
En ligne de commande :

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/token \
  -d "username=admin@example.com&password=..." | jq -r .access_token)
curl -H "Authorization: Bearer $TOKEN" localhost:8000/api/v1/users/me
```

Protéger un endpoint : ajouter le paramètre `user: CurrentUserDep` (ou `SuperuserDep`),
ou `dependencies=[Depends(get_current_user)]` si l'objet utilisateur n'est pas utilisé
(voir `modules/auth/dependencies.py`).

Mesures de sécurité en place : secret JWT obligatoire hors local, algorithme de signature
imposé côté serveur (un jeton `alg: none` est refusé), message d'erreur identique pour un
email inconnu ou un mauvais mot de passe (avec un temps de réponse équivalent), emails
insensibles à la casse, mot de passe jamais renvoyé ni journalisé (`SecretStr`), champs
inconnus refusés (impossible de s'auto-promouvoir administrateur), rehachage transparent
si les paramètres Argon2 évoluent.

## Ajouter une fonctionnalité (ex. `users`)

1. Créer `src/app/modules/users/` en copiant la structure de `items/`.
2. Déclarer le modèle dans `src/app/db/models.py` (pour Alembic).
3. Brancher le routeur dans `src/app/api/v1/router.py`.
4. Protéger les routes si besoin avec `CurrentUserDep` / `SuperuserDep`.
5. Générer la migration : `make migration m="create users table"` puis la relire
   et l'appliquer : `make migrate`.
6. Écrire les tests dans `tests/api/test_users.py`.

## Configuration

| Variable              | Défaut                           | Description                             |
| --------------------- | -------------------------------- | --------------------------------------- |
| `APP_ENVIRONMENT`     | `local`                          | `local`, `test`, `staging`, `production` |
| `APP_DEBUG`           | `false`                          | Mode debug FastAPI                      |
| `APP_LOG_LEVEL`       | `INFO`                           | Niveau de log                           |
| `APP_DATABASE_URL`    | `sqlite+aiosqlite:///./app.db`   | URL SQLAlchemy (async)                  |
| `APP_DATABASE_ECHO`   | `false`                          | Affiche les requêtes SQL                |
| `APP_CORS_ORIGINS`    | `[]`                             | Liste JSON des origines autorisées      |
| `APP_JWT_SECRET_KEY`  | *(secret de dev)*                | Clé de signature JWT — obligatoire en staging/prod |
| `APP_ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                 | Durée de validité d'un jeton            |

## Pistes pour la suite

Refresh tokens et révocation (déconnexion), vérification d'email et réinitialisation
de mot de passe, rate limiting sur `/auth/token` (anti brute-force), logs structurés JSON
avec identifiant de requête, rate limiting, tâches en arrière-plan, cache Redis,
observabilité (OpenTelemetry), tests sur PostgreSQL via Testcontainers.
