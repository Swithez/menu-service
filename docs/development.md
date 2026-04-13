# Development Guide

## Prerequisites

| Tool | Version |
|------|---------|
| Docker | ≥ 24 |
| Docker Compose | ≥ 2.20 |
| Python | 3.12 |
| PostgreSQL | 16 (via Docker) |

---

## Quick Start (Docker Compose)

```bash
# 1. Clone and enter repo
git clone https://github.com/Swithez/menu-service.git
cd menu-service

# 2. Configure environment
cp .env.example .env        # edit values as needed

# 3. Start all services and databases
docker compose up --build

# 4. Verify health
curl http://localhost:8001/health   # {"status":"ok","service":"Menu Service"}
curl http://localhost:8002/health   # {"status":"ok","service":"Warehouse Service"}
curl http://localhost:8003/health   # {"status":"ok","service":"Order Service"}
curl http://localhost:8004/health   # {"status":"ok","service":"Auth Service"}

# 5. Open web interface
open http://localhost:8888          # Login: admin@restaurant.local / admin123

# 6. Interactive API docs (FastAPI services)
open http://localhost:8001/docs     # menu-service Swagger UI
open http://localhost:8002/docs     # warehouse-service Swagger UI
open http://localhost:8004/docs     # auth-service Swagger UI
```

---

## Local Development (without Docker)

### 1. Create a virtual environment per service

```bash
cd services/menu-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start local PostgreSQL databases

```bash
# One container per service DB (or use a single Postgres with multiple DBs)
docker run -d --name menu-db \
  -e POSTGRES_DB=menu_db -e POSTGRES_USER=menu_user -e POSTGRES_PASSWORD=menu_password \
  -p 5432:5432 postgres:16-alpine

docker run -d --name warehouse-db \
  -e POSTGRES_DB=warehouse_db -e POSTGRES_USER=warehouse_user -e POSTGRES_PASSWORD=warehouse_password \
  -p 5433:5432 postgres:16-alpine

docker run -d --name order-db \
  -e POSTGRES_DB=order_db -e POSTGRES_USER=order_user -e POSTGRES_PASSWORD=order_password \
  -p 5434:5432 postgres:16-alpine

docker run -d --name auth-db \
  -e POSTGRES_DB=auth_db -e POSTGRES_USER=auth_user -e POSTGRES_PASSWORD=auth_password \
  -p 5435:5432 postgres:16-alpine
```

### 3. Apply migrations

```bash
# menu-service (Alembic async)
cd services/menu-service && alembic upgrade head

# warehouse-service (Alembic async)
cd services/warehouse-service && alembic upgrade head

# order-service (Flask-Migrate)
cd services/order-service
FLASK_APP=app.main:create_app flask db upgrade

# auth-service (Alembic async — tables created automatically on startup)
# No manual migration needed; schema is auto-created via SQLAlchemy metadata
```

### 4. Run a service

```bash
# menu-service (port 8001)
cd services/menu-service
uvicorn app.main:app --reload --port 8001

# warehouse-service (port 8002)
cd services/warehouse-service
uvicorn app.main:app --reload --port 8002

# order-service (port 8003)
cd services/order-service
FLASK_APP=app.main:create_app flask run --port 8003

# auth-service (port 8004)
cd services/auth-service
uvicorn app.main:app --reload --port 8004

# web-ui (port 8888)
cd services/web-ui
FLASK_APP=app.main:create_app flask run --port 8888
```

---

## Running Tests

Tests use **SQLite in-memory** for isolation — no running Postgres needed.

```bash
# All tests for a service
cd services/menu-service && pytest

# Type-driven tests only (fast, no DB)
pytest tests/types/

# Feature-driven tests only (HTTP flows)
pytest tests/features/

# With coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

Repeat for `warehouse-service`, `order-service`, and `auth-service`.

### Test isolation strategy

| Service | DB in tests | HTTP mocks |
|---------|-------------|------------|
| menu-service | `sqlite+aiosqlite:///:memory:` | N/A |
| warehouse-service | `sqlite+aiosqlite:///:memory:` | N/A |
| order-service | `sqlite:///:memory:` | `unittest.mock.patch('httpx.get')` |
| auth-service | `sqlite+aiosqlite:///:memory:` | N/A |

