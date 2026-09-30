.DEFAULT_GOAL := help
.PHONY: help install dev test cov lint format typecheck check migrate migration docker-up docker-down clean

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Installe les dépendances et les hooks git
	uv sync
	uv run pre-commit install

dev: ## Lance le serveur de développement (rechargement auto)
	uv run uvicorn app.main:create_app --factory --reload

test: ## Lance les tests
	uv run pytest

cov: ## Lance les tests avec rapport de couverture
	uv run pytest --cov --cov-report=term-missing --cov-report=html

lint: ## Vérifie le style et les erreurs (Ruff)
	uv run ruff check .
	uv run ruff format --check .

format: ## Formate et corrige automatiquement le code
	uv run ruff check --fix .
	uv run ruff format .

typecheck: ## Vérifie les types (mypy strict)
	uv run mypy

check: lint typecheck cov ## Tout vérifier (comme la CI)

migrate: ## Applique les migrations
	uv run alembic upgrade head

migration: ## Crée une migration : make migration m="add users table"
	uv run alembic revision --autogenerate -m "$(m)"

docker-up: ## Démarre l'API + PostgreSQL avec Docker
	docker compose up --build -d

docker-down: ## Arrête les conteneurs
	docker compose down

clean: ## Supprime les caches
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
