# API Reference

Base URLs (local dev / Docker Compose):

| Service | Base URL |
|---------|----------|
| auth-service | `http://localhost:8004` |
| menu-service | `http://localhost:8001` |
| warehouse-service | `http://localhost:8002` |
| order-service | `http://localhost:8003` |

All endpoints consume and produce `application/json`.  
UUIDs use the standard `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` format.  
Decimal fields (price, stock) are returned as JSON strings with fixed precision.

---

## auth-service  `/api/v1`

### Authentication

#### `POST /auth/login`
Obtain a JWT access token.

**Request body**
```json
{
  "email": "admin@restaurant.local",
  "password": "admin123"
}
```

**Responses**

| Code | Description |
|------|-------------|
| 200 | Token issued |
| 401 | Invalid email or password |
| 403 | Account is disabled |

**Response body** (`TokenResponse`)
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 28800
}
```

---

#### `GET /auth/me`
Return info about the currently authenticated user.

Requires: `Authorization: Bearer <token>` header.

**Responses:** `200` UserResponse · `401` No / invalid token · `404` User deleted

---

### Users

All user management endpoints require the `users:users:manage` permission.

#### `GET /users`
List all users. Returns `200` array of `UserResponse`.

---

#### `POST /users`
Create a new user.

**Request body**
```json
{
  "email": "waiter@restaurant.local",
  "full_name": "Иван Петров",
  "password": "strongpass",
  "role_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "is_active": true
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | yes | valid email, unique |
| `full_name` | string | yes | 1–255 chars |
| `password` | string | yes | 6–128 chars |
| `role_id` | UUID | no | must exist |
| `is_active` | boolean | no | default `true` |

**Responses:** `201` UserResponse · `409` Email already exists · `422` Validation error

---

#### `GET /users/{user_id}`
Get a single user by ID.

**Responses:** `200` UserResponse · `404` Not found

---

#### `PATCH /users/{user_id}`
Partially update a user. At least one field required.

```json
{
  "full_name": "Новое Имя",
  "role_id": "...",
  "is_active": false,
  "password": "newpassword"
}
```

**Responses:** `200` UserResponse · `404` Not found · `409` Email conflict · `422` Validation error

---

#### `DELETE /users/{user_id}`
Delete a user.

**Responses:** `204` No content · `404` Not found

---

**`UserResponse` schema**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "waiter@restaurant.local",
  "full_name": "Иван Петров",
  "role_id": "...",
  "role_name": "waiter",
  "is_active": true,
  "created_at": "2026-04-13T10:00:00Z",
  "updated_at": "2026-04-13T10:00:00Z"
}
```

---

### Roles

All role management endpoints require the `users:roles:manage` permission.

#### `GET /roles`
List all roles. Returns `200` array of `RoleResponse`.

---

#### `POST /roles`
Create a new role.

```json
{
  "name": "waiter",
  "description": "Официант — создаёт и ведёт заказы",
  "permission_codes": ["orders:create", "orders:read:own", "orders:take"]
}
```

**Responses:** `201` RoleDetailResponse · `409` Name already exists · `422` Validation error

---

#### `GET /roles/{role_id}`
Get a role with its full permission list.

**Responses:** `200` RoleDetailResponse · `404` Not found

---

#### `PATCH /roles/{role_id}`
Update role name or description (not permissions).

```json
{ "name": "senior-waiter", "description": "Старший официант" }
```

**Responses:** `200` RoleDetailResponse · `404` Not found · `409` Name conflict · `422` Validation error

---

#### `PUT /roles/{role_id}/permissions`
Replace the full set of permissions for a role. Provide an array of permission codes.

```json
["orders:create", "orders:read:own", "orders:take", "orders:ready"]
```

**Responses:** `200` RoleDetailResponse · `404` Not found · `422` Unknown permission code

---

#### `DELETE /roles/{role_id}`
Delete a role. Fails if the role is a system role (`is_system=true`) or has assigned users.

**Responses:** `204` No content · `404` Not found · `409` Role is system or has users

---

**`RoleResponse` schema**
```json
{
  "id": "...",
  "name": "waiter",
  "description": "Официант",
  "is_system": false,
  "created_at": "2026-04-13T10:00:00Z",
  "permission_count": 3
}
```

**`RoleDetailResponse`** extends `RoleResponse` with a `permissions` array:
```json
{
  "permissions": [
    { "code": "orders:create", "description": "Создание заказов", "group": "Заказы" }
  ]
}
```

---

### Permissions

Require `users:roles:manage` permission.

#### `GET /permissions`
List all permissions defined in the system.

**Response** — `200` array of `PermissionSchema`
```json
[
  { "code": "menu:categories:read", "description": "Просмотр категорий", "group": "Меню" }
]
```

---

#### `GET /permissions/groups`
Return permissions grouped by domain.

```json
{
  "Меню": [ { "code": "menu:categories:read", ... } ],
  "Склад": [ ... ],
  "Заказы": [ ... ],
  "Пользователи": [ ... ]
}
```

---

### Full Permission List

| Code | Description | Group |
|------|-------------|-------|
| `menu:categories:read` | Просмотр категорий | Меню |
| `menu:categories:write` | Управление категориями | Меню |
| `menu:dishes:read` | Просмотр блюд | Меню |
| `menu:dishes:write` | Управление блюдами | Меню |
| `menu:dishes:price:write` | Изменение цен на блюда | Меню |
| `menu:dishes:price_history:read` | Просмотр истории цен | Меню |
| `warehouse:products:read` | Просмотр продуктов склада | Склад |
| `warehouse:products:write` | Управление продуктами склада | Склад |
| `warehouse:stock:incoming` | Приёмка товара | Склад |
| `warehouse:stock:outgoing` | Списание расхода | Склад |
| `warehouse:stock:write_off` | Ручное списание (потери) | Склад |
| `warehouse:cost_price:read` | Просмотр себестоимости | Склад |
| `orders:create` | Создание заказов | Заказы |
| `orders:read:own` | Просмотр своих заказов | Заказы |
| `orders:read:all` | Просмотр всех заказов | Заказы |
| `orders:take` | Взять заказ в работу | Заказы |
| `orders:ready` | Отметить заказ готовым | Заказы |
| `orders:close` | Закрыть заказ (принять оплату) | Заказы |
| `orders:cancel:own` | Отменить свой заказ | Заказы |
| `orders:cancel:any` | Отменить любой заказ | Заказы |
| `orders:delete` | Удалить заказ | Заказы |
| `users:read` | Просмотр пользователей | Пользователи |
| `users:users:manage` | Управление пользователями | Пользователи |
| `users:roles:manage` | Управление ролями | Пользователи |

---

## menu-service  `/api/v1`

### Categories

#### `POST /categories/`
Create a new menu category.

**Request body**
```json
{
  "name": "Hot Dishes",
  "description": "Warm main courses",
  "is_active": true
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | yes | 1–255 chars, stripped, unique |
| `description` | string | no | max 2000 chars |
| `is_active` | boolean | no | default `true` |

**Responses**

| Code | Description |
|------|-------------|
| 201 | Category created — returns `CategoryResponse` |
| 409 | Name already exists |
| 422 | Validation error |

**Response body** (`CategoryResponse`)
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Hot Dishes",
  "description": "Warm main courses",
  "is_active": true,
  "created_at": "2026-04-13T10:00:00Z",
  "updated_at": "2026-04-13T10:00:00Z"
}
```

---

#### `GET /categories/`
List all categories.

**Query parameters**

| Param | Type | Description |
|-------|------|-------------|
| `active_only` | boolean | If `true`, returns only `is_active=true` categories |

**Response** — `200` array of `CategoryResponse`

---

#### `GET /categories/{id}`
Get a single category by ID.

**Responses:** `200` CategoryResponse · `404` Not found

---

#### `PATCH /categories/{id}`
Partially update a category.

**Request body** (all fields optional)
```json
{
  "name": "New Name",
  "description": "Updated description",
  "is_active": false
}
```

**Responses:** `200` CategoryResponse · `404` Not found · `409` Name conflict · `422` Validation error

---

#### `DELETE /categories/{id}`
Delete a category. Dishes that referenced it will have `category_id = NULL`.

**Responses:** `204` No content · `404` Not found

---

### Dishes

#### `POST /dishes/`
Create a new dish.

**Request body**
```json
{
  "name": "Grilled Salmon",
  "description": "Atlantic salmon, lemon butter",
  "price": "850.00",
  "category_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "is_available": true,
  "image_url": "https://example.com/salmon.jpg",
  "calories": 280,
  "proteins": "25.00",
  "fats": "18.00",
  "carbohydrates": "0.50",
  "weight_grams": 200
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | yes | 1–255 chars |
| `price` | decimal | yes | > 0 |
| `category_id` | UUID | no | must exist in categories |
| `calories` | integer | no | 0–10 000 kcal |
| `proteins` / `fats` / `carbohydrates` | decimal | no | ≥ 0, 2 d.p. |
| `weight_grams` | integer | no | ≥ 1 |

**Responses:** `201` DishResponse · `404` Category not found · `422` Validation error

---

#### `GET /dishes/`
List dishes with optional filters.

**Query parameters**

| Param | Type | Description |
|-------|------|-------------|
| `category_id` | UUID | Filter by category |
| `available_only` | boolean | Only `is_available=true` dishes |

**Response** — `200` array of `DishResponse`

---

#### `GET /dishes/{id}`
**Responses:** `200` DishResponse · `404` Not found

---

#### `PATCH /dishes/{id}`
Update dish metadata (NOT price — use `/price` endpoint).  
At least one field must be provided.

```json
{
  "is_available": false,
  "calories": 310,
  "weight_grams": 250
}
```

**Responses:** `200` DishResponse · `404` Not found · `422` Validation error

---

#### `PATCH /dishes/{id}/price`
Update dish price. Automatically records a `PriceHistory` entry if the price changes.

```json
{ "price": "950.00" }
```

**Responses:** `200` DishResponse (with new price) · `404` Not found · `422` Validation error

> Sending the same price as the current one is idempotent — no history entry is created.

---

#### `GET /dishes/{id}/price-history`
Returns all price changes for a dish, newest first.

**Response** — `200` array of `PriceHistoryResponse`
```json
[
  {
    "id": "...",
    "dish_id": "...",
    "old_price": "850.00",
    "new_price": "950.00",
    "changed_at": "2026-04-13T12:00:00Z"
  }
]
```

---

#### `DELETE /dishes/{id}`
**Responses:** `204` No content · `404` Not found

---

## warehouse-service  `/api/v1`

### Products

#### `POST /products/`
Register a new product (ingredient) in the warehouse.

```json
{
  "name": "Salmon fillet",
  "unit": "kg",
  "calories_per_unit": 180.00,
  "min_stock_level": "5.000",
  "cost_price": "1200.00",
  "initial_stock": "20.000"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | yes | unique, 1–255 chars |
| `unit` | string | yes | one of: `kg g l ml pcs tbsp tsp` |
| `initial_stock` | decimal | no | ≥ 0, default 0 |
| `min_stock_level` | decimal | no | ≥ 0 |
| `cost_price` | decimal | no | > 0 |

If `initial_stock > 0`, an automatic `INCOMING` movement is recorded.

**Responses:** `201` ProductResponse · `409` Name conflict · `422` Validation error

---

**`ProductResponse` schema**
```json
{
  "id": "...",
  "name": "Salmon fillet",
  "unit": "kg",
  "calories_per_unit": 180.00,
  "current_stock": "20.000",
  "min_stock_level": "5.000",
  "cost_price": "1200.00",
  "is_low_stock": false,
  "created_at": "...",
  "updated_at": "..."
}
```
`is_low_stock` = `current_stock ≤ min_stock_level` (computed property, not stored).

---

#### `GET /products/`

| Param | Type | Description |
|-------|------|-------------|
| `low_stock_only` | boolean | Returns only products where `current_stock ≤ min_stock_level` |

**Response** — `200` array of `ProductResponse`

---

#### `GET /products/{id}` · `PATCH /products/{id}` · `DELETE /products/{id}`
Standard CRUD. PATCH requires at least one field.

---

#### `POST /products/{id}/stock`
Adjust stock level. Creates a `StockMovement` record.

```json
{
  "quantity": "15.500",
  "movement_type": "INCOMING",
  "reason": "Supplier delivery #4421",
  "order_id": null
}
```

| `movement_type` | Effect on stock | `reason` / `order_id` required |
|----------------|-----------------|-------------------------------|
| `INCOMING` | `+quantity` | No |
| `OUTGOING` | `-quantity` | Yes (reason OR order_id) |
| `WRITE_OFF` | `-quantity` | Yes (reason OR order_id) |

`quantity` must be non-zero. Attempting to go below 0 returns `422`.

**Responses:** `200` ProductResponse (with updated stock) · `404` Not found · `422` Insufficient stock / validation error

---

#### `GET /products/{id}/movements`
Returns all stock movements for a product, newest first.

```json
[
  {
    "id": "...",
    "product_id": "...",
    "quantity": "15.500",
    "movement_type": "INCOMING",
    "reason": "Supplier delivery #4421",
    "order_id": null,
    "created_at": "..."
  }
]
```

---

## order-service  `/api/v1`

### Order Status Machine

```
            cancel
  CREATED ─────────────────────────────► CANCELLED
     │                                       ▲
  take │    cancel                            │
     ▼ ──────────────────────────────────────┘
  IN_PROGRESS
     │    cancel ──────────────────────────────┘
  ready │
     ▼
   READY
     │
  close │
     ▼
  CLOSED  (terminal — no transitions allowed)
```

---

### Orders

#### `POST /orders/`
Create a new order. Validates each dish via `menu-service`.

```json
{
  "table_number": 5,
  "customer_name": "Ivan Petrov",
  "notes": "No onions please",
  "items": [
    { "dish_id": "...", "quantity": 2, "notes": "Well done" },
    { "dish_id": "...", "quantity": 1 }
  ]
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `items` | array | yes | min 1 item |
| `items[].dish_id` | UUID | yes | must exist and be available in menu-service |
| `items[].quantity` | integer | yes | 1–100 |
| `table_number` | integer | no | 1–999 |

**Price and dish name are snapshotted** from `menu-service` at creation time.  
`total_amount` = Σ(`price_at_order × quantity`).

**Responses:** `201` OrderResponse · `404` Dish not found · `422` Dish unavailable / validation error · `503` menu-service unavailable

---

#### `GET /orders/`

| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status (CREATED, IN_PROGRESS, READY, CLOSED, CANCELLED) |
| `table_number` | integer | Filter by table |
| `limit` | integer | Max results (default 100, max 200) |
| `offset` | integer | Pagination offset (default 0) |

---

#### `GET /orders/{id}` — `200` OrderResponse · `404` Not found

---

#### `PATCH /orders/{id}/status`
Generic status transition. Validates allowed transitions.

```json
{ "status": "IN_PROGRESS" }
```

**Responses:** `200` OrderResponse · `404` Not found · `422` Invalid transition

---

#### `POST /orders/{id}/take`
Shortcut: `CREATED → IN_PROGRESS`. Sets `taken_at`.

#### `POST /orders/{id}/ready`
Shortcut: `IN_PROGRESS → READY`.

#### `POST /orders/{id}/close`
Shortcut: `READY → CLOSED`. Sets `closed_at`. Triggers warehouse stock deduction.

#### `POST /orders/{id}/cancel`
`CREATED | IN_PROGRESS | READY → CANCELLED`. Sets `closed_at`.

#### `DELETE /orders/{id}` — `204` No content

---

**`OrderResponse` schema**
```json
{
  "id": "...",
  "table_number": 5,
  "customer_name": "Ivan Petrov",
  "status": "CREATED",
  "notes": "No onions please",
  "total_amount": "1700.00",
  "items": [
    {
      "id": "...",
      "dish_id": "...",
      "dish_name": "Grilled Salmon",
      "quantity": 2,
      "price_at_order": "850.00",
      "notes": "Well done"
    }
  ],
  "created_at": "2026-04-13T10:00:00Z",
  "updated_at": "2026-04-13T10:00:00Z",
  "taken_at": null,
  "closed_at": null
}
```

---

## Error Response Format

All services return errors in this shape:

```json
{ "detail": "Human-readable description" }
```

Validation errors (422) return the full Pydantic error list:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "price"],
      "msg": "Price must be greater than zero",
      "input": "-50"
    }
  ]
}
```
