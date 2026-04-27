#!/bin/bash
# Запуск бота после заполнения .env
# Запускать из /opt/perfume-bot: bash scripts/start.sh

set -e

if [ ! -f .env ]; then
  echo "Ошибка: файл .env не найден. Скопируй .env.example и заполни значения."
  exit 1
fi

if grep -q "your_bot_token_here" .env; then
  echo "Ошибка: в .env не заполнен TELEGRAM_BOT_TOKEN."
  exit 1
fi

echo "=== Сборка образов ==="
docker compose build --parallel

echo "=== Запуск сервисов ==="
docker compose up -d postgres redis
echo "Ожидание готовности БД..."
sleep 5

echo "=== Применение миграций ==="
docker compose run --rm api alembic upgrade head

echo "=== Запуск всех сервисов ==="
docker compose up -d

echo ""
echo "======================================================"
echo "  Бот запущен!"
echo "======================================================"
echo ""
echo "Проверить статус:  docker compose ps"
echo "Логи бота:         docker compose logs -f bot"
echo "Логи воркера:      docker compose logs -f worker"
echo "Остановить:        docker compose down"
echo ""
echo "Для загрузки каталога парфюмов:"
echo "  docker compose exec api python scripts/seed_catalog.py --csv /path/to/fragrantica.csv"
