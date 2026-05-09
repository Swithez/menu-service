# Справочник API

Базовые URL (локальная разработка / Docker Compose):

| Сервис | Базовый URL |
|---------|----------|
| auth-service | `http://localhost:8004` |
| menu-service | `http://localhost:8001` |
| warehouse-service | `http://localhost:8002` |
| order-service | `http://localhost:8003` |

Все конечные точки используют и выдают `application/json`.  
UUID используют стандартный формат `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`.  
Десятичные поля (цена, запас) возвращаются как JSON-строки с фиксированной точностью.

---

## auth-service  `/api/v1`

### Аутентификация

#### `POST /auth/login`
Получить JWT-токен доступа.

**Тело запроса**
```json
{
  "email": "admin@restaurant.local",
  "password": "admin123"
}
```

**Ответы**

| Код | Описание |
|------|-------------|
| 200 | Токен выдан |
| 401 | Неверный email или пароль |
| 403 | Аккаунт отключён |

**Тело ответа** (`TokenResponse`)
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 28800
}
```

---

#### `GET /auth/me`
Вернуть информацию об аутентифицированном пользователе.

Требуется: заголовок `Authorization: Bearer <token>`.

**Ответы:** `200` UserResponse · `401` Нет / неверный токен · `404` Пользователь удалён

---

### Пользователи

Все конечные точки управления пользователями требуют разрешения `users:users:manage`.

#### `GET /users`
Список всех пользователей. Возвращает массив `UserResponse` с кодом `200`.

---

#### `POST /users`
Создать нового пользователя.

**Тело запроса**
```json
{
  "email": "waiter@restaurant.local",
  "full_name": "Иван Петров",
  "password": "strongpass",
  "role_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "is_active": true
}
```

| Поле | Тип | Обязательное | Ограничения |
|-------|------|----------|-------------|
| `email` | string | да | валидный email, уникальный |
| `full_name` | string | да | 1–255 символов |
| `password` | string | да | 6–128 символов |
| `role_id` | UUID | нет | должна существовать |
| `is_active` | boolean | нет | по умолчанию `true` |

**Ответы:** `201` UserResponse · `409` Email уже существует · `422` Ошибка валидации

---

#### `GET /users/{user_id}`
Получить одного пользователя по ID.

**Ответы:** `200` UserResponse · `404` Не найден

---

#### `PATCH /users/{user_id}`
Частичное обновление пользователя. Требуется хотя бы одно поле.

```json
{
  "full_name": "Новое Имя",
  "role_id": "...",
  "is_active": false,
  "password": "newpassword"
}
```

**Ответы:** `200` UserResponse · `404` Не найден · `409` Конфликт email · `422` Ошибка валидации

---

#### `DELETE /users/{user_id}`
Удалить пользователя.

**Ответы:** `204` Без содержимого · `404` Не найден

---

**Схема `UserResponse`**
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

### Роли

Все конечные точки управления ролями требуют разрешения `users:roles:manage`.

#### `GET /roles`
Список всех ролей. Возвращает массив `RoleResponse` с кодом `200`.

---

#### `POST /roles`
Создать новую роль.

```json
{
  "name": "waiter",
  "description": "Официант — создаёт и ведёт заказы",
  "permission_codes": ["orders:create", "orders:read:own", "orders:take"]
}
```

**Ответы:** `201` RoleDetailResponse · `409` Имя уже существует · `422` Ошибка валидации

---

#### `GET /roles/{role_id}`
Получить роль со своим полным списком разрешений.

**Ответы:** `200` RoleDetailResponse · `404` Не найдена

---

#### `PATCH /roles/{role_id}`
Обновить имя или описание роли (не разрешения).

```json
{ "name": "senior-waiter", "description": "Старший официант" }
```

**Ответы:** `200` RoleDetailResponse · `404` Не найдена · `409` Конфликт имени · `422` Ошибка валидации

---

#### `PUT /roles/{role_id}/permissions`
Заменить весь набор разрешений для роли. Предоставьте массив кодов разрешений.

```json
["orders:create", "orders:read:own", "orders:take", "orders:ready"]
```

**Ответы:** `200` RoleDetailResponse · `404` Не найдена · `422` Неизвестный код разрешения

---

#### `DELETE /roles/{role_id}`
Удалить роль. Ошибка, если роль системная (`is_system=true`) или имеет назначенных пользователей.

**Ответы:** `204` Без содержимого · `404` Не найдена · `409` Роль системная или имеет пользователей

---

**Схема `RoleResponse`**
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

**`RoleDetailResponse`** расширяет `RoleResponse` массивом `permissions`:
```json
{
  "permissions": [
    { "code": "orders:create", "description": "Создание заказов", "group": "Заказы" }
  ]
}
```

---

### Разрешения

Требуют разрешение `users:roles:manage`.

#### `GET /permissions`
Список всех разрешений, определённых в системе.

**Ответ** — массив `PermissionSchema` с кодом `200`
```json
[
  { "code": "menu:categories:read", "description": "Просмотр категорий", "group": "Меню" }
]
```

---

#### `GET /permissions/groups`
Вернуть разрешения, сгруппированные по домену.

```json
{
  "Меню": [ { "code": "menu:categories:read", "description": "..." } ],
  "Склад": [ "..." ],
  "Заказы": [ "..." ],
  "Пользователи": [ "..." ]
}
```

---

### Полный список разрешений

| Код | Описание | Группа |
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

### Категории

#### `POST /categories/`
Создать новую категорию меню.

**Тело запроса**
```json
{
  "name": "Горячие блюда",
  "description": "Тёплые основные блюда",
  "is_active": true
}
```

| Поле | Тип | Обязательное | Ограничения |
|-------|------|----------|-------------|
| `name` | string | да | 1–255 символов, обрезается, уникально |
| `description` | string | нет | макс 2000 символов |
| `is_active` | boolean | нет | по умолчанию `true` |

**Ответы**

| Код | Описание |
|------|-------------|
| 201 | Категория создана — возвращает `CategoryResponse` |
| 409 | Имя уже существует |
| 422 | Ошибка валидации |

**Тело ответа** (`CategoryResponse`)
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Горячие блюда",
  "description": "Тёплые основные блюда",
  "is_active": true,
  "created_at": "2026-04-13T10:00:00Z",
  "updated_at": "2026-04-13T10:00:00Z"
}
```

