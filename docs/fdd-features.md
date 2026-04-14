# FDD — Feature Catalogue

> Авторитетний довідник Feature-Driven Development для екосистеми menu-service.
> Кожен запис відповідає класу `TestFeatureXxx` у `tests/features/`.

---

## 1. menu-service

### 1.1 Category Create
**As** a restaurant manager **I want** to create menu categories **so that** dishes can be organised by type.

| Сценарій | Очікуваний результат |
|---|---|
| Валідна назва + опис | 201, тіло містить `id`, `is_active: true` |
| Дублікат назви | 409 |
| Пуста назва (`"   "`) | 422 |
| Порожня назва (`""`) | 422 |

**Покрито:** `tests/features/test_category_crud.py::TestFeatureCategoryCreate`

---

### 1.2 Category Read
**As** a restaurant manager **I want** to list and retrieve categories **so that** I can see what categories exist.

| Сценарій | Очікуваний результат |
|---|---|
| Список усіх | 200, список |
| Отримати за ID | 200, правильний об'єкт |
| Неіснуючий ID | 404 |
| Фільтр `active_only=true` | тільки активні категорії |

**Покрито:** `tests/features/test_category_crud.py::TestFeatureCategoryRead`

---

### 1.3 Category Update
**As** a restaurant manager **I want** to update category details **so that** I can correct names or deactivate categories.

| Сценарій | Очікуваний результат |
|---|---|
| Перейменувати категорію | 200, нова назва у відповіді |
| Деактивувати (`is_active: false`) | 200, `is_active: false` |
| Оновити неіснуючий ID | 404 |

**Покрито:** `tests/features/test_category_crud.py::TestFeatureCategoryUpdate`

---

### 1.4 Category Delete
**As** a restaurant manager **I want** to delete categories **so that** obsolete categories are removed.

| Сценарій | Очікуваний результат |
|---|---|
| Видалити існуючу | 204 |
| Наступний GET | 404 |
| Видалити неіснуючу | 404 |

**Покрито:** `tests/features/test_category_crud.py::TestFeatureCategoryDelete`

---

### 1.5 Dish Create
**As** a restaurant manager **I want** to create dishes with prices and nutrition info **so that** the menu is complete.

| Сценарій | Очікуваний результат |
|---|---|
| Мінімальний (назва + ціна) | 201, `is_available: true` |
| З повними нутрицієнтами | 201, всі поля збережено |
| З валідним `category_id` | 201, `category_id` встановлено |
| З неіснуючим `category_id` | 404 |
| Нульова ціна | 422 |
| Від'ємна ціна | 422 |

**Покрито:** `tests/features/test_dish_management.py::TestFeatureDishCreate`

---

### 1.6 Dish Read
**As** a guest **I want** to browse dishes **so that** I can choose what to order.

| Сценарій | Очікуваний результат |
|---|---|
| Список страв | 200, список |
| Отримати за ID | 200, правильний об'єкт |
| Неіснуючий ID | 404 |
| Фільтр `available_only=true` | тільки доступні страви |
| Фільтр за `category_id` | тільки страви цієї категорії |

**Покрито:** `tests/features/test_dish_management.py::TestFeatureDishRead`

---

### 1.7 Dish Update
**As** a restaurant manager **I want** to update dish details **so that** information stays accurate.

| Сценарій | Очікуваний результат |
|---|---|
| Позначити недоступною | 200, `is_available: false` |
| Оновити нутрицієнти | 200, нові калорії збережено |

**Покрито:** `tests/features/test_dish_management.py::TestFeatureDishUpdate`

---

### 1.8 Price Management
**As** a restaurant manager **I want** to change dish prices with history **so that** I can audit price changes.

| Сценарій | Очікуваний результат |
|---|---|
| Оновлення ціни | 200, нова ціна; запис в історії |
| Та сама ціна надіслана | 200; без запису в історії |
| Два послідовних оновлення | 2 записи в історії, найновіший перший |

