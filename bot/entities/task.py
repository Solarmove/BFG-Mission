import datetime

from pydantic import BaseModel, field_validator

from bot.utils.enum import TaskStatus
from configreader import KYIV


class BaseTaskModel(BaseModel):
    @field_validator(
        "start_datetime",
        "end_datetime",
        "completed_datetime",
        mode="before",
        check_fields=False,
    )
    def normalize_to_kyiv(cls, v: datetime.datetime) -> datetime:
        if isinstance(v, datetime.datetime):
            v = v.replace(tzinfo=KYIV)
        return v



class TaskRead(BaseTaskModel):
    """Модель для читання даних завдання."""

    id: int
    """Унікальний ідентифікатор завдання."""
    creator_id: int
    """ID користувача, який створив завдання."""
    executor_id: int
    """ID користувача, який виконує завдання."""
    title: str
    """Заголовок завдання."""
    description: str | None = None
    """Опис завдання. Може бути None, якщо опис не потрібен."""
    start_datetime: datetime.datetime
    """Дата та час початку завдання."""
    end_datetime: datetime.datetime
    """Дата та час завершення завдання."""
    category_id: int | None = None
    """ID категорії завдання. Може бути None, якщо категорія була видалена."""
    completed_datetime: datetime.datetime | None = None
    """Дата та час завершення коли користувач завершив це завдання. Може бути None, якщо завдання ще не виконано."""
    photo_required: bool = False
    """Чи потрібне фото звіт при виконанні завдання? За замовчуванням False."""
    video_required: bool = False
    """Чи потрібне відео звіт при виконанні завдання? За замовчуванням False."""
    file_required: bool = False
    """Чи потрібен файл звіт при виконанні завдання? За замовчуванням False."""
    status: TaskStatus = TaskStatus.NEW
    """Статус завдання. За замовчуванням NEW."""


class TaskCreate(BaseTaskModel):
    """Модель для створення нового завдання."""

    creator_id: int
    """ID користувача, який створює завдання"""
    executor_id: int
    """ID користувача, який виконує завдання"""
    title: str
    """Заголовок завдання"""
    description: str | None = None
    """Опис завдання. Може бути None, якщо опис не потрібен"""
    start_datetime: datetime.datetime
    """Дата та час початку завдання"""
    end_datetime: datetime.datetime
    """Дата та час завершення завдання"""
    category_id: int | None = None
    """ID категорії завдання. Може бути None, тільки якщо категорія була видалена. 
    Зазвичай повинно бути вказано ID категорії, якщо вона існує"""
    photo_required: bool = False
    """Чи потрібне фото звіт при виконанні завдання? За замовчуванням False"""
    video_required: bool = False
    """Чи потрібне відео звіт при виконанні завдання? За замовчуванням False"""
    file_required: bool = False
    """Чи потрібен файл звіт при виконанні завдання? За замовчуванням False"""
    status: TaskStatus = TaskStatus.NEW
    """Статус завдання. За замовчуванням NEW"""

    task_control_points: list["TaskControlPointCreate"] | None = None

    @field_validator("start_datetime", "end_datetime", mode="before")
    def normalize_to_kyiv(cls, v: datetime.datetime) -> datetime:
        if isinstance(v, datetime.datetime):
            v = v.replace(tzinfo=KYIV)
        return v


class TaskUpdate(BaseTaskModel):
    """Модель для оновлення існуючого завдання."""

    id: int
    title: str | None = None
    """Заголовок завдання. Може бути None, якщо не потрібно змінювати"""
    description: str | None = None
    """Опис завдання. Може бути None, якщо не потрібно змінювати"""
    start_datetime: datetime.datetime | None = None
    """Дата та час початку завдання. Може бути None, якщо не потрібно змінювати"""
    end_datetime: datetime.datetime | None = None
    """Дата та час завершення завдання. Може бути None, якщо не потрібно змінювати"""
    category_id: int | None = None
    """ID категорії завдання. Може бути None, якщо не потрібно змінювати"""
    photo_required: bool | None = False
    """Чи потрібне фото звіт при виконанні завдання? За замовчуванням False"""
    video_required: bool | None = False
    """Чи потрібне відео звіт при виконанні завдання? За замовчуванням False"""
    file_required: bool | None = False
    """Чи потрібен файл звіт при виконанні завдання? За замовчуванням False"""

    @field_validator("start_datetime", "end_datetime", mode="before")
    def normalize_to_kyiv(cls, v: datetime.datetime) -> datetime:
        if isinstance(v, datetime.datetime):
            v = v.replace(tzinfo=KYIV)
        return v



class TaskControlPointRead(BaseModel):
    """Модель для читання контрольної точки звіту завдання.
    Тобто виконавець в цій точці зможе відзвітувати про прогрес виконання завдання (якщо це передбачено)"""

    id: int
    task_id: int
    deadline: datetime.datetime
    datetime_complete: datetime.datetime | None = None
    description: str | None = None

    @field_validator("datetime_complete", "deadline", mode="before")
    def normalize_to_kyiv(cls, v: datetime.datetime) -> datetime:
        if isinstance(v, datetime.datetime):
            v = v.replace(tzinfo=KYIV)
        return v



class TaskControlPointCreate(BaseModel):
    """Модель для створення контрольної точки звіту завдання.
    Тобто виконавець в цій точці зможе відзвітувати про прогрес виконання завдання (якщо це передбачено)"""

    deadline: datetime.datetime
    """Дата та час дедлайну контрольної точки звіту"""
    description: str
    """Опис контрольної точки звіту, що повинно бути зроблено або будь які інші деталі, які потрібно врахувати при звіті"""

    @field_validator("deadline", mode="before")
    def normalize_to_kyiv(cls, v: datetime.datetime) -> datetime:
        if isinstance(v, datetime.datetime):
            v = v.replace(tzinfo=KYIV)
        return v



class TaskCategoryRead(BaseModel):
    """Модель для читання категорії завдання."""

    id: int
    """Унікальний ідентифікатор категорії завдання."""
    name: str
    """Назва категорії завдання."""


class TaskCategoryCreate(BaseModel):
    """Модель для створення нової категорії завдання."""

    name: str
    """Назва категорії завдання. Необхідно для створення нової категорії."""


class TaskCategoryUpdate(BaseModel):
    """Модель для оновлення категорії завдання."""

    name: str
    """Нова назва категорії завдання. Необхідно для оновлення існуючої категорії."""
