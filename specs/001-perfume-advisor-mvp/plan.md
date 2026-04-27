# План реализации: Парфюмерный советник MVP

**Ветка**: `main` | **Дата**: 2026-04-27 | **Спецификация**: [spec.md](spec.md)
**Источник**: `specs/001-perfume-advisor-mvp/spec.md`

## Резюме

Telegram-бот на aiogram 3, который помогает пользователям подбирать духи по ароматическим
нотам (cosine similarity), хранит избранное в PostgreSQL и отслеживает цены в российских
интернет-магазинах через Celery-воркеры и скраперы. LLM-слой обеспечивает естественную
подачу результатов, не участвуя в логике рекомендаций.

## Технический контекст

**Язык/Версия**: Python 3.11+
**Основные зависимости**: aiogram 3, FastAPI, SQLAlchemy 2.x async, Alembic, Celery + Celery Beat, Redis, Playwright, httpx, numpy, pydantic-settings
**Хранилище**: PostgreSQL (prod), SQLite (dev/CI), Redis (FSM-состояние, кэш, брокер Celery)
**Тестирование**: pytest + pytest-asyncio; интеграционные тесты — против SQLite; тесты скраперов — против локальных HTML-фикстур
**Целевая платформа**: Linux-сервер, Docker Compose
**Тип проекта**: Telegram-бот + внутренний REST API + фоновые воркеры
**Цели производительности**: p95 ответа бота < 3 с; уведомление о снижении цены < 30 мин; цикл проверки цен ≤ 6 ч
**Ограничения**: задержка скрапера ≥ 1 с/домен; circuit breaker при ≥ 5 ошибках подряд; нет параллельных запросов к одному хосту
**Масштаб/Объём**: MVP для одного разработчика; каталог ~17 000–20 000 парфюмов (статический датасет Fragrantica с Kaggle)

## Проверка конституции

*GATE: обязательна перед Phase 0. Повторная проверка после Phase 1.*

| Принцип | Статус | Подтверждение |
|---------|--------|---------------|
| I. Test-First | ✅ | Для каждой задачи сначала пишутся тесты (Red → Green → Refactor) |
| II. Simplicity | ✅ | Рекомендации — cosine similarity на numpy; никакого ML в MVP |
| III. LLM-Aware | ✅ | LLM — только слой подачи ответов; класс `LLMProvider` изолирует провайдера; для MVP допустимы шаблонные ответы без LLM |
| IV. Data Integrity | ✅ | Все миграции через Alembic; `shop_offers` — append-only; SQLAlchemy-модели обязательны |
| V. UX First | ✅ | Все потоки через `StatesGroup` aiogram 3; хардкод текстов в обработчиках запрещён |
| VI. Ethical Scraping | ✅ | Абстрактный базовый класс для скраперов; задержки, circuit breaker, Fragrantica только из датасета |

*Нарушений нет. Gate пройден.*

## Структура проекта

### Документация (эта фича)

```text
specs/001-perfume-advisor-mvp/
├── plan.md              # этот файл
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── scraper-contract.md
│   └── bot-fsm.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Исходный код (корень репозитория)

```text
perfume_bot/
├── bot/
│   ├── main.py               # точка входа, настройка Dispatcher
│   ├── states.py             # определения StatesGroup
│   ├── keyboards.py          # построители InlineKeyboardMarkup
│   └── handlers/
│       ├── start.py          # /start
│       ├── notes.py          # выбор категорий и нот
│       ├── recommendations.py
│       └── favorites.py
├── api/
│   ├── main.py               # FastAPI app
│   └── routers/
│       ├── recommendations.py
│       ├── favorites.py
│       └── prices.py
├── models/
│   ├── user.py
│   ├── perfume.py            # Perfume, FragranceNote, FragranceCategory, PerfumeNote
│   ├── shop.py               # Shop, ShopOffer
│   └── favorite.py
├── services/
│   ├── recommendation.py     # cosine similarity + ранжирование
│   ├── favorites.py          # CRUD избранного
│   └── notification.py       # логика ценовых уведомлений
├── workers/
│   ├── app.py                # конфигурация Celery
│   ├── price_checker.py      # задача check_prices (каждые 6 ч)
│   ├── catalog_updater.py    # задача update_catalog (раз в сутки)
│   └── notifier.py           # задача notify_users
├── scrapers/
│   ├── base.py               # AbstractScraper
│   ├── randewoo.py
│   ├── notino.py
│   ├── zolotoe_yabloko.py
│   └── letuagl.py
├── llm/
│   └── provider.py           # LLMProvider — абстракция над Claude API
└── core/
    ├── config.py             # Pydantic Settings
    ├── database.py           # async engine + sessionmaker
    └── redis.py              # Redis-клиент

tests/
├── contract/
│   ├── test_randewoo.py      # против HTML-фикстуры
│   ├── test_notino.py
│   ├── test_zolotoe_yabloko.py
│   └── test_letuagl.py
├── integration/
│   ├── test_recommendation_service.py
│   ├── test_favorites_service.py
│   └── test_price_checker.py
└── unit/
    ├── test_cosine_similarity.py
    └── test_notification_logic.py

fixtures/html/               # сохранённые HTML-страницы магазинов для тестов

migrations/versions/         # Alembic-миграции (нумерация: 001_, 002_, ...)

docker/
├── Dockerfile.bot
├── Dockerfile.api
└── Dockerfile.worker

docker-compose.yml
pyproject.toml
.env.example
```

**Решение по структуре**: монорепозиторий — единый Python-пакет `perfume_bot` с разделением по слоям (bot / api / workers / scrapers / services / models / core). Все сервисы поднимаются через один `docker-compose.yml`.
