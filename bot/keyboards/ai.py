from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def exit_ai_agent_kb() -> InlineKeyboardBuilder:
    """
    Create a keyboard for exiting the AI agent.
    """
    cancel_kb = InlineKeyboardBuilder()
    cancel_kb.add(InlineKeyboardButton(text="Назад", callback_data="cancel_ai_agent"))
    return cancel_kb