**Покрито:** `tests/features/test_dish_management.py::TestFeaturePriceManagement`

---

### 1.9 Dish Delete
**As** a restaurant manager **I want** to delete dishes **so that** discontinued items are removed.

| Сценарій | Очікуваний результат |
|---|---|
| Видалити існуючу | 204 |
| Наступний GET | 404 |

**Покрито:** `tests/features/test_dish_management.py::TestFeatureDishDelete`

---

## 2. auth-service

### 2.1 Login
**As** a system user **I want** to log in with email and password **so that** I receive a JWT for subsequent requests.

| Сценарій | Очікуваний результат |
|---|---|
| Правильні дані | 200, `access_token` (JWT з 3 сегментів), `token_type: bearer`, `expires_in > 0` |
| Невірний пароль | 401 |
| Неіснуючий email | 401 |
| Невірний формат email | 422 |
| Відсутнє поле password | 422 |
| Токен несе permissions | claim `permissions` непорожній |

**Покрито:** `tests/features/test_auth_flow.py::TestFeatureLogin`

---

### 2.2 Current User (me)
**As** an authenticated user **I want** to retrieve my profile **so that** I can see my role and email.

| Сценарій | Очікуваний результат |
|---|---|
| Валідний токен | 200, `email`, `is_active: true`, `role_name` |
| Без токена | 401 або 403 |
| Невалідний токен | 401 |
| Токен адміна | список `permissions` непорожній, містить `users:roles:manage` |

**Покрито:** `tests/features/test_auth_flow.py::TestFeatureMe`

---

### 2.3 Health Check
**As** infrastructure **I want** a health endpoint **so that** load balancers can probe the service.

| Сценарій | Очікуваний результат |
|---|---|
| GET /health | 200, `{"status": "ok"}` |

**Покрито:** `tests/features/test_auth_flow.py::TestFeatureHealth`

---

### 2.4 Role List
**As** an admin **I want** to list all roles **so that** I can see what roles exist.

| Сценарій | Очікуваний результат |
|---|---|
| Авторизований | 200, список містить `admin` |
| Неавторизований | 401 або 403 |

**Покрито:** `tests/features/test_roles.py::TestFeatureRoleList`

---

### 2.5 Role Create
**As** an admin **I want** to create roles with optional permissions **so that** I can group access rights.

| Сценарій | Очікуваний результат |
|---|---|
| Мінімальний (тільки назва) | 201, `is_system: false`, `permissions: []` |
| З кодами permissions | 201, список permissions заповнено |
| Дублікат назви | 409 |
| Пуста назва | 422 |
| Невідомий код permission | 409 |

**Покрито:** `tests/features/test_roles.py::TestFeatureRoleCreate`

---

### 2.6 Role Read
**As** an admin **I want** to get a role by ID **so that** I can inspect its permissions.

| Сценарій | Очікуваний результат |
|---|---|
| Валідний ID | 200, `name`, список `permissions` |
| Неіснуючий ID | 404 |
| Системна роль (`admin`) | `is_system: true` |

**Покрито:** `tests/features/test_roles.py::TestFeatureRoleRead`

---

### 2.7 Role Update
**As** an admin **I want** to rename or re-describe roles **so that** I can keep names meaningful.

| Сценарій | Очікуваний результат |
|---|---|
| Перейменувати | 200, нова назва |
| Оновити опис | 200, новий опис |
| Неіснуюча роль | 404 |
| Перейменувати на існуючу назву | 409 |

**Покрито:** `tests/features/test_roles.py::TestFeatureRoleUpdate`

---

### 2.8 Role Permissions
**As** an admin **I want** to replace a role's permission set atomically **so that** changes are consistent.

| Сценарій | Очікуваний результат |
|---|---|
| Замінити на новий набір | 200, тільки нові коди присутні |
| Замінити на порожній список | 200, `permissions: []` |
| Невідомий код permission | 422 |