---

#### `GET /categories/`
Список всех категорий.

**Параметры запроса**

| Параметр | Тип | Описание |
|-------|------|-------------|
| `active_only` | boolean | Если `true`, возвращает только категории с `is_active=true` |

**Ответ** — массив `CategoryResponse` с кодом `200`

---

#### `GET /categories/{id}`
Получить одну категорию по ID.

**Ответы:** `200` CategoryResponse · `404` Не найдена

---

#### `PATCH /categories/{id}`
Частичное обновление категории.

```json
{
  "name": "Салаты",
  "is_active": false
}
```

**Ответы:** `200` CategoryResponse · `404` Не найдена · `422` Ошибка валидации

---

#### `DELETE /categories/{id}`
Удалить категорию.

**Ответы:** `204` Без содержимого · `404` Не найдена

---

### Блюда

#### `POST /dishes/`
Создать новое блюдо.

**Тело запроса**
```json
{
  "name": "Борщ",
  "description": "Традиционный суп со свёклой и капустой",
  "price": "150.00",
  "category_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "is_available": true,
  "image_url": "https://example.com/borscht.jpg"
}
```

| Поле | Тип | Обязательное | Ограничения |
|-------|------|----------|-------------|
| `name` | string | да | 1–255 символов |
| `price` | decimal | да | > 0 |
| `description` | string | нет | макс 2000 символов |
| `category_id` | UUID | нет | должна существовать в категориях |
| `is_available` | boolean | нет | по умолчанию `true` |
| `image_url` | string | нет | URL изображения |

**Ответы:** `201` DishResponse · `404` Категория не найдена · `422` Ошибка валидации

---

#### `GET /dishes/`
Список блюд с опциональными фильтрами.

**Параметры запроса**

| Параметр | Тип | Описание |
|-------|------|-------------|
| `category_id` | UUID | Фильтр по категории |
| `available_only` | boolean | Только блюда с `is_available=true` |

**Ответ** — массив `DishResponse` с кодом `200`

---

#### `GET /dishes/{id}`
**Ответы:** `200` DishResponse · `404` Не найдено

---

#### `PATCH /dishes/{id}`
Обновить метаданные блюда. **Цена через этот эндпоинт не изменяется** — используйте `/price`.  
Требуется хотя бы одно поле.

```json
{
  "is_available": false,
  "description": "Новое описание"
}
```

**Ответы:** `200` DishResponse · `404` Не найдено · `422` Ошибка валидации

---

#### `PATCH /dishes/{id}/price`
Обновить цену блюда. Автоматически записывает `PriceHistory`, если цена изменилась.

```json
{ "price": "180.00" }
```

**Ответы:** `200` DishResponse (с новой ценой) · `404` Не найдено · `422` Ошибка валидации

> Отправка той же цены идемпотентна — запись истории не создаётся.

---

#### `GET /dishes/{id}/price-history`
Вернуть все изменения цены для блюда, самые новые первыми.

**Ответ** — массив `PriceHistoryResponse` с кодом `200`
```json
[
  {
    "id": "...",
    "dish_id": "...",
    "old_price": "150.00",
    "new_price": "180.00",
    "changed_at": "2026-04-13T12:00:00Z"
  }
]
```

