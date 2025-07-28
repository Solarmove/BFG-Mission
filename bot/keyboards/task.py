from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_end_task_kb(task_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text="Завершити завдання",
            callback_data=f"done_task:{task_id}",
        )
    )
    data = kb.as_markup()
    return data


def create_show_task_kb(task_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text="Переглянути завдання",
            callback_data=f"show_task:{task_id}",
        )
    )
    return kb.as_markup()


def create_accept_task_kb(task_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text="Прийняти завдання",
            callback_data=f"accept_task:{task_id}",
        )
    )
    return kb.as_markup()