**Покрито:** `tests/features/test_roles.py::TestFeatureRolePermissions`

---

### 2.9 Role Delete
**As** an admin **I want** to delete non-system roles **so that** obsolete roles are removed.

| Сценарій | Очікуваний результат |
|---|---|
| Видалити кастомну роль | 204 |
| Наступний GET | 404 |
| Видалити системну роль | 409 |
| Видалити неіснуючу | 404 |

**Покрито:** `tests/features/test_roles.py::TestFeatureRoleDelete`

---

### 2.10 User List
**As** an admin **I want** to list all users **so that** I can manage accounts.

| Сценарій | Очікуваний результат |
|---|---|
| Авторизований | 200, список містить seed-адміна |
| Неавторизований | 401 або 403 |

**Покрито:** `tests/features/test_users.py::TestFeatureUserList`

---

### 2.11 User Create
**As** an admin **I want** to create user accounts **so that** staff can log in.

| Сценарій | Очікуваний результат |
|---|---|
| Мінімальний (email + ім'я + пароль) | 201, `is_active: true`, `role_id: null` |
| З роллю | 201, `role_id` встановлено |
| Дублікат email | 409 |
| Пароль занадто короткий (< 6 символів) | 422 |
| Невірний формат email | 422 |
| `is_active: false` | 201, `is_active: false` |

**Покрито:** `tests/features/test_users.py::TestFeatureUserCreate`

---

### 2.12 User Read
**As** an admin **I want** to get a user by ID **so that** I can inspect their details.

| Сценарій | Очікуваний результат |
|---|---|
| Валідний ID | 200, правильний об'єкт |
| Неіснуючий ID | 404 |

**Покрито:** `tests/features/test_users.py::TestFeatureUserRead`

---

### 2.13 User Update
**As** an admin **I want** to update user accounts **so that** I can manage names, passwords, roles.

| Сценарій | Очікуваний результат |
|---|---|
| Оновити ім'я | 200, нове ім'я |
| Деактивувати | 200, `is_active: false` |
| Змінити пароль | 200 |
| Призначити роль | 200, `role_id` встановлено |
| Неіснуючий користувач | 404 |
| Порожнє тіло (без полів) | 422 |

**Покрито:** `tests/features/test_users.py::TestFeatureUserUpdate`

---

### 2.14 User Delete
**As** an admin **I want** to delete users **so that** former staff cannot log in.

| Сценарій | Очікуваний результат |
|---|---|
| Видалити існуючого | 204 |
| Наступний GET | 404 |
| Неіснуючий ID | 404 |

**Покрито:** `tests/features/test_users.py::TestFeatureUserDelete`

---

### 2.15 Inactive User Login
**As** the system **I want** to block inactive users from logging in **so that** deactivated accounts cannot access the API.

| Сценарій | Очікуваний результат |
|---|---|
| Спроба входу неактивним юзером | 403 |

**Покрито:** `tests/features/test_users.py::TestFeatureInactiveUserLogin`

---

## 3. warehouse-service

### 3.1 Product Create
**As** a warehouse manager **I want** to add products (ingredients) **so that** stock levels can be tracked.

| Сценарій | Очікуваний результат |
|---|---|
| Мінімальний (назва + одиниця) | 201, `current_stock: 0` |
| З початковим запасом | 201, `current_stock` = вказане значення |
| Дублікат назви | 409 |
| Невалідна одиниця | 422 |

**Покрито:** `tests/features/test_product_crud.py::TestFeatureProductCreate`

---

### 3.2 Stock Management
**As** a warehouse manager **I want** to record stock movements **so that** the kitchen always knows what is available.

| Сценарій | Очікуваний результат |
|---|---|
| Надходження (INCOMING) | 200, `current_stock` збільшується |
| Витрата (OUTGOING) | 200, `current_stock` зменшується |
| Витрата > наявного запасу | 422 |
| Будь-який рух | записується в `/movements` |
| Продукт нижче `min_stock_level` | з'являється у фільтрі `?low_stock_only=true` |

**Покрито:** `tests/features/test_product_crud.py::TestFeatureStockManagement`

---

### 3.3 Product Read
**As** a kitchen worker **I want** to browse products **so that** I can check stock levels.

| Сценарій | Очікуваний результат |
|---|---|
| Список усіх | 200, список |
| Отримати за ID | 200, правильний об'єкт |
| Неіснуючий ID | 404 |

**Покрито:** `tests/features/test_product_crud.py::TestFeatureProductRead`

---

### 3.4 Product Delete
**As** a warehouse manager **I want** to delete products **so that** discontinued ingredients are removed.

| Сценарій | Очікуваний результат |
|---|---|
| Видалити існуючий | 204, наступний GET → 404 |

**Покрито:** `tests/features/test_product_crud.py::TestFeatureProductDelete`

---

## 4. order-service

### 4.1 Order Create
**As** a waiter **I want** to create orders for a table **so that** the kitchen can start preparing.

| Сценарій | Очікуваний результат |
|---|---|
| Валідне замовлення | 201, `status: CREATED`, список позицій заповнено |
| Розрахунок суми | `total_amount` = сума(ціна × кількість) |
| Порожній список позицій | 422 |
| Відсутнє поле items | 422 |
| Знімок ціни | `price_at_order` зберігається з menu-service на момент замовлення |

**Покрито:** `tests/features/test_order_lifecycle.py::TestFeatureCreateOrder`

---

### 4.2 Order Read
**As** a manager **I want** to query orders **so that** I can track all activity.

| Сценарій | Очікуваний результат |
|---|---|
| Отримати за ID | 200, правильний об'єкт |
| Неіснуючий ID | 404 |
| Список усіх | 200, список |
| Фільтр за `status` | тільки відповідні замовлення |

**Покрито:** `tests/features/test_order_lifecycle.py::TestFeatureOrderRead`

---

### 4.3 Order Status Lifecycle
**As** kitchen staff **I want** to advance order status **so that** the team knows progress.

Lifecycle: `CREATED → IN_PROGRESS → READY → CLOSED`
Скасування можливе з: `CREATED`, `IN_PROGRESS`

| Сценарій | Очікуваний результат |
|---|---|
| Взяти в роботу | 200, `status: IN_PROGRESS`, `taken_at` встановлено |
| Позначити готовим | 200, `status: READY` |
| Закрити замовлення | 200, `status: CLOSED`, `closed_at` встановлено |
| Скасувати зі статусу CREATED | 200, `status: CANCELLED` |
| Скасувати зі статусу IN_PROGRESS | 200, `status: CANCELLED` |
| Невалідний перехід (CREATED → CLOSED) | 422 |
| Скасувати CLOSED замовлення | 422 |

**Покрито:** `tests/features/test_order_lifecycle.py::TestFeatureOrderStatusLifecycle`

---

### 4.4 Order Delete
**As** a manager **I want** to delete orders **so that** test or erroneous orders can be removed.

| Сценарій | Очікуваний результат |
|---|---|
| Видалити існуюче | 204 |
| Наступний GET | 404 |

**Покрито:** `tests/features/test_order_lifecycle.py::TestFeatureOrderDelete`

---

## Зведена таблиця покриття

| Сервіс | TDD тести | FDD тести | Фіч |
|---|---|---|---|
| menu-service | 2 файли, 38 тестів | 2 файли, 32 тести | 9 |
| auth-service | 2 файли, 52 тести | 3 файли, 54 тести | 15 |
| warehouse-service | 1 файл, 22 тести | 1 файл, 13 тестів | 4 |
| order-service | 1 файл, 19 тестів | 1 файл, 18 тестів | 4 |
| **Разом** | **131 тест** | **117 тестів** | **32** |
