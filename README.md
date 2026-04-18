# Система микросервисов ресторанного меню

## Документация

| Документ | Описание |
|----------|-------------|
| [Справочник API](docs/api.md) | Все эндпоинты, схемы запросов/ответов, коды ошибок |
| [Руководство по разработке](docs/development.md) | Настройка, запуск тестов, переменные окружения, примеры рабочих процессов |
| [Каталог функций FDD](docs/fdd-features.md) | Авторитетный справочник функций с привязкой к тест-классам |
| [ERD](docs/erd.puml) | Диаграмма сущностей (PlantUML) |
| [C4 — System Context](docs/c4_context.puml) | C4 Уровень 1: акторы и системы |
| [C4 — Containers](docs/c4_container.puml) | C4 Уровень 2: сервисы, базы данных, коммуникация |
| [C4 — Components](docs/c4_component.puml) | C4 Уровень 3: внутренняя структура menu-service |

> Откройте `.puml` файлы на **[PlantText](https://www.planttext.com)** или **[PlantUML online](https://plantuml.com/plantuml)**.

## Архитектура

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Docker Compose                              │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │                web-ui  (Flask : 8888)                         │   │
│  │  • HTML-интерфейс для браузера                                │   │
│  │  • Читает JWT из сессии, проксирует запросы ко всем API       │   │
│  └──────┬──────────┬──────────────┬────────────────┬─────────────┘   │
│         │          │              │                │                  │
│  ┌──────▼──────┐ ┌─▼────────────┐ │         ┌──────▼──────────────┐  │
│  │menu-service │ │warehouse-    │ │         │  auth-service        │  │
│  │(FastAPI:8001│ │service       │ │         │  (FastAPI : 8004)    │  │
│  │• Категории  │ │(FastAPI:8002)│ │         │  • JWT авторизация   │  │
│  │• Блюда      │ │• Продукты    │ │         │  • CRUD пользователей│  │
│  │• Цены       │ │• Остатки     │ │         │  • Роли и права      │  │
│  │  DB:menu_db │ │  движения    │ │         │  DB: auth_db         │  │
│  └─────────────┘ │  DB:wh_db   │ │         └──────────────────────┘  │
│                  └─────────────┘ │                                    │
│                        ┌─────────▼──────────────┐                    │
│                        │  order-service          │                    │
│                        │  (Flask : 8003)         │                    │
│                        │  • Жизненный цикл заказов                   │
│                        │  CREATED→IN_PROGRESS    │                    │
│                        │        →READY→CLOSED    │                    │
│                        │  DB: order_db           │                    │
│                        └────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────────┘
```

## Сервисы

| Сервис               | Технология | Порт | Ответственность                                   |
|----------------------|------------|------|---------------------------------------------------|
| `menu-service`       | FastAPI    | 8001 | Меню: категории, блюда, история цен               |
| `warehouse-service`  | FastAPI    | 8002 | Склад: продукты, движения запаса, низкий остаток  |
| `order-service`      | Flask      | 8003 | Заказы: создание, взятие, готовность, закрытие    |
| `auth-service`       | FastAPI    | 8004 | Авторизация: JWT, пользователи, роли, права       |
| `web-ui`             | Flask      | 8888 | Браузерный интерфейс для всех сервисов            |

## Быстрый старт

```bash
# Скопировать переменные окружения
cp .env.example .env

# Запустить все сервисы (Docker)
make up
# или: docker compose up --build

# Проверка работоспособности
curl http://localhost:8001/health   # menu-service
curl http://localhost:8002/health   # warehouse-service
curl http://localhost:8003/health   # order-service
curl http://localhost:8004/health   # auth-service

# Веб-интерфейс
open http://localhost:8888          # Войти: admin@restaurant.local / admin123
```

## Тестирование

У каждого сервиса два набора тестов (SQLite в памяти — Docker не нужен):

### Доменные тесты (`tests/domain/`) — DDD
Проверяют бизнес-правила в полной изоляции: агрегаты, схемы Pydantic, машину состояний.
Без HTTP, без базы данных.

### Функциональные тесты (`tests/features/`) — FDD
Проверяют полные HTTP-потоки через тестовый клиент.
Фокус: жизненный цикл, обработка ошибок, фильтрация.

```bash
# Все тесты (без Docker)
make test

# По отдельному сервису
make test-menu
make test-warehouse
make test-order
make test-auth

# С отчётом о покрытии
make cov-order
```

## Сводка API

### Auth Service (FastAPI — порт 8004)
| Метод | Путь | Описание |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Получить JWT-токен |
| GET | `/api/v1/auth/me` | Информация о текущем пользователе |
| GET | `/api/v1/users` | Список пользователей |
| POST | `/api/v1/users` | Создать пользователя |
| GET | `/api/v1/users/{id}` | Получить пользователя |
| PATCH | `/api/v1/users/{id}` | Обновить пользователя |
| DELETE | `/api/v1/users/{id}` | Удалить пользователя |
| GET | `/api/v1/roles` | Список ролей |
| POST | `/api/v1/roles` | Создать роль |
| GET | `/api/v1/roles/{id}` | Получить роль с правами |
| PATCH | `/api/v1/roles/{id}` | Обновить роль |
| PUT | `/api/v1/roles/{id}/permissions` | Заменить права роли |
| DELETE | `/api/v1/roles/{id}` | Удалить роль |
| GET | `/api/v1/permissions` | Список всех прав |
| GET | `/api/v1/permissions/groups` | Права, сгруппированные по домену |

### Menu Service (FastAPI — порт 8001)
| Метод | Путь | Описание |
|--------|------|-------------|
| POST | `/api/v1/categories/` | Создать категорию |
| GET | `/api/v1/categories/` | Список категорий |
| GET | `/api/v1/categories/{id}` | Получить категорию |
| PATCH | `/api/v1/categories/{id}` | Обновить категорию |
| DELETE | `/api/v1/categories/{id}` | Удалить категорию |
| POST | `/api/v1/dishes/` | Создать блюдо |
| GET | `/api/v1/dishes/` | Список блюд (фильтр по категории, доступности) |
| GET | `/api/v1/dishes/{id}` | Получить блюдо |
| PATCH | `/api/v1/dishes/{id}` | Обновить блюдо (не цену) |
| PATCH | `/api/v1/dishes/{id}/price` | Обновить цену (записывает историю) |
| GET | `/api/v1/dishes/{id}/price-history` | История изменений цены |
| DELETE | `/api/v1/dishes/{id}` | Удалить блюдо |

### Warehouse Service (FastAPI — порт 8002)
| Метод | Путь | Описание |
|--------|------|-------------|
| POST | `/api/v1/products/` | Создать продукт |
| GET | `/api/v1/products/` | Список продуктов (фильтр по низкому запасу) |
| GET | `/api/v1/products/{id}` | Получить продукт |
| PATCH | `/api/v1/products/{id}` | Обновить продукт |
| POST | `/api/v1/products/{id}/stock` | Изменить остаток (INCOMING/OUTGOING/WRITE_OFF) |
| GET | `/api/v1/products/{id}/movements` | История движений склада |
| DELETE | `/api/v1/products/{id}` | Удалить продукт |

### Order Service (Flask — порт 8003)
| Метод | Путь | Описание |
|--------|------|-------------|
| POST | `/api/v1/orders/` | Создать заказ |
| GET | `/api/v1/orders/` | Список заказов (фильтр по статусу, столику) |
| GET | `/api/v1/orders/{id}` | Получить заказ |
| PATCH | `/api/v1/orders/{id}/status` | Универсальный переход статуса |
| POST | `/api/v1/orders/{id}/take` | CREATED → IN_PROGRESS |
| POST | `/api/v1/orders/{id}/ready` | IN_PROGRESS → READY |
| POST | `/api/v1/orders/{id}/close` | READY → CLOSED |
| POST | `/api/v1/orders/{id}/cancel` | Любой → CANCELLED |
| DELETE | `/api/v1/orders/{id}` | Удалить заказ |

## Схема базы данных

### auth_db
- `permissions` — code (PK), description, group
- `roles` — id, name, description, is_system, created_at
- `role_permissions` — role_id, permission_code (составной PK)
- `users` — id, email, full_name, hashed_password, role_id, is_active, timestamps

### menu_db
- `categories` — id, name, description, is_active, timestamps
- `dishes` — id, category_id, name, description, price, is_available, image_url, timestamps
- `price_history` — id, dish_id, old_price, new_price, changed_at

### warehouse_db
- `products` — id, name, unit, current_stock, min_stock_level, cost_price, timestamps
- `stock_movements` — id, product_id, quantity, movement_type (INCOMING/OUTGOING/WRITE_OFF), reason, order_id, created_at

### order_db
- `orders` — id, table_number, customer_name, status, notes, total_amount, taken_at, closed_at, timestamps
- `order_items` — id, order_id, dish_id, dish_name (снимок), quantity, price_at_order (снимок), notes
