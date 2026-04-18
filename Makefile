# ─── Menu-service project — Makefile ─────────────────────────────────────────
#
# Docker mode (full stack):
#   make up          — build and start all services
#   make down        — stop and remove containers
#   make logs        — tail logs from all services
#
# Local mode (no Docker needed — tests only, SQLite in-memory):
#   make test                    — run all service tests
#   make test-menu               — run menu-service tests
#   make test-warehouse          — run warehouse-service tests
#   make test-order              — run order-service tests
#   make test-auth               — run auth-service tests
#
# Local development (requires local PostgreSQL or use Docker for DBs only):
#   make db-up       — start only the database containers
#   make db-down     — stop database containers
#   make run-menu    — run menu-service locally (needs local Postgres or db-up)
#   make run-order   — run order-service locally
#   make run-warehouse — run warehouse-service locally

.PHONY: up down logs build \
        test test-menu test-warehouse test-order test-auth \
        db-up db-down \
        run-menu run-order run-warehouse

# ── Docker (full stack) ───────────────────────────────────────────────────────

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

# ── Tests (no Docker required — all use SQLite in-memory) ────────────────────

test: test-menu test-warehouse test-order test-auth

test-menu:
	cd services/menu-service && python -m pytest tests/ -v --tb=short

test-warehouse:
	cd services/warehouse-service && python -m pytest tests/ -v --tb=short

test-order:
	cd services/order-service && python -m pytest tests/ -v --tb=short

test-auth:
	cd services/auth-service && python -m pytest tests/ -v --tb=short

# Coverage reports

cov-menu:
	cd services/menu-service && python -m pytest tests/ --cov=app --cov-report=term-missing

cov-warehouse:
	cd services/warehouse-service && python -m pytest tests/ --cov=app --cov-report=term-missing

cov-order:
	cd services/order-service && python -m pytest tests/ --cov=app --cov-report=term-missing

# ── Local dev: databases only (Docker for DBs, services run locally) ──────────

db-up:
	docker compose up -d menu-db warehouse-db order-db auth-db

db-down:
	docker compose stop menu-db warehouse-db order-db auth-db
	docker compose rm -f menu-db warehouse-db order-db auth-db

# ── Run services locally (after db-up or with local Postgres) ────────────────
# Requires: pip install -r services/<name>/requirements.txt
# Defaults connect to localhost with the same credentials as Docker.

run-menu:
	cd services/menu-service && \
	  alembic upgrade head && \
	  uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

run-warehouse:
	cd services/warehouse-service && \
	  alembic upgrade head && \
	  uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

run-order:
	cd services/order-service && \
	  flask db upgrade && \
	  flask run --host 0.0.0.0 --port 8003 --debug

run-auth:
	cd services/auth-service && \
	  alembic upgrade head && \
	  uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
