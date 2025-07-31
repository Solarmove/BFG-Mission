#!/usr/bin/env sh
set -e

# Переходим в рабочую директорию (куда скопирован ваш код)
cd /app

# Применяем все миграции
alembic upgrade head

# Запускаем бота
exec uv run python -m bot
