# Руководство по разработке

## Предварительные требования

| Инструмент | Версия |
|------|---------|
| Docker | ≥ 24 |
| Docker Compose | ≥ 2.20 |
| Python | 3.12 |
| PostgreSQL | 16 (через Docker) |

---

## Быстрый старт (Docker Compose)

```bash
# 1. Клонировать и войти в репозиторий
git clone https://github.com/Swithez/menu-service.git
cd menu-service

# 2. Настроить окружение
cp .env.example .env        # отредактировать значения если нужно

# 3. Запустить все сервисы и базы данных
make up
# или: docker compose up --build

# 4. Проверить работоспособность
curl http://localhost:8001/health   # {"status":"ok","service":"Menu Service"}
curl http://localhost:8002/health   # {"status":"ok","service":"Warehouse Service"}
curl http://localhost:8003/health   # {"status":"ok","service":"Order Service"}
curl http://localhost:8004/health   # {"status":"ok","service":"Auth Service"}

# 5. Открыть веб-интерфейс
open http://localhost:8888          # Вход: admin@restaurant.local / admin123

# 6. Интерактивная документация API (сервисы FastAPI)
open http://localhost:8001/docs     # menu-service Swagger UI
open http://localhost:8002/docs     # warehouse-service Swagger UI
open http://localhost:8004/docs     # auth-service Swagger UI
```

---

## Локальная разработка (без Docker)

### Вариант 1 — только тесты (Docker не нужен)

Все тесты используют SQLite в памяти. Запуск через Makefile:

```bash
make test            # все сервисы
make test-menu       # только menu-service
make test-warehouse  # только warehouse-service
make test-order      # только order-service
make test-auth       # только auth-service
```

### Вариант 2 — запустить сервисы локально (только базы данных в Docker)

```bash
# Запустить только БД
make db-up

# Затем запустить нужные сервисы локально
make run-menu       # порт 8001
make run-warehouse  # порт 8002
make run-order      # порт 8003
make run-auth       # порт 8004
```

### Вариант 3 — полностью вручную

#### 1. Создать виртуальное окружение для каждого сервиса

```bash
cd services/menu-service
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Запустить локальные базы данных PostgreSQL

```bash
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

#### 3. Применить миграции

```bash
# menu-service (Alembic async)
cd services/menu-service && alembic upgrade head

# warehouse-service (Alembic async)
cd services/warehouse-service && alembic upgrade head

# order-service (Flask-Migrate)
cd services/order-service
FLASK_APP=app.main:create_app flask db upgrade

# auth-service — схема создаётся автоматически при первом запуске
```

#### 4. Запустить сервис

```bash
# menu-service (порт 8001)
cd services/menu-service
uvicorn app.main:app --reload --port 8001

# warehouse-service (порт 8002)
cd services/warehouse-service
uvicorn app.main:app --reload --port 8002

# order-service (порт 8003)
cd services/order-service
FLASK_APP=app.main:create_app flask run --port 8003

# auth-service (порт 8004)
cd services/auth-service
uvicorn app.main:app --reload --port 8004
```

---

## Запуск тестов

Тесты используют **SQLite в памяти** для изоляции — запущенный Postgres не требуется.

```bash
# Все тесты одного сервиса
cd services/menu-service && pytest

# Только доменные тесты (DDD — быстрые, без HTTP и БД)
pytest tests/domain/

# Только функциональные тесты (FDD — HTTP-потоки)
pytest tests/features/

# С отчётом о покрытии
pytest --cov=app --cov-report=html
```

Повторите то же самое для `warehouse-service`, `order-service` и `auth-service`.

### Структура тестов

| Каталог | Тип | Описание |
|---------|-----|----------|
| `tests/domain/` | **DDD** | Чистая доменная логика: агрегаты, бизнес-правила, схемы Pydantic. Без HTTP, без БД. |
| `tests/features/` | **FDD** | Полные HTTP-сценарии через тестовый клиент. Фокус на пользовательских функциях. |

### Стратегия изоляции тестов

| Сервис | БД в тестах | Mock-ирование HTTP |
|---------|-------------|---------------------|
| menu-service | `sqlite+aiosqlite:///:memory:` | — |
| warehouse-service | `sqlite+aiosqlite:///:memory:` | — |
| order-service | `sqlite:///:memory:` | `unittest.mock.patch('httpx.get')` |
| auth-service | `sqlite+aiosqlite:///:memory:` | — |

---

## Структура проекта

