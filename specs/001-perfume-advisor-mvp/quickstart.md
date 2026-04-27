# Быстрый старт: Парфюмерный советник MVP

**Дата**: 2026-04-27

---

## Предварительные требования

- Docker & Docker Compose v2+
- Python 3.11+ (для локального запуска без Docker)
- Токен Telegram-бота (получить у @BotFather)
- Датасет Fragrantica с Kaggle (CSV-файл парфюмов)

---

## 1. Настройка окружения

```bash
cp .env.example .env
```

Заполнить `.env`:

```dotenv
# Telegram
TELEGRAM_BOT_TOKEN=your_token_here

# PostgreSQL
POSTGRES_USER=perfume
POSTGRES_PASSWORD=secret
POSTGRES_DB=perfume_bot
DATABASE_URL=postgresql+asyncpg://perfume:secret@postgres:5432/perfume_bot

# Redis
REDIS_URL=redis://redis:6379/0

# LLM (опционально для MVP)
ANTHROPIC_API_KEY=your_key_here
```

---

## 2. Запуск через Docker Compose

```bash
# Поднять все сервисы
docker compose up -d

# Применить миграции
docker compose exec api alembic upgrade head

# Загрузить каталог из датасета Fragrantica
docker compose exec api python scripts/seed_catalog.py --csv /data/fragrantica.csv

# Посмотреть логи бота
docker compose logs -f bot
```

---

## 3. Локальный запуск (без Docker)

```bash
# Установить зависимости
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Запустить PostgreSQL и Redis локально (или через Docker)
docker compose up -d postgres redis

# Применить миграции (DATABASE_URL должен указывать на localhost)
alembic upgrade head

# Загрузить каталог
python scripts/seed_catalog.py --csv /path/to/fragrantica.csv

# Запустить бота
python -m perfume_bot.bot.main

# В отдельном терминале — воркер
celery -A perfume_bot.workers.app worker --loglevel=info

# Планировщик
celery -A perfume_bot.workers.app beat --loglevel=info
```

---

## 4. Запуск тестов

```bash
# Все тесты
pytest

# Только контрактные тесты скраперов
pytest tests/contract/ -v

# Только интеграционные
pytest tests/integration/ -v

# С покрытием
pytest --cov=perfume_bot --cov-report=term-missing
```

---

## 5. Проверка работоспособности

После запуска выполнить в Telegram:

1. Открыть бота, отправить `/start` → должно появиться приветствие с кнопками категорий.
2. Выбрать 1–2 категории → нажать «Далее» → выбрать несколько нот.
3. Нажать «Показать подборку» → должны появиться карточки с духами.
4. Нажать «В избранное» на одной карточке → должно прийти подтверждение.
5. Отправить `/favorites` → должен отобразиться список с добавленным парфюмом.

---

## 6. Создание новой миграции

```bash
alembic revision --autogenerate -m "add_column_X_to_table_Y"
# Проверить сгенерированный файл в migrations/versions/
alembic upgrade head
```

---

## 7. Структура окружений

| Окружение | БД | Redis | Боты |
|-----------|----|-------|------|
| `local` | SQLite (`:memory:` или файл) | локальный Redis | тестовый бот |
| `staging` | PostgreSQL (Docker) | Redis (Docker) | тестовый бот |
| `prod` | PostgreSQL (managed) | Redis (managed) | боевой бот |
