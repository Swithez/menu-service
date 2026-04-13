# Restaurant Menu Microservice System

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/api.md) | All endpoints, request/response schemas, error codes |
| [Architecture & ADRs](docs/architecture.md) | Design decisions, layer diagram, inter-service communication |
| [Development Guide](docs/development.md) | Setup, running tests, environment variables, workflow examples |
| [ERD](docs/erd.puml) | Entity Relationship Diagram (PlantUML) |
| [C4 — System Context](docs/c4_context.puml) | C4 Level 1: actors and systems |
| [C4 — Containers](docs/c4_container.puml) | C4 Level 2: services, databases, communication |
| [C4 — Components](docs/c4_component.puml) | C4 Level 3: internal structure of menu-service |

> Render `.puml` files at **[PlantText](https://www.planttext.com)** or **[PlantUML online](https://plantuml.com/plantuml)**.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Docker Compose                              │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │                web-ui  (Flask : 8888)                         │   │
│  │  • Browser-facing HTML interface                              │   │
│  │  • Reads JWT from session, proxies requests to all APIs       │   │
│  └──────┬──────────┬──────────────┬────────────────┬─────────────┘   │
│         │          │              │                │                  │
│  ┌──────▼──────┐ ┌─▼────────────┐ │         ┌──────▼──────────────┐  │
│  │menu-service │ │warehouse-    │ │         │  auth-service        │  │
│  │(FastAPI:8001│ │service       │ │         │  (FastAPI : 8004)    │  │
│  │• Categories │ │(FastAPI:8002)│ │         │  • JWT login         │  │
│  │• Dishes     │ │• Products    │ │         │  • Users CRUD        │  │
│  │• Prices     │ │• Stock       │ │         │  • Roles & perms     │  │
│  │  DB:menu_db │ │  movements   │ │         │  DB: auth_db         │  │
│  └─────────────┘ │  DB:wh_db   │ │         └──────────────────────┘  │
│                  └─────────────┘ │                                    │
│                        ┌─────────▼──────────────┐                    │
│                        │  order-service          │                    │
│                        │  (Flask : 8003)         │                    │
│                        │  • Orders lifecycle     │                    │
│                        │  CREATED→IN_PROGRESS    │                    │
│                        │        →READY→CLOSED    │                    │
│                        │  DB: order_db           │                    │
│                        └────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────────┘
```

## Services

| Service              | Tech     | Port | Responsibility                           |
|----------------------|----------|------|------------------------------------------|
| `menu-service`       | FastAPI  | 8001 | Menu: categories, dishes, prices, kcal   |
| `warehouse-service`  | FastAPI  | 8002 | Stock: products, movements, low-stock    |
| `order-service`      | Flask    | 8003 | Orders: create, take, close, cancel      |
| `auth-service`       | FastAPI  | 8004 | Auth: JWT, users, roles, permissions     |
| `web-ui`             | Flask    | 8888 | Browser UI for all services              |

## Quick Start

```bash
# Copy environment variables
cp .env.example .env

# Start all services
docker compose up --build

# Health checks
curl http://localhost:8001/health   # menu-service
curl http://localhost:8002/health   # warehouse-service
curl http://localhost:8003/health   # order-service
curl http://localhost:8004/health   # auth-service

# Web interface
open http://localhost:8888          # Login with admin@restaurant.local / admin123
```

## API Summary

### Auth Service (FastAPI — port 8004)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Obtain JWT token |
| GET | `/api/v1/auth/me` | Current user info |
| GET | `/api/v1/users` | List users |
| POST | `/api/v1/users` | Create user |
| GET | `/api/v1/users/{id}` | Get user |
| PATCH | `/api/v1/users/{id}` | Update user |
| DELETE | `/api/v1/users/{id}` | Delete user |
| GET | `/api/v1/roles` | List roles |
| POST | `/api/v1/roles` | Create role |
| GET | `/api/v1/roles/{id}` | Get role with permissions |
| PATCH | `/api/v1/roles/{id}` | Update role |
| PUT | `/api/v1/roles/{id}/permissions` | Replace role permissions |
| DELETE | `/api/v1/roles/{id}` | Delete role |
| GET | `/api/v1/permissions` | List all permissions |
| GET | `/api/v1/permissions/groups` | Permissions grouped by domain |

### Menu Service (FastAPI — port 8001)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/categories/` | Create category |
| GET | `/api/v1/categories/` | List categories |
| GET | `/api/v1/categories/{id}` | Get category |
| PATCH | `/api/v1/categories/{id}` | Update category |
| DELETE | `/api/v1/categories/{id}` | Delete category |
| POST | `/api/v1/dishes/` | Create dish |
| GET | `/api/v1/dishes/` | List dishes (filter by category, availability) |
| GET | `/api/v1/dishes/{id}` | Get dish |
| PATCH | `/api/v1/dishes/{id}` | Update dish |
| PATCH | `/api/v1/dishes/{id}/price` | Update price (records history) |
| GET | `/api/v1/dishes/{id}/price-history` | Price change log |
| DELETE | `/api/v1/dishes/{id}` | Delete dish |

### Warehouse Service (FastAPI — port 8002)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/products/` | Create product |
| GET | `/api/v1/products/` | List products (filter low-stock) |
| GET | `/api/v1/products/{id}` | Get product |
| PATCH | `/api/v1/products/{id}` | Update product |
| POST | `/api/v1/products/{id}/stock` | Adjust stock (INCOMING/OUTGOING/WRITE_OFF) |
| GET | `/api/v1/products/{id}/movements` | Stock movement history |
| DELETE | `/api/v1/products/{id}` | Delete product |

### Order Service (Flask — port 8003)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/orders/` | Create order |
| GET | `/api/v1/orders/` | List orders (filter by status, table) |
| GET | `/api/v1/orders/{id}` | Get order |
| PATCH | `/api/v1/orders/{id}/status` | Generic status transition |
| POST | `/api/v1/orders/{id}/take` | CREATED → IN_PROGRESS |
| POST | `/api/v1/orders/{id}/ready` | IN_PROGRESS → READY |
| POST | `/api/v1/orders/{id}/close` | READY → CLOSED |
| POST | `/api/v1/orders/{id}/cancel` | Any → CANCELLED |
| DELETE | `/api/v1/orders/{id}` | Delete order |

## Testing

Each service has two test suites:

### Type-Driven Tests (`tests/types/`)
Validate Pydantic schemas in isolation — no DB, no HTTP.
Focus: type constraints, field validators, value ranges.

```bash
cd services/menu-service && pytest tests/types/
cd services/warehouse-service && pytest tests/types/
cd services/order-service && pytest tests/types/
cd services/auth-service && pytest tests/types/
```

### Feature-Driven Tests (`tests/features/`)
Test complete HTTP flows through the service using test clients.
Focus: business rules, lifecycle, error cases, filtering.

```bash
cd services/menu-service && pytest tests/features/
cd services/warehouse-service && pytest tests/features/
cd services/order-service && pytest tests/features/
cd services/auth-service && pytest tests/features/
```

### Run all tests with coverage
```bash
cd services/menu-service && pytest --cov=app
cd services/warehouse-service && pytest --cov=app
cd services/order-service && pytest --cov=app
cd services/auth-service && pytest --cov=app
```

## Database Schema

### auth_db
- `permissions` — code (PK), description, group (seeded from code, not editable via API)
- `roles` — id, name, description, is_system, created_at
- `role_permissions` — role_id, permission_code (composite PK)
- `users` — id, email, full_name, hashed_password, role_id, is_active, timestamps

### menu_db
- `categories` — id, name, description, is_active, timestamps
- `dishes` — id, category_id, name, price, calories, proteins, fats, carbs, weight_grams, is_available, image_url, timestamps
- `price_history` — id, dish_id, old_price, new_price, changed_at

### warehouse_db
- `products` — id, name, unit, calories_per_unit, current_stock, min_stock_level, cost_price, timestamps
- `stock_movements` — id, product_id, quantity, movement_type (INCOMING/OUTGOING/WRITE_OFF), reason, order_id, created_at

### order_db
- `orders` — id, table_number, customer_name, status, notes, total_amount, taken_at, closed_at, timestamps
- `order_items` — id, order_id, dish_id, dish_name (snapshot), quantity, price_at_order (snapshot), notes
