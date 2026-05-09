# Система микросервисов ресторанного меню

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

| Сервис              | Технология | Порт | Ответственность                                  |
|---------------------|------------|------|--------------------------------------------------|
| `menu-service`      | FastAPI    | 8001 | Меню: категории, блюда, история цен              |
| `warehouse-service` | FastAPI    | 8002 | Склад: продукты, движения запаса, низкий остаток |
| `order-service`     | Flask      | 8003 | Заказы: создание, взятие, готовность, закрытие   |
| `auth-service`      | FastAPI    | 8004 | Авторизация: JWT, пользователи, роли, права      |
| `web-ui`            | Flask      | 8888 | Браузерный интерфейс для всех сервисов           |

---

## Запуск через Docker

Самый простой способ. Требуется только Docker Desktop.

```bash
# 1. Скопировать конфигурацию окружения
copy .env.example .env

# 2. Собрать и запустить все сервисы
docker compose up -d --build
```

Все базы данных создаются автоматически, миграции применяются при старте.

**Проверить работоспособность:**

```
http://localhost:8888   — веб-интерфейс  (admin@restaurant.local / admin123)
http://localhost:8001/docs   — menu-service Swagger UI
http://localhost:8002/docs   — warehouse-service Swagger UI
http://localhost:8004/docs   — auth-service Swagger UI
```

**Полезные команды:**

```bash
docker compose logs -f          # логи всех сервисов
docker compose logs -f menu-service   # логи одного сервиса
docker compose down             # остановить и удалить контейнеры
docker compose down -v          # также удалить тома с базами данных
```

---

## Запуск тестов через Docker

Тесты используют SQLite в памяти — базы данных PostgreSQL **не нужны**.
Достаточно собрать образ сервиса и запустить в нём pytest.

```bash
# menu-service
docker compose run --rm --no-deps menu-service pytest

# warehouse-service
docker compose run --rm --no-deps warehouse-service pytest

# order-service
docker compose run --rm --no-deps order-service pytest

# auth-service
docker compose run --rm --no-deps auth-service pytest
```

С отчётом о покрытии:

```bash
docker compose run --rm --no-deps menu-service pytest --cov=app --cov-report=term-missing
```

Только один тип тестов:

```bash
docker compose run --rm --no-deps menu-service pytest tests/domain/    # DDD
docker compose run --rm --no-deps menu-service pytest tests/features/  # FDD
```

> Флаг `--no-deps` запускает контейнер сервиса без зависимых контейнеров (БД не нужны).  
> Если образы ещё не собраны, добавьте `--build`: `docker compose run --build --rm --no-deps ...`

---

## Запуск тестов на Windows (консоль)

Тесты работают полностью локально — PostgreSQL и Docker **не нужны**.  
Требуется: Python 3.12, установленный и доступный в PATH.

Принцип одинаков для всех четырёх сервисов. Ниже показан полный пример для каждого.

### menu-service

```powershell
cd services\menu-service

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

pytest                          # все тесты
pytest tests/domain/            # только доменные (DDD)
pytest tests/features/          # только функциональные (FDD)
pytest --cov=app --cov-report=term-missing   # с покрытием
```

### warehouse-service

```powershell
cd services\warehouse-service

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

pytest
```

### order-service

```powershell
cd services\order-service

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

pytest
```

### auth-service

```powershell
cd services\auth-service

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

pytest
```

> **Повторный запуск:** виртуальное окружение создаётся один раз.  
> При следующем открытии консоли достаточно `.venv\Scripts\activate` из папки сервиса.

---

## Запуск сервисов на Windows (консоль)

Этот способ подходит для разработки одного сервиса без пересборки Docker-образа.  
Базы данных при этом удобнее всего поднять через Docker.

### Шаг 1 — Запустить базы данных

```bash
docker compose up -d menu-db warehouse-db order-db auth-db
```

Подождите несколько секунд, пока PostgreSQL инициализируется.

### Шаг 2 — Настроить переменные окружения

```powershell
copy .env.example .env
```

