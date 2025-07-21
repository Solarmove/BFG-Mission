# AIogram Bot Template

Это шаблон для создания Telegram-бота с использованием библиотек:
- [aiogram 3.x.x](https://github.com/aiogram/aiogram)
- [aiogram_dialog](https://github.com/Tishka17/aiogram_dialog)
- [aiogram_i18n](https://github.com/aiogram/i18n)
- [arq](https://github.com/python-arq/arq)

а также поддержки Redis и многоязычности (i18n).
Шаблон предоставляет базовую структуру проекта,
включающую работу с планировщиком задач, конфигурацию через переменные окружения и пример
использования systemd для автозапуска на сервере.

## Особенности

- Базовая структура: четкое разделение логики бота, планировщика и настроек.
- Redis: интеграция для кэширования и хранения данных.
- Postgres: поддержка для работы с базой данных.
- Sqlalchemy: ORM для работы с базой данных.
- i18n: поддержка многоязычных сообщений.
- Systemd Unit-файлы: примеры для автозапуска бота и планировщика на Linux (Ubuntu).
- Docker: поддержка контейнеризации через Docker Compose.

## Требования

- Python 3.10 или выше
- Redis
- PostgreSQL
- Docker и Docker Compose (для запуска в контейнерах)
- Ubuntu (для установки и настройки на сервере)

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/Solarmove/aiogram_bot_template.git
cd aiogram_bot_template
```


### 2. Настройка переменных окружения

Скопируйте пример файла окружения и отредактируйте его в соответствии с вашими настройками:

```bash
cp .env.example .env
nano .env
```

Или Vim:

```bash
vim .env
```

Заполните необходимые данные (токен бота, настройки подключения к Redis и Postgres и т.д.).

### 5. Запуск бота

#### Docker Compose (рекомендуется)

Для запуска всех компонентов в Docker-контейнерах:

```bash
docker-compose up --build -d
```

Это запустит бота, PostgreSQL и Redis в отдельных контейнерах с правильной конфигурацией.

Запуск планировщика:

```bash
arq scheduler.main.WorkerSettings
```

#### Автоматический запуск с помощью systemd

В папке systemd находятся примеры unit-файлов для запуска бота и планировщика. Скопируйте файлы в
директорию `/etc/systemd/system/`:

```bash
sudo cp systemd/aiogram_bot.service /etc/systemd/system/
sudo cp systemd/aiogram_scheduler.service /etc/systemd/system/
```

Перезагрузите systemd и запустите сервисы:

```bash
sudo systemctl daemon-reload
sudo systemctl start aiogram_scheduler.service
```

Для автоматического запуска при загрузке системы выполните:

```bash
sudo systemctl enable aiogram_scheduler.service
```

## Структура проекта

```
├── bot/                 # Основной код бота
├── scheduler/           # Код планировщика задач
│   ├── main.py          # Настройки ARQ-воркера
│   └── func.py          # Функции для планировщика
├── systemd/             # Unit-файлы для systemd
├── .env.example         # Пример файла с переменными окружения
├── docker-compose.yml   # Конфигурация Docker Compose
└── README.md            # Документация проекта
```

## Использование Docker

В проект включен файл `docker-compose.yml`, который настраивает три сервиса:

1. **bot** - основной сервис с ботом, собирается из текущего каталога
2. **postgres** - база данных PostgreSQL 15 с сохранением данных в volume
3. **redis** - Redis 7 для кэширования и очередей

Переменные окружения передаются из файла `.env`.

## Использование планировщика (ARQ)

Планировщик задач ARQ настроен в модуле `scheduler`. Для добавления новых задач:

1. Создайте функцию в `scheduler/func.py`
2. Зарегистрируйте её в `WorkerSettings.functions` в `scheduler/main.py`
3. Для периодических задач используйте `WorkerSettings.cron_jobs`

## Использование

- Добавление логики: Расширяйте функциональность бота, добавляя новые хэндлеры и команды в
  директории `bot/`.
- Планировщик: Используйте модуль `scheduler` для выполнения периодических
  задач. ([Документация](https://arq-docs.helpmanual.io/))
- Многоязычность: Добавляйте файлы переводов и используйте встроенную поддержку i18n для локализации
  сообщений.

## Вклад в проект

Если у вас есть идеи или улучшения:

1. Сделайте fork репозитория.
2. Создайте новую ветку для своей функциональности.
3. Отправьте pull request с описанием изменений.