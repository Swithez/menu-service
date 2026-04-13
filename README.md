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
┌──────────────────────────────────────────────────────────────────┐
│                         Docker Compose                           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │          menu-service  (FastAPI : 8001)                     │ │
│  │  • Categories CRUD                                          │ │
│  │  • Dishes CRUD  (name, description, image)                  │ │
│  │  • Nutrition info  (calories, proteins, fats, carbs)        │ │
│  │  • Price management + full price history                    │ │
│  │  DB: menu_db (PostgreSQL)                                   │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               │ HTTP GET /dishes/{id}             │
│  ┌─────────────────────────────▼──────────────────────────────┐  │
│  │       warehouse-service  (FastAPI : 8002)                  │  │
│  │  • Products / ingredients CRUD                             │  │
│  │  • Stock level tracking (current_stock, min_stock_level)   │  │
│  │  • Stock movements  (INCOMING / OUTGOING / WRITE_OFF)      │  │
│  │  • Low-stock alert filter                                  │  │
│  │  DB: warehouse_db (PostgreSQL)                             │  │
│  └────────────────────────────┬───────────────────────────────┘  │
│                               │ HTTP GET /dishes/{id}             │
│                               │ HTTP POST /products/consume       │
│  ┌─────────────────────────────▼──────────────────────────────┐  │
│  │          order-service  (Flask : 8003)                     │  │
│  │  • Order CRUD                                              │  │
│  │  • Full status lifecycle:                                  │  │
│  │      CREATED → IN_PROGRESS → READY → CLOSED               │  │
│  │                           ↘ CANCELLED                      │  │
│  │  • Price & dish-name snapshots at order time               │  │
│  │  • Notifies warehouse on CLOSE (stock deduction)           │  │
│  │  DB: order_db (PostgreSQL)                                 │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Services

| Service            | Tech        | Port | Responsibility                          |
|--------------------|-------------|------|-----------------------------------------|
| `menu-service`     | FastAPI     | 8001 | Menu: categories, dishes, prices, kcal  |
| `warehouse-service`| FastAPI     | 8002 | Stock: products, movements, low-stock   |
| `order-service`    | Flask       | 8003 | Orders: create, take, close, cancel     |

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
```

## API Summary

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
```

### Feature-Driven Tests (`tests/features/`)
Test complete HTTP flows through the service using test clients.
Focus: business rules, lifecycle, error cases, filtering.

```bash
cd services/menu-service && pytest tests/features/
cd services/warehouse-service && pytest tests/features/
cd services/order-service && pytest tests/features/
```

### Run all tests with coverage
```bash
cd services/menu-service && pytest
cd services/warehouse-service && pytest
cd services/order-service && pytest
```

## Database Schema

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