```
menu-service/              ← корень репозитория
├── Makefile               ← команды для Docker и локальной разработки
├── docker-compose.yml
├── .env.example
├── README.md
├── docs/
│   ├── api.md             ← Справочник API (все сервисы)
│   ├── development.md     ← этот файл
│   ├── fdd-features.md    ← каталог функций FDD
│   ├── erd.puml           ← Диаграмма отношений сущностей
│   ├── c4_context.puml    ← C4 Уровень 1: Контекст системы
│   ├── c4_container.puml  ← C4 Уровень 2: Диаграмма контейнера
│   └── c4_component.puml  ← C4 Уровень 3: Компонент (menu-service)
└── services/
    ├── auth-service/           FastAPI — JWT auth, пользователи, роли, права
    │   ├── app/
    │   │   ├── api/v1/         HTTP маршруты (auth, пользователи, роли, права)
    │   │   ├── models/         SQLAlchemy ORM модели
    │   │   ├── repositories/   Запросы к БД
    │   │   ├── schemas/        Pydantic схемы
    │   │   ├── services/       Бизнес-логика
    │   │   ├── permissions.py  Реестр прав доступа
    │   │   ├── config.py       pydantic-settings
    │   │   ├── database.py     Async engine + session factory
    │   │   └── main.py         FastAPI app factory + lifespan
    │   ├── alembic/            Миграции
    │   ├── tests/
    │   │   └── features/       FDD: тесты функций HTTP
    │   ├── pyproject.toml
    │   └── requirements.txt
    │
    ├── menu-service/           FastAPI — категории, блюда, история цен
    │   ├── app/
    │   │   ├── api/v1/         HTTP маршруты
    │   │   ├── models/         SQLAlchemy ORM модели
    │   │   ├── repositories/   Запросы к БД
    │   │   ├── schemas/        Pydantic схемы
    │   │   ├── services/       Бизнес-логика
    │   │   ├── config.py       pydantic-settings
    │   │   ├── database.py     Async engine + session factory
    │   │   └── main.py         FastAPI app factory
    │   ├── alembic/            Миграции
    │   ├── tests/
    │   │   ├── domain/         DDD: доменная логика (схемы, бизнес-правила)
    │   │   └── features/       FDD: HTTP-сценарии
    │   ├── pyproject.toml
    │   └── requirements.txt
    │
    ├── warehouse-service/      FastAPI — продукты, запас, движения
    │   └── (аналогично menu-service)
    │
    ├── order-service/          Flask — жизненный цикл заказов
    │   ├── app/
    │   │   ├── api/v1/         Flask blueprints
    │   │   ├── models/         SQLAlchemy модели
    │   │   ├── repositories/   Запросы к БД (sync)
    │   │   ├── schemas/        Pydantic схемы
    │   │   ├── services/       Бизнес-логика + httpx вызовы
    │   │   ├── extensions.py   db, migrate singletons
    │   │   ├── config.py
    │   │   └── main.py         Flask app factory
    │   ├── migrations/         Flask-Migrate / Alembic
    │   ├── tests/
    │   │   ├── domain/         DDD: агрегаты, машина состояний, схемы
    │   │   └── features/       FDD: HTTP-сценарии жизненного цикла
    │   ├── pyproject.toml
    │   └── requirements.txt
    │
    └── web-ui/                 Flask — браузерный интерфейс
        ├── app/
        │   ├── views/          Flask blueprints
        │   ├── clients/        HTTP-клиенты для каждого бэкенд-сервиса
        │   ├── middleware/      Валидация JWT
        │   ├── templates/      Jinja2 HTML шаблоны
        │   ├── static/         CSS
        │   ├── config.py
        │   └── main.py         Flask app factory
        └── requirements.txt
```

---

## Makefile — доступные команды

```bash
make up              # Собрать и запустить все сервисы (Docker)
make down            # Остановить и удалить контейнеры
make logs            # Следить за логами всех сервисов
make build           # Пересобрать образы

make test            # Все тесты (SQLite, без Docker)
make test-menu       # Тесты menu-service
make test-warehouse  # Тесты warehouse-service
make test-order      # Тесты order-service
make test-auth       # Тесты auth-service

make cov-menu        # Покрытие menu-service
make cov-order       # Покрытие order-service

make db-up           # Запустить только контейнеры с БД
make db-down         # Остановить контейнеры с БД

make run-menu        # Запустить menu-service локально (порт 8001)
make run-order       # Запустить order-service локально (порт 8003)
make run-warehouse   # Запустить warehouse-service локально (порт 8002)
make run-auth        # Запустить auth-service локально (порт 8004)
```

---

## Добавление нового сервиса

1. Скопировать существующий каталог сервиса как шаблон.
2. Создать новый раздел БД в `docker-compose.yml`.
3. Добавить новый сервис в `docker-compose.yml` с `depends_on`.
4. Зарегистрировать переменные окружения в `.env.example`.
5. Написать тесты `tests/domain/` первыми (бизнес-правила), затем `tests/features/` (HTTP).
6. Запустить `alembic revision --autogenerate -m "initial"` для создания миграции.
7. Добавить клиент в `services/web-ui/app/clients/`, если UI должен обращаться к нему.
8. Добавить команды в `Makefile`.

