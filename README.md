# Парфюмерный советник — Telegram-бот

Telegram-бот для подбора духов по ароматическим нотам. Пользователь выбирает предпочтительные ноты, бот подбирает подходящие парфюмы, показывает актуальные цены в российских онлайн-магазинах и уведомляет о снижении стоимости.

---

## Возможности

- **Подбор по нотам** — выбор категорий и конкретных нот, рекомендации по косинусному сходству (numpy, без ML)
- **Избранное** — добавление парфюмов в список избранного, управление через команду `/favorites`
- **Мониторинг цен** — автоматическая проверка каждые 6 часов; уведомление при снижении ≥ 10%
- **Скрапинг** — Randewoo, Notino, Золотое Яблоко, Летуаль (с circuit breaker и задержками)
- **REST API** — внутренние эндпоинты `/recommendations`, `/favorites`, `/prices`

---

## Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Telegram-бот | aiogram 3, FSM + RedisStorage |
| REST API | FastAPI + uvicorn |
| БД | PostgreSQL (prod) / SQLite (dev/CI) |
| ORM / миграции | SQLAlchemy 2 async, Alembic |
| Очереди | Celery 5 + Celery Beat, Redis-брокер |
| Скрапинг | httpx + BeautifulSoup4 |
| Рекомендации | numpy (cosine similarity) |
| Конфигурация | pydantic-settings, .env |
| Инфраструктура | Docker Compose (6 сервисов) |

---

## Быстрый старт

### Требования

- Docker & Docker Compose v2+
- Токен Telegram-бота (получить у @BotFather)
- Датасет Fragrantica с Kaggle (CSV-файл парфюмов)

### 1. Скопировать конфигурацию

```bash
cp .env.example .env
```

Заполнить `.env`:

```dotenv
TELEGRAM_BOT_TOKEN=your_token_here
DATABASE_URL=postgresql+asyncpg://perfume:secret@postgres:5432/perfume_bot
REDIS_URL=redis://redis:6379/0
ANTHROPIC_API_KEY=your_key_here  # опционально для MVP
```

### 2. Запустить через Docker Compose

```bash
docker compose up -d

# Применить миграции
docker compose exec api alembic upgrade head

# Загрузить каталог парфюмов из CSV
docker compose exec api python scripts/seed_catalog.py --csv /data/fragrantica.csv

# Логи бота
docker compose logs -f bot
```

### 3. Локальный запуск (без Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Поднять только БД и Redis
docker compose up -d postgres redis

# Миграции
alembic upgrade head

# Загрузить каталог
python scripts/seed_catalog.py --csv /path/to/fragrantica.csv

# Бот
python -m perfume_bot.bot.main

# Celery воркер (в отдельном терминале)
celery -A perfume_bot.workers.app worker --loglevel=info

# Celery Beat (в отдельном терминале)
celery -A perfume_bot.workers.app beat --loglevel=info
```

---

## Тесты

```bash
# Все тесты
pytest

# Только контрактные тесты скраперов
pytest tests/contract/ -v

# Только интеграционные тесты
pytest tests/integration/ -v

# Юнит-тесты
pytest tests/unit/ -v

# С отчётом о покрытии
pytest --cov=perfume_bot --cov-report=term-missing
```

---

## Структура проекта

```
perfume-bot/
├── perfume_bot/
│   ├── api/
│   │   ├── main.py                  # FastAPI приложение
│   │   └── routers/
│   │       ├── recommendations.py   # GET /recommendations/
│   │       ├── favorites.py         # GET/POST/DELETE /favorites/
│   │       └── prices.py            # GET /prices/{perfume_id}
│   ├── bot/
│   │   ├── handlers/
│   │   │   ├── start.py             # /start, главное меню
│   │   │   ├── notes.py             # Выбор категорий и нот
│   │   │   ├── recommendations.py   # Просмотр рекомендаций
│   │   │   └── favorites.py         # Управление избранным
│   │   ├── keyboards.py             # Построители клавиатур
│   │   ├── main.py                  # Dispatcher, middleware, роутеры
│   │   └── states.py                # FSM-состояния (NoteSelection, FavoritesMenu)
│   ├── core/
│   │   ├── config.py                # Pydantic Settings
│   │   ├── database.py              # Async SQLAlchemy engine
│   │   └── redis.py                 # Async Redis-клиент
│   ├── llm/
│   │   └── provider.py              # LLMProvider (шаблоны в MVP)
│   ├── models/
│   │   ├── base.py                  # DeclarativeBase
│   │   ├── perfume.py               # FragranceCategory, FragranceNote, Perfume, PerfumeNote
│   │   ├── shop.py                  # Shop, ShopOffer (append-only)
│   │   ├── user.py                  # User
│   │   └── favorite.py              # Favorite
│   ├── scrapers/
│   │   ├── base.py                  # AbstractScraper, OfferResult, исключения
│   │   ├── randewoo.py              # RandewooScraper
│   │   ├── notino.py                # NotinoScraper
│   │   ├── zolotoe_yabloko.py       # ZolotoeYablokoScraper
│   │   └── letuagl.py               # LetuaglScraper
│   ├── services/
│   │   ├── recommendation.py        # RecommendationService (cosine similarity)
│   │   ├── favorites.py             # FavoritesService
│   │   └── notification.py          # NotificationService
│   └── workers/
│       ├── app.py                   # Celery app + Beat расписание
│       ├── price_checker.py         # Задача check_prices
│       ├── notifier.py              # Задача notify_user
│       └── catalog_updater.py       # Задача update_catalog (stub)
├── migrations/
│   ├── env.py
│   └── versions/
│       ├── 001_create_categories_notes.py
│       ├── 002_create_perfumes.py
│       ├── 003_create_shops_offers.py
│       └── 004_create_users_favorites.py
├── tests/
│   ├── conftest.py                  # SQLite in-memory фикстуры
│   ├── contract/                    # Контрактные тесты скраперов (respx)
│   ├── integration/                 # Интеграционные тесты сервисов
│   └── unit/                        # Юнит-тесты (cosine similarity)
├── fixtures/html/                   # HTML-фикстуры для тестов скраперов
├── docker/
│   ├── Dockerfile.bot
│   ├── Dockerfile.api
│   └── Dockerfile.worker
├── scripts/
│   └── seed_catalog.py              # Загрузка CSV-каталога Fragrantica
├── specs/                           # Spec-kit: спецификации и план реализации
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## API

Внутренний REST API доступен на порту `8000`:

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/recommendations/?note_ids=1,2,3` | Подборка парфюмов по ID нот |
| `GET` | `/favorites/{user_id}` | Список избранного пользователя |
| `POST` | `/favorites/{user_id}/{perfume_id}` | Добавить в избранное |
| `DELETE` | `/favorites/{favorite_id}` | Удалить из избранного |
| `GET` | `/prices/{perfume_id}` | Актуальные цены по магазинам |
| `GET` | `/healthz` | Проверка работоспособности |

---

## Архитектурные ограничения

- Таблица `shop_offers` — **append-only**: UPDATE и DELETE запрещены на уровне сервиса
- Скраперы: задержка ≥ 1 с между запросами; circuit breaker при ≥ 5 последовательных ошибках
- TDD: тесты пишутся до реализации (принцип конституции)
- Все ноты имеют тип `top`, `middle` или `base`; дефолт `base`

---

## Лицензия

Для образовательных целей. Данные парфюмов — датасет Fragrantica с Kaggle.
