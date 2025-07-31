#!/usr/bin/env sh
set -e

# Переходим в рабочую директорию (куда скопирован ваш код)
cd /app


exec uv run alembic revision --autogenerate

# Применяем все миграции
exec uv run alembic upgrade head

# Запускаем бота
exec uv run python -m bot
