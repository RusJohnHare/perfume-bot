---
description: "Список задач — Парфюмерный советник MVP"
---

# Задачи: Парфюмерный советник MVP

**Источник**: `specs/001-perfume-advisor-mvp/`
**Зависимости**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Тесты**: TDD обязателен (Принцип I конституции). Тесты пишутся до реализации и должны падать.

**Организация**: задачи сгруппированы по сценарию для независимой реализации каждого.

## Формат: `[ID] [P?] [Story?] Описание с путём к файлу`

- **[P]**: можно выполнять параллельно (разные файлы, нет зависимостей)
- **[Story]**: к какому сценарию относится задача (US1, US2, US3)
- Тесты (⚠️ TDD) всегда предшествуют реализации

---

## Фаза 1: Инициализация проекта

**Цель**: базовая структура, зависимости, инфраструктура разработки

- [x] T001 Создать структуру директорий проекта согласно plan.md: `perfume_bot/bot/handlers/`, `perfume_bot/api/routers/`, `perfume_bot/models/`, `perfume_bot/services/`, `perfume_bot/workers/`, `perfume_bot/scrapers/`, `perfume_bot/llm/`, `perfume_bot/core/`, `tests/contract/`, `tests/integration/`, `tests/unit/`, `fixtures/html/`, `migrations/`, `docker/`, `scripts/`
- [x] T002 Инициализировать `pyproject.toml` с зависимостями: aiogram==3.*, fastapi, uvicorn, sqlalchemy[asyncio], alembic, asyncpg, aiosqlite, celery[redis], redis, httpx, numpy, pydantic-settings, anthropic; dev: pytest, pytest-asyncio, pytest-cov, respx
- [x] T003 [P] Создать `.env.example` со всеми переменными окружения (`TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, `REDIS_URL`, `ANTHROPIC_API_KEY`)
- [x] T004 [P] Написать `docker-compose.yml` с сервисами: postgres:16, redis:7-alpine, bot, api, worker, worker-beat
- [x] T005 [P] Настроить Alembic: `alembic init migrations`, заполнить `alembic.ini` и `migrations/env.py` для async SQLAlchemy
- [x] T006 [P] Настроить pytest в `pyproject.toml`: asyncio_mode = "auto", testpaths = ["tests"], фикстура async engine на SQLite in-memory

**Checkpoint**: `pytest` запускается без ошибок; `docker compose config` валиден.

---

## Фаза 2: Базовая инфраструктура *(блокирует все сценарии)*

**Цель**: общие компоненты, необходимые каждому сценарию

⚠️ **КРИТИЧНО**: работа над сценариями не может начаться до завершения этой фазы.

- [x] T007 Реализовать `perfume_bot/core/config.py` — класс `Settings` (Pydantic BaseSettings), все параметры из `.env`
- [x] T008 [P] Реализовать `perfume_bot/core/database.py` — async engine SQLAlchemy, `AsyncSessionLocal`, функция `get_db()`
- [x] T009 [P] Реализовать `perfume_bot/core/redis.py` — async Redis-клиент, `get_redis()`
- [x] T010 [P] Реализовать `perfume_bot/scrapers/base.py` — `AbstractScraper`, `OfferResult`, `ScraperError`, `ScraperBlockedError`, `ScraperParseError` согласно `contracts/scraper-contract.md`
- [x] T011 [P] Реализовать `perfume_bot/llm/provider.py` — `LLMProvider` с методом `format_recommendation(perfume) -> str`; в MVP использует шаблон без вызова API
- [x] T012 Создать миграцию Alembic `001_create_categories_notes.py`: таблицы `fragrance_categories`, `fragrance_notes` согласно `data-model.md`
- [x] T013 Создать миграцию Alembic `002_create_perfumes.py`: таблицы `perfumes`, `perfume_notes`
- [x] T014 Создать миграцию Alembic `003_create_shops_offers.py`: таблицы `shops`, `shop_offers` (append-only)
- [x] T015 Создать миграцию Alembic `004_create_users_favorites.py`: таблицы `users`, `favorites`
- [x] T016 Написать `scripts/seed_catalog.py` — загрузка парфюмов из CSV Fragrantica: категории, ноты, парфюмы, связи `perfume_notes`

**Checkpoint**: `alembic upgrade head` выполняется без ошибок; `seed_catalog.py --dry-run` парсит CSV.

---

## Фаза 3: Сценарий 1 — Выбор нот и рекомендации (P1) 🎯 MVP

**Цель**: пользователь открывает бота, выбирает ноты, получает 5 рекомендаций с ценами и ссылками

**Независимый тест**: запустить бота, отправить `/start`, выбрать 2–3 ноты, нажать «Показать подборку» — получить ≥ 5 карточек парфюмов.

### Тесты для Сценария 1 ⚠️ (написать до реализации, убедиться что падают)

- [x] T017 [P] [US1] Написать юнит-тесты cosine similarity в `tests/unit/test_cosine_similarity.py`: корректный результат для идентичных векторов, для пустого пересечения, для частичного совпадения
- [x] T018 [P] [US1] Написать интеграционный тест `RecommendationService` в `tests/integration/test_recommendation_service.py`: возвращает ≥ 5 результатов, fallback при < 5 точных совпадениях

### Реализация Сценария 1

- [x] T019 [P] [US1] Создать SQLAlchemy-модель `User` в `perfume_bot/models/user.py` (поля: id, tg_user_id, username, created_at)
- [x] T020 [P] [US1] Создать SQLAlchemy-модели `FragranceCategory`, `FragranceNote`, `Perfume`, `PerfumeNote` в `perfume_bot/models/perfume.py`
- [x] T021 [US1] Реализовать `RecommendationService` в `perfume_bot/services/recommendation.py`: построение бинарных векторов нот из БД, cosine similarity через numpy, ранжирование, fallback при < 5 (зависит от T019, T020)
- [x] T022 [US1] Объявить FSM-состояния `NoteSelection` (`choosing_categories`, `choosing_notes`, `viewing_results`) в `perfume_bot/bot/states.py`
- [x] T023 [US1] Реализовать построители клавиатур `categories_kb`, `notes_kb`, `perfume_card_kb`, `results_nav_kb` в `perfume_bot/bot/keyboards.py` согласно `contracts/bot-fsm.md`
- [x] T024 [US1] Реализовать обработчик `/start` и главного меню в `perfume_bot/bot/handlers/start.py` (зависит от T022, T023)
- [x] T025 [US1] Реализовать обработчики выбора категорий и нот в `perfume_bot/bot/handlers/notes.py` (зависит от T021, T022, T023)
- [x] T026 [US1] Реализовать обработчики просмотра рекомендаций (пагинация, карточки) в `perfume_bot/bot/handlers/recommendations.py` (зависит от T025)
- [x] T027 [US1] Настроить `Dispatcher`, `RedisStorage`, зарегистрировать роутеры в `perfume_bot/bot/main.py` (зависит от T024, T026)

**Checkpoint**: тесты T017, T018 зелёные; бот стартует, сценарий 1 работает от начала до конца.

---

## Фаза 4: Сценарий 2 — Управление избранным (P2)

**Цель**: добавить парфюм в избранное из карточки, просматривать и удалять список

**Независимый тест**: нажать «В избранное» → уйти → `/favorites` → увидеть добавленный парфюм без активного мониторинга цен.

### Тесты для Сценария 2 ⚠️ (написать до реализации, убедиться что падают)

- [x] T028 [US2] Написать интеграционный тест `FavoritesService` в `tests/integration/test_favorites_service.py`: добавление, дедупликация, удаление, переключение уведомлений

### Реализация Сценария 2

- [x] T029 [P] [US2] Создать SQLAlchemy-модель `Favorite` в `perfume_bot/models/favorite.py` (поля: id, user_id, perfume_id, notify_on_price_drop, added_at; UNIQUE constraint)
- [x] T030 [US2] Реализовать `FavoritesService` в `perfume_bot/services/favorites.py`: add, remove, list, toggle_notify, дедупликация на уровне БД (зависит от T029)
- [x] T031 [US2] Добавить построители клавиатур `favorites_item_kb`, `favorites_nav_kb`, `main_menu_kb` в `perfume_bot/bot/keyboards.py`
- [x] T032 [US2] Добавить FSM-состояния `FavoritesMenu` (`viewing_list`) в `perfume_bot/bot/states.py`
- [x] T033 [US2] Реализовать обработчики избранного (просмотр, удаление, toggle уведомлений) в `perfume_bot/bot/handlers/favorites.py` (зависит от T030, T031, T032)
- [x] T034 [US2] Зарегистрировать роутер `favorites` и команду `/favorites` в `perfume_bot/bot/main.py`
- [x] T035 [US2] Обновить `perfume_card_kb` в `keyboards.py`: кнопка «В избранное» / «Убрать из избранного» в зависимости от состояния

**Checkpoint**: тест T028 зелёный; сценарий 2 работает независимо от сценария 1.

---

## Фаза 5: Сценарий 3 — Мониторинг цен и уведомления (P3)

**Цель**: автоматическая проверка цен каждые 6 ч, уведомление при снижении ≥ 10%

**Независимый тест**: вручную вызвать задачу `check_prices` для конкретного парфюма → пользователь получает уведомление в Telegram в течение 30 мин.

### Тесты для Сценария 3 ⚠️ (написать до реализации, убедиться что падают)

- [x] T036 [P] [US3] Сохранить HTML-фикстуру страницы товара Randewoo в `fixtures/html/randewoo_product.html`; написать контрактный тест в `tests/contract/test_randewoo.py`
- [x] T037 [P] [US3] Сохранить HTML-фикстуру Notino в `fixtures/html/notino_product.html`; написать `tests/contract/test_notino.py`
- [x] T038 [P] [US3] Сохранить HTML-фикстуру Золотого Яблока в `fixtures/html/zolotoe_yabloko_product.html`; написать `tests/contract/test_zolotoe_yabloko.py`
- [x] T039 [P] [US3] Сохранить HTML-фикстуру Летуаль в `fixtures/html/letuagl_product.html`; написать `tests/contract/test_letuagl.py`
- [x] T040 [US3] Написать интеграционный тест задачи `check_prices` в `tests/integration/test_price_checker.py`: снижение цены ≥ 10% → событие уведомления создаётся; circuit breaker при ≥ 5 ошибках

### Реализация Сценария 3

- [x] T041 [P] [US3] Создать SQLAlchemy-модели `Shop`, `ShopOffer` в `perfume_bot/models/shop.py` (append-only: в сервисе запрещены UPDATE/DELETE)
- [x] T042 [US3] Реализовать скрапер `RandewooScraper` в `perfume_bot/scrapers/randewoo.py` (зависит от T010, T041)
- [x] T043 [P] [US3] Реализовать скрапер `NotinoScraper` в `perfume_bot/scrapers/notino.py`
- [x] T044 [P] [US3] Реализовать скрапер `ZolotoeYablokoScraper` в `perfume_bot/scrapers/zolotoe_yabloko.py`
- [x] T045 [P] [US3] Реализовать скрапер `LetuaglScraper` в `perfume_bot/scrapers/letuagl.py`
- [x] T046 [US3] Реализовать `NotificationService` в `perfume_bot/services/notification.py`: определение факта снижения ≥ 10%, формирование текста уведомления, отправка через `Bot(token=...)` + `asyncio.run()` (зависит от T041)
- [x] T047 [US3] Настроить Celery app в `perfume_bot/workers/app.py`: брокер Redis, backend Redis, настройки сериализации (зависит от T009)
- [x] T048 [US3] Реализовать задачу `check_prices` в `perfume_bot/workers/price_checker.py`: обход избранного с `notify=true`, вызов скрапера, сохранение `ShopOffer`, вызов `notify_users` при снижении ≥ 10% (зависит от T042–T046, T047)
- [x] T049 [US3] Реализовать задачу `notify_users` в `perfume_bot/workers/notifier.py`: отправка уведомлений пользователям через Telegram Bot API (зависит от T048)
- [x] T050 [US3] Настроить расписание Celery Beat в `perfume_bot/workers/app.py`: `check_prices` — каждые 6 ч, `update_catalog` — раз в сутки в 03:00

**Checkpoint**: тесты T036–T040 зелёные; при ручном вызове `check_prices.delay()` уведомление приходит в Telegram.

---

## Фаза N: Полировка и сквозные задачи

**Цель**: Docker-образы, FastAPI API, документация

- [x] T051 [P] Написать `docker/Dockerfile.bot` (multi-stage, Python 3.11-slim)
- [x] T052 [P] Написать `docker/Dockerfile.api` (multi-stage, Python 3.11-slim + uvicorn)
- [x] T053 [P] Написать `docker/Dockerfile.worker` (multi-stage, Python 3.11-slim + celery)
- [x] T054 [P] Реализовать FastAPI-эндпоинт `/recommendations` в `perfume_bot/api/routers/recommendations.py`
- [x] T055 [P] Реализовать FastAPI-эндпоинт `/favorites` в `perfume_bot/api/routers/favorites.py`
- [x] T056 [P] Реализовать FastAPI-эндпоинт `/prices` в `perfume_bot/api/routers/prices.py`
- [x] T057 [P] Реализовать `perfume_bot/api/main.py`: FastAPI app, подключение роутеров
- [x] T058 [P] Написать `README.md` с описанием проекта, инструкцией по запуску, структурой
- [x] T059 Провалидировать все сценарии по чеклисту `quickstart.md`

---

## Зависимости и порядок выполнения

### Зависимости между фазами

- **Фаза 1 (Setup)**: нет зависимостей — начинать немедленно
- **Фаза 2 (Foundational)**: зависит от завершения Фазы 1 — **блокирует все сценарии**
- **Сценарии (Фазы 3–5)**: зависят от завершения Фазы 2; могут идти параллельно при наличии ресурсов
- **Полировка**: зависит от завершения всех нужных сценариев

### Зависимости между сценариями

- **Сценарий 1 (P1)**: нет зависимостей от других сценариев
- **Сценарий 2 (P2)**: нет зависимостей от Сценария 1, но логически дополняет его
- **Сценарий 3 (P3)**: зависит от Сценария 2 (нужна таблица `favorites`)

### Внутри каждого сценария

1. Тесты пишутся первыми и должны **падать** — затем реализация
2. Модели → Сервисы → Обработчики/Задачи
3. Сценарий считается завершённым только после прохождения всех тестов

### Возможности параллельного выполнения

- Все задачи с меткой `[P]` внутри одной фазы можно выполнять одновременно
- В Фазе 2: T008, T009, T010, T011 — параллельно; T012–T015 — последовательно (миграции зависят от очерёдности)
- В Сценарии 3: T036–T039 (HTML-фикстуры и тесты скраперов), T042–T045 (скраперы) — параллельно

---

## Параллельный пример: Сценарий 3

```bash
# Запустить тесты скраперов одновременно (после сохранения фикстур):
Task: "Тест Randewoo в tests/contract/test_randewoo.py"     — T036
Task: "Тест Notino в tests/contract/test_notino.py"         — T037
Task: "Тест Золотого Яблока в tests/contract/test_zolotoe_yabloko.py" — T038
Task: "Тест Летуаль в tests/contract/test_letuagl.py"       — T039

# Запустить реализацию скраперов одновременно (после T042):
Task: "NotinoScraper в scrapers/notino.py"          — T043
Task: "ZolotoeYablokoScraper в scrapers/..."        — T044
Task: "LetuaglScraper в scrapers/letuagl.py"        — T045
```

---

## Стратегия реализации

### MVP-минимум (только Сценарий 1)

1. Завершить Фазу 1: Setup
2. Завершить Фазу 2: Foundational (**обязательно перед стартом Сценария 1**)
3. Завершить Фазу 3: Сценарий 1
4. **СТОП И ПРОВЕРКА**: протестировать Сценарий 1 независимо
5. Задеплоить / показать

### Инкрементальная доставка

1. Setup + Foundational → база готова
2. Сценарий 1 → тест независимо → деплой (MVP!)
3. Сценарий 2 → тест независимо → деплой
4. Сценарий 3 → тест независимо → деплой
5. Полировка

---

## Итого задач

| Фаза | Задач | Из них параллельных |
|------|-------|---------------------|
| Фаза 1: Setup | 6 | 4 |
| Фаза 2: Foundational | 10 | 5 |
| Фаза 3: Сценарий 1 (P1) | 11 | 4 |
| Фаза 4: Сценарий 2 (P2) | 8 | 2 |
| Фаза 5: Сценарий 3 (P3) | 15 | 8 |
| Полировка | 9 | 8 |
| **Итого** | **59** | **31** |