---

## Проверка типов

```bash
cd services/auth-service && mypy app/
cd services/menu-service && mypy app/
cd services/warehouse-service && mypy app/
cd services/order-service && mypy app/
```

---

## Переменные окружения

### auth-service
| Переменная | По умолчанию | Описание |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://auth_user:auth_password@localhost:5435/auth_db` | Async DSN |
| `JWT_SECRET` | `change-me-in-production-use-long-random-string` | Ключ подписи HS256 — **изменить в production** |
| `JWT_ALGORITHM` | `HS256` | Алгоритм подписи токена |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | TTL токена (8 часов) |
| `ADMIN_EMAIL` | `admin@restaurant.local` | Email администратора при инициализации |
| `ADMIN_PASSWORD` | `admin123` | Пароль администратора — **изменить в production** |
| `ADMIN_FULL_NAME` | `Администратор` | Отображаемое имя администратора |
| `SERVICE_PORT` | `8004` | Порт привязки |

### menu-service
| Переменная | По умолчанию | Описание |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://menu_user:menu_password@localhost:5432/menu_db` | Async DSN |
| `SERVICE_HOST` | `0.0.0.0` | Хост привязки |
| `SERVICE_PORT` | `8001` | Порт привязки |
| `DEBUG` | `false` | SQLAlchemy echo |

### warehouse-service
| Переменная | По умолчанию | Описание |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://warehouse_user:warehouse_password@localhost:5433/warehouse_db` | Async DSN |
| `MENU_SERVICE_URL` | `http://localhost:8001` | Базовый URL сервиса меню |
| `SERVICE_PORT` | `8002` | Порт привязки |

### order-service
| Переменная | По умолчанию | Описание |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://order_user:order_password@localhost:5434/order_db` | Sync DSN (psycopg2) |
| `MENU_SERVICE_URL` | `http://localhost:8001` | Используется для валидации блюда при создании заказа |
| `WAREHOUSE_SERVICE_URL` | `http://localhost:8002` | Используется для списания запаса при закрытии |
| `SERVICE_PORT` | `8003` | Порт привязки |

### web-ui
| Переменная | По умолчанию | Описание |
|----------|---------|-------------|
| `MENU_SERVICE_URL` | `http://localhost:8001` | Базовый URL сервиса меню |
| `WAREHOUSE_SERVICE_URL` | `http://localhost:8002` | Базовый URL сервиса склада |
| `ORDER_SERVICE_URL` | `http://localhost:8003` | Базовый URL сервиса заказов |
| `AUTH_SERVICE_URL` | `http://localhost:8004` | Базовый URL сервиса аутентификации |
| `SECRET_KEY` | `change-me-in-production` | Секрет сессии Flask — **изменить в production** |
| `JWT_SECRET` | `change-me-in-production-use-long-random-string` | Общий с auth-service для валидации токена |
| `JWT_ALGORITHM` | `HS256` | Алгоритм токена |

---

## Пример типичного рабочего процесса

```bash
# 1. Получить JWT токен
TOKEN=$(curl -s -X POST http://localhost:8004/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@restaurant.local","password":"admin123"}' | jq -r .access_token)

# 2. Создать категорию
CATEGORY_ID=$(curl -s -X POST http://localhost:8001/api/v1/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Горячие блюда"}' | jq -r .id)

# 3. Создать блюдо
DISH_ID=$(curl -s -X POST http://localhost:8001/api/v1/dishes/ \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Борщ\",\"price\":\"150.00\",\"category_id\":\"$CATEGORY_ID\"}" \
  | jq -r .id)

# 4. Добавить продукт на склад
curl -s -X POST http://localhost:8002/api/v1/products/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Свекла","unit":"kg","initial_stock":"20.000","min_stock_level":"5.000"}'

# 5. Создать заказ
ORDER_ID=$(curl -s -X POST http://localhost:8003/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -d "{\"table_number\":3,\"items\":[{\"dish_id\":\"$DISH_ID\",\"quantity\":2}]}" \
  | jq -r .id)

# 6. Кухня берёт заказ в работу
curl -s -X POST http://localhost:8003/api/v1/orders/$ORDER_ID/take | jq .status

# 7. Отметить как готово
curl -s -X POST http://localhost:8003/api/v1/orders/$ORDER_ID/ready | jq .status

# 8. Закрыть (запускает списание запаса на складе)
curl -s -X POST http://localhost:8003/api/v1/orders/$ORDER_ID/close | jq .

# 9. Обновить цену блюда и просмотреть историю
curl -s -X PATCH http://localhost:8001/api/v1/dishes/$DISH_ID/price \
  -H "Content-Type: application/json" -d '{"price":"180.00"}'
curl -s http://localhost:8001/api/v1/dishes/$DISH_ID/price-history | jq .
```