---

#### `DELETE /dishes/{id}`
**Ответы:** `204` Без содержимого · `404` Не найдено

---

### Состав блюд (ингредиенты)

#### `GET /dishes/{id}/ingredients`
Получить список ингредиентов (рецепт) блюда.

**Ответы:** `200` массив `DishIngredientResponse` · `404` Блюдо не найдено

> Те же данные включаются в поле `ingredients` при `GET /dishes/{id}`.

---

#### `POST /dishes/{id}/ingredients`
Добавить ингредиент в состав блюда.

```json
{
  "product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "product_name": "Куриное филе",
  "quantity": "0.300",
  "unit": "kg"
}
```

| Поле | Тип | Обязательное | Ограничения |
|-------|------|----------|-------------|
| `product_id` | UUID | да | ID продукта из warehouse-service |
| `product_name` | string | да | 1–255 символов (снимок имени) |
| `quantity` | decimal | да | > 0 |
| `unit` | string | да | 1–50 символов |

**Ответы:** `201` DishIngredientResponse · `404` Блюдо не найдено · `422` Ошибка валидации

---

#### `DELETE /dishes/{id}/ingredients/{ingredient_id}`
Удалить ингредиент из состава блюда.

**Ответы:** `204` Без содержимого · `404` Не найдено

---

**Схема `DishIngredientResponse`**
```json
{
  "id": "...",
  "dish_id": "...",
  "product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "product_name": "Куриное филе",
  "quantity": "0.300",
  "unit": "kg"
}
```

---

**Схема `DishResponse`**
```json
{
  "id": "...",
  "name": "Борщ",
  "description": "Традиционный суп",
  "price": "150.00",
  "category_id": "...",
  "is_available": true,
  "image_url": null,
  "created_at": "2026-04-13T10:00:00Z",
  "updated_at": "2026-04-13T10:00:00Z",
  "ingredients": [
    {
      "id": "...",
      "dish_id": "...",
      "product_id": "...",
      "product_name": "Свёкла",
      "quantity": "0.200",
      "unit": "kg"
    }
  ]
}
```

---

## warehouse-service  `/api/v1`

### Продукты

#### `POST /products/`
Зарегистрировать новый продукт (ингредиент) на складе.

```json
{
  "name": "Филе лосося",
  "unit": "kg",
  "min_stock_level": "5.000",
  "cost_price": "1200.00",
  "initial_stock": "20.000"
}
```

| Поле | Тип | Обязательное | Ограничения |
|-------|------|----------|-------------|
| `name` | string | да | уникально, 1–255 символов |
| `unit` | string | да | одно из: `kg g l ml pcs tbsp tsp` |
| `initial_stock` | decimal | нет | ≥ 0, по умолчанию 0 |
| `min_stock_level` | decimal | нет | ≥ 0 |
| `cost_price` | decimal | нет | > 0 |

Если `initial_stock > 0`, автоматически записывается движение типа `INCOMING`.

**Ответы:** `201` ProductResponse · `409` Конфликт имени · `422` Ошибка валидации

---

**Схема `ProductResponse`**
```json
{
  "id": "...",
  "name": "Филе лосося",
  "unit": "kg",
  "current_stock": "20.000",
  "min_stock_level": "5.000",
  "cost_price": "1200.00",
  "is_low_stock": false,
  "created_at": "...",
  "updated_at": "..."
}
```

`is_low_stock` = `current_stock ≤ min_stock_level` (вычисляемое свойство, не сохраняется в БД).

---

#### `GET /products/`

| Параметр | Тип | Описание |
|-------|------|-------------|
| `low_stock_only` | boolean | Возвращает только продукты, где `current_stock ≤ min_stock_level` |

**Ответ** — массив `ProductResponse` с кодом `200`

---

#### `GET /products/{id}` · `PATCH /products/{id}` · `DELETE /products/{id}`
Стандартный CRUD. PATCH требует хотя бы одно поле.

---

#### `POST /products/{id}/stock`
Корректировать уровень запаса. Создаёт запись `StockMovement`.

```json
{
  "quantity": "15.500",
  "movement_type": "INCOMING",
  "reason": "Поставка поставщика №4421",
  "order_id": null
}
```

| `movement_type` | Влияние на запас | Требуется `reason` / `order_id` |
|----------------|-----------------|-------------------------------|
| `INCOMING` | `+quantity` | Нет |
| `OUTGOING` | `-quantity` | Да (reason ИЛИ order_id) |
| `WRITE_OFF` | `-quantity` | Да (reason ИЛИ order_id) |

`quantity` должно быть ненулевым. Попытка опуститься ниже 0 возвращает `422`.

**Ответы:** `200` ProductResponse (с обновлённым запасом) · `404` Не найдено · `422` Недостаточно запаса / ошибка валидации

