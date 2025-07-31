from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram_i18n import I18nContext

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager, StartMode  # noqa: F401

from ..ai_agent_menu_dialogs.states import AIAgentMenu
from ...db.models.models import Positions
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


async def on_ai_agent_click(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    """
    Handle the click event for the AI Agent button.
    """
    await manager.done()
    state: FSMContext = manager.middleware_data["state"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    await call.message.answer(i18n.get("ai-agent-helper-text"))
    await state.set_state(AIAgentMenu.send_query)
    await state.set_data({"agent_type": "helper"})


async def on_analytics_click(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    """
    Handle the click event for the Analytics button.
    """
    await manager.done()
    state: FSMContext = manager.middleware_data["state"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    await call.message.answer(i18n.get("ai-agent-analytics-text"))
    await state.set_state(AIAgentMenu.send_query)
    await state.set_data({"agent_type": "analytics"})
