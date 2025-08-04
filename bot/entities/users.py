import datetime

from pydantic import BaseModel, field_validator

from configreader import KYIV


class HierarchyLevelRead(BaseModel):
    """Модель для читання даних рівня ієрархії користувача з бази даних."""

    id: int
    """Унікальний ідентифікатор рівня ієрархії в базі даних."""
    level: int
    """Назва рівня ієрархії користувача."""
    create_task_prompt: str | None = None
    """Промпт для завдання, який використовується"""
    work_schedule_prompt: str | None = None
    """Промпт для робочого графіку, який використовується"""
    category_prompt: str | None = None
    """Промпт для категорії, який використовується"""
    analytics_prompt: str | None = None
    """Промпт для аналітики, який використовується"""


class PositionRead(BaseModel):
    """Модель для читання даних позиції користувача з бази даних."""

    id: int
    """Унікальний ідентифікатор позиції користувача в базі даних."""
    title: str
    """Назва посади користувача."""
    hierarchy_level_id: int | None = None
    """ID рівня ієрархії, до якого належить позиція користувача."""
    hierarchy_level: HierarchyLevelRead | None = None


class UserRead(BaseModel):
    """Модель для читання даних користувача з бази даних."""

    id: int
    """Унікальний ідентифікатор користувача в базі даних. Часто називаэться `user_id`, 'telegram_id', 'chat_id',."""
    username: str | None = None
    """Ім'я користувача в Telegram. Може бути `None`, якщо користувач не має імені."""
    full_name_tg: str
    """Повне ім'я користувача в Telegram. Використовується для ідентифікації користувача."""
    full_name: str | None = None
    """Повне ім'я користувача. Може бути `None`, якщо користувач не має повного імені."""
    position_id: int | None = None
    """ID категорії користувача. Може бути `None`, якщо користувач не має категорії."""
    position: PositionRead | None = None
    """Дані позиції користувача."""
    created_at: datetime.datetime
    """Дата та час створення користувача. Використовується для відстеження часу реєстрації."""
    updated_at: datetime.datetime
    """Дата та час останнього оновлення користувача. Використовується для відстеження змін у профілі користувача."""

    @field_validator("created_at", "updated_at", mode="before")
    def normalize_to_kyiv(cls, v: datetime) -> datetime:
        if isinstance(v, datetime.datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=KYIV)  # наивное = время в Киеве
            else:
                v = v.astimezone(KYIV)  # приводим к Киеву, если было в другой зоне
        return v


class WorkScheduleRead(BaseModel):
    """Модель для читання даних робочого графіку користувача з бази даних."""

    id: int
    """Унікальний ідентифікатор робочого графіку."""
    user_id: int
    """ID користувача, до якого належить робочий графік."""
    start_time: datetime.time
    """Час початку робочого дня."""
    end_time: datetime.time
    """Час закінчення робочого дня."""
    date: datetime.date

    @field_validator("start_time", "end_time", "date", mode="before")
    def normalize_to_kyiv(cls, v: datetime.datetime) -> datetime:
        if isinstance(v, datetime.datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=KYIV)  # наивное = время в Киеве
            else:
                v = v.astimezone(KYIV)  # приводим к Киеву, если было в другой зоне
        return v



class WorkScheduleUpdate(BaseModel):
    """Модель для оновлення робочого графіку користувача."""

    start_time: datetime.time | None = None
    """Час початку робочого дня. Може бути `None`, якщо не потрібно змінювати."""
    end_time: datetime.time | None = None
    """Час закінчення робочого дня. Може бути `None`, якщо не потрібно змінювати."""
    date: datetime.date | None = None
    """Дата робочого графіку. Може бути `None`, якщо не потрібно змінювати."""

    @field_validator("start_time", "end_time", "date", mode="before")
    def normalize_to_kyiv(cls, v: datetime.datetime) -> datetime:
        if isinstance(v, datetime.datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=KYIV)  # наивное = время в Киеве
            else:
                v = v.astimezone(KYIV)  # приводим к Киеву, если было в другой зоне
        return v



class WorkScheduleCreate(BaseModel):
    """Модель для створення нового робочого графіку користувача."""

    user_id: int
    """ID користувача, для якого створюється робочий графік."""
    start_time: datetime.time
    """Час початку робочого дня."""
    end_time: datetime.time
    """Час закінчення робочого дня."""
    date: datetime.date
    """Дата робочого графіку."""

    @field_validator("start_time", "end_time", "date", mode="before")
    def normalize_to_kyiv(cls, v: datetime.datetime) -> datetime:
        if isinstance(v, datetime.datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=KYIV)  # наивное = время в Киеве
            else:
                v = v.astimezone(KYIV)  # приводим к Киеву, если было в другой зоне
        return v