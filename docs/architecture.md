# Architecture Decision Record (ADR)

## ADR-001 — Microservice decomposition

**Status:** Accepted  
**Date:** 2026-04-13

### Context
A restaurant management system needs to handle four distinct bounded contexts:
authentication & access control, menu composition, warehouse inventory, and order
processing. These domains evolve at different rates, have different scalability
needs, and are owned by different roles.

### Decision
Split the system into four independent backend microservices plus one frontend
service, each with its own PostgreSQL database and deployment unit.

| Service | Framework | Port | Rationale |
|---------|-----------|------|-----------|
| `auth-service` | FastAPI | 8004 | Async JWT issuance; RBAC with fine-grained permissions |
| `menu-service` | FastAPI | 8001 | Heavy schema validation (Pydantic), async read-heavy workload |
| `warehouse-service` | FastAPI | 8002 | Same pattern as menu; async bulk queries for stock reports |
| `order-service` | Flask | 8003 | Synchronous; simpler lifecycle state machine; demonstrates polyglot approach |
| `web-ui` | Flask | 8888 | Server-rendered HTML; proxies API calls on behalf of the browser |

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

Both suites use pytest with `asyncio_mode = "auto"` (FastAPI services) or standard
sync (Flask services). Coverage reported on the `app/` package.

---

## ADR-005 — Centralized RBAC in auth-service

**Status:** Accepted

### Context
The system has multiple roles (admin, waiter, cook, warehouse manager, etc.) each
requiring access to different subsets of functionality across services. Scattering
authorization logic across services would make it impossible to audit or change
consistently.

### Decision
All identity and access management lives in `auth-service`:
- **Permissions** are defined as static codes in code (`permissions.py`) and
  seeded into the database on startup.
- **Roles** are dynamic entities created via API, each with an arbitrary set of
  permission codes.
- **Users** carry a single role. JWT tokens embed the full set of permission codes
  at issuance time.
- Other services validate the JWT and inspect permission claims locally — they do
  **not** call auth-service on every request.

### Consequences
- (+) Single source of truth for access control
- (+) No per-request network hop for authorization
- (-) Token permissions are stale until re-login if roles change mid-session
- Mitigation: `ACCESS_TOKEN_EXPIRE_MINUTES` defaults to 480 (8 h); short enough
  for a restaurant shift cycle

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
web-ui  ──POST /api/v1/auth/login──────────────►  auth-service
        ◄── {access_token} ──────────────────────

web-ui  ──GET /api/v1/* (Authorization: Bearer)►  menu-service / warehouse-service
                                               ►  order-service / auth-service

order-service  ──GET /api/v1/dishes/{dish_id}──►  menu-service
               ◄── 200 {name, price, is_available}

order-service  ──POST /api/v1/products/consume─►  warehouse-service
               (fire-and-forget, after order commit)
```

All inter-service calls use `httpx` with a **5-second timeout**. A `503 Service
Unavailable` is returned to the caller if `menu-service` is unreachable during
order creation. Warehouse failures are silently logged.

JWT tokens issued by `auth-service` are validated locally by `web-ui` using the
shared `JWT_SECRET` — no round-trip to auth-service on each page load.
