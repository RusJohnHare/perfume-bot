# Модель данных: Парфюмерный советник MVP

**Дата**: 2026-04-27
**Источник**: `specs/001-perfume-advisor-mvp/spec.md`, `research.md`

---

## Сущности и таблицы

### `users` — Пользователи

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | внутренний идентификатор |
| `tg_user_id` | BIGINT | UNIQUE, NOT NULL | Telegram user ID |
| `username` | VARCHAR(64) | NULLABLE | @username в Telegram |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | дата регистрации |

**Индексы**: UNIQUE на `tg_user_id`.

---

### `fragrance_categories` — Категории ароматов

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | SERIAL | PK | |
| `name` | VARCHAR(64) | UNIQUE, NOT NULL | «Цитрусовые», «Древесные», … |

**Начальные данные**: Цитрусовые, Древесные, Цветочные, Мускусные, Восточные, Свежие,
Пряные, Фужерные, Шипровые, Гурманские.

---

### `fragrance_notes` — Ароматические ноты

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | SERIAL | PK | |
| `name` | VARCHAR(128) | UNIQUE, NOT NULL | «Бергамот», «Сандал», … |
| `category_id` | INT | FK → fragrance_categories.id, NOT NULL | |

**Индексы**: FK-индекс на `category_id`.

---

### `perfumes` — Духи

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | SERIAL | PK | |
| `name` | VARCHAR(256) | NOT NULL | название парфюма |
| `brand` | VARCHAR(128) | NOT NULL | бренд |
| `description` | TEXT | NULLABLE | краткое описание |
| `fragrantica_url` | VARCHAR(512) | NULLABLE | ссылка на карточку Fragrantica |

**Индексы**: составной на `(brand, name)`.

---

### `perfume_notes` — Ноты парфюма (связующая таблица)

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `perfume_id` | INT | FK → perfumes.id, NOT NULL | |
| `note_id` | INT | FK → fragrance_notes.id, NOT NULL | |
| `note_type` | VARCHAR(8) | CHECK IN ('top','middle','base','main') | |

**PK**: `(perfume_id, note_id)`.

---

### `shops` — Магазины

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | SERIAL | PK | |
| `name` | VARCHAR(64) | UNIQUE, NOT NULL | «Randewoo», «Notino», … |
| `base_url` | VARCHAR(256) | NOT NULL | корневой URL магазина |

**Начальные данные**: Randewoo, Notino, Золотое Яблоко, Летуаль.

---

### `shop_offers` — Предложения магазинов *(append-only)*

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | |
| `perfume_id` | INT | FK → perfumes.id, NOT NULL | |
| `shop_id` | INT | FK → shops.id, NOT NULL | |
| `url` | VARCHAR(1024) | NOT NULL | прямая ссылка на товар |
| `price_rub` | DECIMAL(10,2) | NULLABLE | цена в рублях; NULL = неизвестна |
| `in_stock` | BOOLEAN | NOT NULL, DEFAULT true | |
| `checked_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | время проверки |

**Правила**:
- Записи только добавляются; UPDATE и DELETE запрещены на уровне приложения.
- «Актуальная» цена = запись с максимальным `checked_at` для пары `(perfume_id, shop_id)`.

**Индексы**:
- `(perfume_id, shop_id, checked_at DESC)` — для выборки актуальной цены.
- `(shop_id, checked_at DESC)` — для обхода воркером по магазину.

---

### `favorites` — Избранное

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `perfume_id` | INT | FK → perfumes.id, NOT NULL | |
| `notify_on_price_drop` | BOOLEAN | NOT NULL, DEFAULT true | |
| `added_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Ограничения**: UNIQUE `(user_id, perfume_id)` — дедупликация на уровне БД.

**Индексы**:
- `(user_id)` — список избранного пользователя.
- `(notify_on_price_drop)` WHERE = true — выборка для воркера мониторинга.

---

## Диаграмма связей

```
fragrance_categories
    │ 1
    │
    ▼ N
fragrance_notes ◄──────────── perfume_notes ────────────► perfumes
                                                              │ 1
                                                              │
                                                              ▼ N
                                                         shop_offers ◄─── shops
                                                              │
                                                              │ (через perfume_id)
                                                              │
users ──────────────────────────────────────────────────► favorites
```

---

## Переходы состояний избранного

```
[не в избранном]
       │  нажать «В избранное»
       ▼
[в избранном, уведомления включены]  ←──── нажать «Вкл. уведомления»
       │  нажать «Откл. уведомления»
       ▼
[в избранном, уведомления выключены]
       │  нажать «Убрать из избранного»  (из любого состояния)
       ▼
[не в избранном]
```

---

## Заметки по миграциям

- Файлы именуются: `001_create_users.py`, `002_create_notes.py`, …
- При начальном наполнении данных из датасета Fragrantica используются отдельные
  seed-скрипты (`scripts/seed_catalog.py`), а не Alembic data migrations.
- `shop_offers` не имеет внешних ключей с CASCADE DELETE — данные должны быть неизменяемы.