---

## Project Structure

```
menu-service/              ← repository root
├── docker-compose.yml
├── .env.example
├── README.md
├── docs/
│   ├── api.md             ← API reference (all services)
│   ├── architecture.md    ← ADRs and layer diagram
│   ├── development.md     ← this file
│   ├── erd.puml           ← Entity Relationship Diagram
│   ├── c4_context.puml    ← C4 Level 1: System Context
│   ├── c4_container.puml  ← C4 Level 2: Container Diagram
│   └── c4_component.puml  ← C4 Level 3: Component (menu-service)
└── services/
    ├── auth-service/           FastAPI — JWT auth, users, roles, permissions
    │   ├── app/
    │   │   ├── api/v1/         HTTP routers (auth, users, roles, permissions)
    │   │   ├── models/         SQLAlchemy ORM models
    │   │   ├── repositories/   DB queries
    │   │   ├── schemas/        Pydantic schemas
    │   │   ├── services/       business logic (auth, users, roles)
    │   │   ├── permissions.py  central permissions registry
    │   │   ├── config.py       pydantic-settings
    │   │   ├── database.py     async engine + session factory
    │   │   └── main.py         FastAPI app factory + lifespan (auto-seed)
    │   ├── alembic/            migrations
    │   ├── tests/
    │   │   ├── types/          type-driven tests
    │   │   └── features/       feature-driven HTTP tests
    │   ├── pyproject.toml
    │   └── requirements.txt
    │
    ├── menu-service/           FastAPI — categories, dishes, prices
    │   ├── app/
    │   │   ├── api/v1/         HTTP routers
    │   │   ├── models/         SQLAlchemy ORM models
    │   │   ├── repositories/   DB queries
    │   │   ├── schemas/        Pydantic schemas
    │   │   ├── services/       business logic
    │   │   ├── config.py       pydantic-settings
    │   │   ├── database.py     async engine + session factory
    │   │   └── main.py         FastAPI app factory + lifespan
    │   ├── alembic/            migrations
    │   ├── tests/
    │   │   ├── types/          type-driven tests
    │   │   └── features/       feature-driven HTTP tests
    │   ├── pyproject.toml
    │   └── requirements.txt
    │
    ├── warehouse-service/      FastAPI — products, stock, movements
    │   └── (same layout as menu-service)
    │
    ├── order-service/          Flask — orders lifecycle
    │   ├── app/
    │   │   ├── api/v1/         Flask blueprints
    │   │   ├── models/         SQLAlchemy models
    │   │   ├── repositories/   DB queries (sync)
    │   │   ├── schemas/        Pydantic schemas
    │   │   ├── services/       business logic + httpx calls
    │   │   ├── extensions.py   db, migrate singletons
    │   │   ├── config.py
    │   │   └── main.py         Flask app factory
    │   ├── migrations/         Flask-Migrate / Alembic
    │   └── tests/
    │       ├── types/
    │       └── features/
    │
    └── web-ui/                 Flask — browser UI
        ├── app/
        │   ├── views/          Flask blueprints (auth, dashboard, menu, warehouse, orders, admin)
        │   ├── clients/        HTTP clients for each backend service
        │   ├── middleware/      JWT validation middleware
        │   ├── templates/      Jinja2 HTML templates
        │   ├── static/         CSS
        │   ├── config.py
        │   └── main.py         Flask app factory
        └── requirements.txt
```

---

## Adding a New Service

1. Copy an existing service directory as a template.
2. Create a new database section in `docker-compose.yml`.
3. Add the new service to `docker-compose.yml` with `depends_on`.
4. Register environment variables in `.env.example`.
5. Write `tests/types/` tests first (type-driven), then `tests/features/`.
6. Run `alembic revision --autogenerate -m "initial"` to generate migration.
7. Add a client in `services/web-ui/app/clients/` if the UI needs to talk to it.

---

## Type Checking

```bash
cd services/auth-service && mypy app/
cd services/menu-service && mypy app/
cd services/warehouse-service && mypy app/
cd services/order-service && mypy app/
```

---

## Environment Variables

