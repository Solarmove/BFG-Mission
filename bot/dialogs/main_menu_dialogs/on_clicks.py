from aiogram.exceptions import TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram_i18n import I18nContext

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager, StartMode, ShowMode  # noqa: F401

from ...db.models.models import Positions
from ...keyboards.ai import exit_ai_agent_kb
from ...states.ai import AIAgentMenu
from ...utils.unitofwork import UnitOfWork


async def on_enter_full_name_click(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    full_name: str,
):
    """
    Handle the click event when the user enters their full name.
    """
    uow: UnitOfWork = manager.middleware_data["uow"]
    position_model: Positions = await uow.positions.find_one(
        id=manager.start_data.get("position_id")
    )
    user_exists = await uow.users.user_exist(message.from_user.id, update_cache=True)
    if user_exists:
        await uow.users.edit_one(
            id=message.from_user.id, data=dict(full_name=full_name)
        )
    else:
        await uow.users.add_one(
            data=dict(
                id=message.from_user.id,
                full_name=full_name,
                full_name_tg=message.from_user.full_name,
                username=message.from_user.username,
                position_id=position_model.id,
            ),
        )
    await uow.commit()
    await manager.start(states.MainMenu.select_action, mode=StartMode.RESET_STACK)


async def on_analytics_click(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    """
    Handle the click event for the Analytics button.
    """
    await manager.done(show_mode=ShowMode.NO_UPDATE)
    state: FSMContext = manager.middleware_data["state"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    await call.message.edit_text(
        i18n.get("ai-agent-analytics-text"),
        reply_markup=exit_ai_agent_kb().as_markup(),
    )
    await state.set_state(AIAgentMenu.send_query)
    call_data = {
        "message_id": call.message.message_id,
        "inline_message_id": call.inline_message_id,
    }
    await state.set_data({"prompt": "analytics_prompt", "call_data": call_data})


async def on_start_create_task(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    await manager.done(show_mode=ShowMode.NO_UPDATE)
    state: FSMContext = manager.middleware_data["state"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    try:
        await call.message.edit_text(
            i18n.get("ai-agent-create-task-text"),
            reply_markup=exit_ai_agent_kb().as_markup(),
        )
    except TelegramRetryAfter:
        await call.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[]])
        )
        await call.message.answer(
            i18n.get("ai-agent-create-task-text"),
            reply_markup=exit_ai_agent_kb().as_markup(),
        )

    await state.set_state(AIAgentMenu.send_query)
    call_data = {
        "message_id": call.message.message_id,
        "inline_message_id": call.inline_message_id,
    }
    await state.set_data({"prompt": "create_task_prompt", "call_data": call_data})