Значения по умолчанию в `.env` указывают на `localhost` с портами 5432–5435 — это именно то, что запустили на шаге 1.

### Шаг 3 — Запустить нужный сервис

Откройте отдельную консоль для каждого сервиса.

#### menu-service (порт 8001)

```powershell
cd services\menu-service

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Применить миграции
alembic upgrade head

# Запустить
uvicorn app.main:app --reload --port 8001
```

#### warehouse-service (порт 8002)

```powershell
cd services\warehouse-service

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

alembic upgrade head

$env:MENU_SERVICE_URL = "http://localhost:8001"
uvicorn app.main:app --reload --port 8002
```

#### order-service (порт 8003)

```powershell
cd services\order-service

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Применить миграции (Flask-Migrate)
$env:FLASK_APP = "app.main:create_app"
$env:DATABASE_URL = "postgresql://order_user:order_password@localhost:5434/order_db"
flask db upgrade

# Запустить
$env:MENU_SERVICE_URL = "http://localhost:8001"
$env:WAREHOUSE_SERVICE_URL = "http://localhost:8002"
flask run --port 8003
```

#### auth-service (порт 8004)

```powershell
cd services\auth-service

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Схема создаётся автоматически при первом старте
uvicorn app.main:app --reload --port 8004
```

#### web-ui (порт 8888)

```powershell
cd services\web-ui

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

$env:MENU_SERVICE_URL      = "http://localhost:8001"
$env:WAREHOUSE_SERVICE_URL = "http://localhost:8002"
$env:ORDER_SERVICE_URL     = "http://localhost:8003"
$env:AUTH_SERVICE_URL      = "http://localhost:8004"
$env:SECRET_KEY            = "dev-secret"
$env:JWT_SECRET            = "change-me-in-production-use-long-random-string"
$env:FLASK_APP             = "app.main:create_app"

flask run --port 8888
```

> Запускайте сервисы в порядке: сначала **menu** и **warehouse**, затем **order**, затем **auth**, последним — **web-ui**.

---

## Документация

| Документ | Описание |
|----------|----------|
| [Справочник API](docs/api.md) | Все эндпоинты, схемы запросов/ответов, коды ошибок |
| [Руководство по разработке](docs/development.md) | Переменные окружения, структура проекта, примеры curl |
| [Каталог функций FDD](docs/fdd-features.md) | Справочник функций с привязкой к тест-классам |
| [ERD](docs/erd.puml) | Диаграмма сущностей (PlantUML) |
| [C4 — System Context](docs/c4_context.puml) | C4 Уровень 1: акторы и системы |
| [C4 — Containers](docs/c4_container.puml) | C4 Уровень 2: сервисы, БД, коммуникация |
| [C4 — Components](docs/c4_component.puml) | C4 Уровень 3: внутренняя структура menu-service |

> `.puml` файлы открываются на **[PlantText](https://www.planttext.com)** или **[PlantUML online](https://plantuml.com/plantuml)**.

---

## Схема баз данных

### menu_db
- `categories` — id, name, description, is_active, timestamps
- `dishes` — id, category_id, name, description, price, is_available, image_url, timestamps
- `dish_ingredients` — id, dish_id, product_id, product_name, quantity, unit
- `price_history` — id, dish_id, old_price, new_price, changed_at

### warehouse_db
- `products` — id, name, unit, current_stock, min_stock_level, cost_price, timestamps
- `stock_movements` — id, product_id, quantity, movement_type (INCOMING/OUTGOING/WRITE_OFF), reason, order_id, created_at

### order_db
- `orders` — id, table_number, customer_name, status, notes, total_amount, taken_at, closed_at, timestamps
- `order_items` — id, order_id, dish_id, dish_name (снимок), quantity, price_at_order (снимок), notes
- `order_ingredients` — id, order_id, product_id, product_name, unit, quantity (агрегировано)

### auth_db
- `permissions` — code (PK), description, group
- `roles` — id, name, description, is_system, timestamps
- `role_permissions` — role_id, permission_code (составной PK)
- `users` — id, email, full_name, hashed_password, role_id, is_active, timestamps