### auth-service
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://auth_user:auth_password@localhost:5435/auth_db` | Async DSN |
| `JWT_SECRET` | `change-me-in-production-use-long-random-string` | HS256 signing key — **change in production** |
| `JWT_ALGORITHM` | `HS256` | Token signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Token TTL (8 hours) |
| `ADMIN_EMAIL` | `admin@restaurant.local` | Bootstrap admin email |
| `ADMIN_PASSWORD` | `admin123` | Bootstrap admin password — **change in production** |
| `ADMIN_FULL_NAME` | `Администратор` | Bootstrap admin display name |
| `SERVICE_PORT` | `8004` | Bind port |

### menu-service
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://menu_user:menu_password@localhost:5432/menu_db` | Async DSN |
| `SERVICE_HOST` | `0.0.0.0` | Bind host |
| `SERVICE_PORT` | `8001` | Bind port |
| `DEBUG` | `false` | SQLAlchemy echo |

### warehouse-service
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://warehouse_user:warehouse_password@localhost:5433/warehouse_db` | Async DSN |
| `MENU_SERVICE_URL` | `http://localhost:8001` | Menu service base URL |
| `SERVICE_PORT` | `8002` | Bind port |

### order-service
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://order_user:order_password@localhost:5434/order_db` | Sync DSN (psycopg2) |
| `MENU_SERVICE_URL` | `http://localhost:8001` | Used for dish validation |
| `WAREHOUSE_SERVICE_URL` | `http://localhost:8002` | Used for stock deduction |
| `SERVICE_PORT` | `8003` | Bind port |

### web-ui
| Variable | Default | Description |
|----------|---------|-------------|
| `MENU_SERVICE_URL` | `http://localhost:8001` | Menu service base URL |
| `WAREHOUSE_SERVICE_URL` | `http://localhost:8002` | Warehouse service base URL |
| `ORDER_SERVICE_URL` | `http://localhost:8003` | Order service base URL |
| `AUTH_SERVICE_URL` | `http://localhost:8004` | Auth service base URL |
| `SECRET_KEY` | `change-me-in-production` | Flask session secret — **change in production** |
| `JWT_SECRET` | `change-me-in-production-use-long-random-string` | Shared with auth-service for token validation |
| `JWT_ALGORITHM` | `HS256` | Token algorithm |

---

## Typical Workflow Example

```bash
# 1. Obtain JWT token
TOKEN=$(curl -s -X POST http://localhost:8004/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@restaurant.local","password":"admin123"}' | jq -r .access_token)

# 2. Create a category
CATEGORY_ID=$(curl -s -X POST http://localhost:8001/api/v1/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Hot Dishes"}' | jq -r .id)

# 3. Create a dish
DISH_ID=$(curl -s -X POST http://localhost:8001/api/v1/dishes/ \
  -H "Content-Type: application/json" \
  -d "{
    \"name\":\"Borscht\",\"price\":\"150.00\",
    \"category_id\":\"$CATEGORY_ID\",
    \"calories\":85,\"proteins\":\"3.5\",\"fats\":\"2.0\",\"carbohydrates\":\"12.0\",
    \"weight_grams\":300
  }" | jq -r .id)

# 4. Receive produce into warehouse
curl -s -X POST http://localhost:8002/api/v1/products/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Beetroot","unit":"kg","initial_stock":"20.000","min_stock_level":"5.000"}'

# 5. Create an order
ORDER_ID=$(curl -s -X POST http://localhost:8003/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -d "{\"table_number\":3,\"items\":[{\"dish_id\":\"$DISH_ID\",\"quantity\":2}]}" \
  | jq -r .id)

# 6. Kitchen takes the order
curl -s -X POST http://localhost:8003/api/v1/orders/$ORDER_ID/take | jq .status

# 7. Mark as ready
curl -s -X POST http://localhost:8003/api/v1/orders/$ORDER_ID/ready | jq .status

# 8. Close (triggers warehouse stock deduction)
curl -s -X POST http://localhost:8003/api/v1/orders/$ORDER_ID/close | jq .

# 9. View price history after a price change
curl -s -X PATCH http://localhost:8001/api/v1/dishes/$DISH_ID/price \
  -H "Content-Type: application/json" -d '{"price":"180.00"}'
curl -s http://localhost:8001/api/v1/dishes/$DISH_ID/price-history | jq .
```