---

#### `GET /products/{id}/movements`
Вернуть все движения запаса для продукта, самые новые первыми.

```json
[
  {
    "id": "...",
    "product_id": "...",
    "quantity": "15.500",
    "movement_type": "INCOMING",
    "reason": "Поставка поставщика №4421",
    "order_id": null,
    "created_at": "..."
  }
]
```

---

## order-service  `/api/v1`

### Машина состояний заказа

```
            отмена
  CREATED ─────────────────────────────► CANCELLED
     │                                       ▲
  взять │    отмена                           │
     ▼ ──────────────────────────────────────┘
  IN_PROGRESS
     │    отмена ──────────────────────────────┘
  готово │
     ▼
   READY
     │
  закрыть │
     ▼
  CLOSED  (терминальное — переходы не допускаются)
```

---

### Заказы

#### `POST /orders/`
Создать новый заказ. Проверяет каждое блюдо через `menu-service`.

```json
{
  "table_number": 5,
  "customer_name": "Иван Петров",
  "notes": "Без лука, пожалуйста",
  "items": [
    { "dish_id": "...", "quantity": 2, "notes": "Хорошо прожаренный" },
    { "dish_id": "...", "quantity": 1 }
  ]
}
```

| Поле | Тип | Обязательное | Ограничения |
|-------|------|----------|-------------|
| `items` | array | да | мин 1 позиция |
| `items[].dish_id` | UUID | да | должно существовать и быть доступным в menu-service |
| `items[].quantity` | integer | да | 1–100 |
| `table_number` | integer | нет | 1–999 |

**Цена и имя блюда снимаются как снимок** из `menu-service` во время создания заказа.  
`total_amount` = Σ(`price_at_order × quantity`).

Если у блюда задан состав (ингредиенты), сервис проверяет наличие продуктов на складе с учётом
**уже существующих активных заказов** (`CREATED`, `IN_PROGRESS`). При нехватке возвращается `422`
с перечислением дефицитных позиций.

**Ответы:**

| Код | Описание |
|-----|----------|
| 201 | Заказ создан |
| 404 | Блюдо не найдено в menu-service |
| 422 | Блюдо недоступно / пустой список / недостаточно продуктов на складе |
| 503 | menu-service недоступен |

---

#### `GET /orders/`

| Параметр | Тип | Описание |
|-------|------|-------------|
| `status` | string | Фильтр по статусу (CREATED, IN_PROGRESS, READY, CLOSED, CANCELLED) |
| `table_number` | integer | Фильтр по номеру стола |
| `limit` | integer | Макс. результатов (по умолчанию 100, макс. 200) |
| `offset` | integer | Смещение для пагинации (по умолчанию 0) |

---

#### `GET /orders/{id}` — `200` OrderResponse · `404` Не найдено

---

#### `PATCH /orders/{id}/status`
Универсальный переход статуса. Проверяет допустимые переходы.

```json
{ "status": "IN_PROGRESS" }
```

**Ответы:** `200` OrderResponse · `404` Не найдено · `422` Недопустимый переход

---

#### `POST /orders/{id}/take`
Сокращение: `CREATED → IN_PROGRESS`. Устанавливает `taken_at`.

#### `POST /orders/{id}/ready`
Сокращение: `IN_PROGRESS → READY`. Запускает **списание ингредиентов** со склада
(`POST /products/{id}/stock` с `movement_type: OUTGOING`) — fire-and-forget, ошибки складского
сервиса не блокируют переход.

#### `POST /orders/{id}/close`
Сокращение: `READY → CLOSED`. Устанавливает `closed_at`.

#### `POST /orders/{id}/cancel`
`CREATED | IN_PROGRESS → CANCELLED`. Устанавливает `closed_at`.

#### `DELETE /orders/{id}` — `204` Без содержимого

---

**Схема `OrderResponse`**
```json
{
  "id": "...",
  "table_number": 5,
  "customer_name": "Иван Петров",
  "status": "CREATED",
  "notes": "Без лука, пожалуйста",
  "total_amount": "300.00",
  "items": [
    {
      "id": "...",
      "dish_id": "...",
      "dish_name": "Борщ",
      "quantity": 2,
      "price_at_order": "150.00",
      "notes": null
    }
  ],
  "created_at": "2026-04-13T10:00:00Z",
  "updated_at": "2026-04-13T10:00:00Z",
  "taken_at": null,
  "closed_at": null
}
```

---

## Формат ответа об ошибке

Все сервисы возвращают ошибки в этом формате:

```json
{ "detail": "Описание ошибки" }
```

Ошибки валидации (422) возвращают полный список ошибок Pydantic:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "price"],
      "msg": "Цена должна быть больше нуля",
      "input": "-50"
    }
  ]
}
```
