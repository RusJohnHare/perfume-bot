#!/bin/bash
# Скрипт первоначальной настройки сервера Ubuntu 22.04
# Запускать от root: bash setup_server.sh

set -e

REPO_URL="https://github.com/RusJohnHare/perfume-bot.git"
APP_DIR="/opt/perfume-bot"

echo "=== Установка Docker ==="
apt-get update -q
apt-get install -y -q ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -q
apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker
echo "Docker $(docker --version) установлен"

echo "=== Клонирование репозитория ==="
git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"

echo "=== Создание .env ==="
cp .env.example .env

echo ""
echo "======================================================"
echo "  Установка завершена!"
echo "======================================================"
echo ""
echo "Следующий шаг — заполни .env:"
echo "  nano $APP_DIR/.env"
echo ""
echo "Минимум нужно указать:"
echo "  TELEGRAM_BOT_TOKEN=<токен от @BotFather>"
echo "  POSTGRES_PASSWORD=<придумай пароль>"
echo ""
echo "Затем запусти:"
echo "  cd $APP_DIR && bash scripts/start.sh"
