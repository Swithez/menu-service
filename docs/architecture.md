# Architecture Decision Record (ADR)

## ADR-001 — Microservice decomposition

**Status:** Accepted  
**Date:** 2026-04-13

### Context
A restaurant management system needs to handle three distinct bounded contexts:
menu composition, warehouse inventory, and order processing. These domains
evolve at different rates, have different scalability needs, and are owned by
different roles (menu editor, warehouse manager, kitchen/waiter).

### Decision
Split the system into three independent microservices, each with its own
PostgreSQL database and deployment unit.

| Service | Framework | Rationale |
|---------|-----------|-----------|
| `menu-service` | FastAPI | Heavy schema validation (Pydantic), async read-heavy workload, OpenAPI docs for free |
| `warehouse-service` | FastAPI | Same pattern as menu; async bulk queries for stock reports |
| `order-service` | Flask | Synchronous; simpler lifecycle state machine; demonstrates polyglot approach |

### Consequences
- (+) Independent deployability and scalability per service
- (+) Technology choice per domain
- (+) Database isolation — no cross-schema queries
- (-) Inter-service HTTP latency on order creation
- (-) No distributed transactions; eventual consistency for stock deduction

---

## ADR-002 — Eventual consistency for stock deduction

**Status:** Accepted

### Context
When an order is `CLOSED`, the warehouse must deduct consumed ingredients.
A two-phase commit across two services would couple them tightly.

### Decision
`order-service` calls `warehouse-service` in a **fire-and-forget** manner
after committing the order close to its own DB. Failures are logged; a future
reconciliation job can sync discrepancies.

### Consequences
- (+) Order close is not blocked by warehouse availability
- (-) Brief inconsistency window if warehouse is down
- Mitigation: warehouse movements carry `order_id`; reconciliation is possible

---

## ADR-003 — Price and dish-name snapshots in orders

**Status:** Accepted

### Context
Dish prices change over time. An order must reflect the price at the moment
it was placed, not the current menu price.

### Decision
`order_items` stores `dish_name` and `price_at_order` as **denormalized snapshots**
copied from `menu-service` at order creation time.

### Consequences
- (+) Historical accuracy; orders never change after creation
- (+) `order-service` remains readable even if `menu-service` is down
- (-) Slight data duplication

---

## ADR-004 — Type-driven + Feature-driven testing strategy

**Status:** Accepted

### Context
Two orthogonal testing concerns exist:
1. Schema correctness (type constraints, value ranges, field validators)
2. Business feature correctness (HTTP flows, state transitions, error cases)

### Decision
Split tests into two suites per service:

- `tests/types/` — **Type-driven**: pure Pydantic schema tests, no DB, no HTTP.
  Fast, cheap, runs first. Catches type bugs at the boundary.
- `tests/features/` — **Feature-driven**: full HTTP flow via test client with
  in-memory SQLite. Organised by user-facing feature. Catches business-logic bugs.

Both suites use pytest with `asyncio_mode = "auto"` (FastAPI) or standard sync
(Flask). Coverage reported on the `app/` package.

---

## Layered Architecture (per service)

```
HTTP request
     │
     ▼
┌─────────────────────────────────────────┐
│  Router / View  (api/v1/)               │  ← Pydantic validation, HTTP semantics
│  • Deserialise request                  │
│  • Serialise response                   │
│  • Map HTTP status codes                │
└────────────────────┬────────────────────┘
                     │ calls
┌────────────────────▼────────────────────┐
│  Service  (services/)                   │  ← Business rules, domain errors
│  • Cross-entity validation              │
│  • Orchestrates multiple repositories   │
│  • Raises HTTP exceptions               │
└────────────────────┬────────────────────┘
                     │ calls
┌────────────────────▼────────────────────┐
│  Repository  (repositories/)            │  ← Data access only, no business logic
│  • SQLAlchemy queries                   │
│  • flush / refresh                      │
└────────────────────┬────────────────────┘
                     │ ORM
┌────────────────────▼────────────────────┐
│  Model  (models/)                       │  ← SQLAlchemy Mapped classes
│  • Table definition                     │
│  • Relationships                        │
└─────────────────────────────────────────┘
```

---

## Inter-service Communication

```
order-service  ──GET /api/v1/dishes/{dish_id}──►  menu-service
               ◄── 200 {name, price, is_available} ──

order-service  ──POST /api/v1/products/consume──►  warehouse-service
               (fire-and-forget, after order commit)
```

All calls use `httpx` with a **5-second timeout**. A `503 Service Unavailable`
is returned to the caller if `menu-service` is unreachable during order creation.
Warehouse failures are silently logged.
