from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram_i18n import I18nContext

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager, ShowMode  # noqa: F401

from ...keyboards.ai import exit_ai_agent_kb
from ...states.ai import AIAgentMenu
from ...utils.unitofwork import UnitOfWork


async def on_enter_category_name(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    message_text: str,
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    await uow.task_categories.add_one(dict(name=message_text))
    await uow.commit()
    await message.answer(i18n.get("category-created-text", category_name=message_text))


async def on_select_category(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    manager.dialog_data["category_id"] = int(item_id)
    category_model = await uow.task_categories.find_one(id=int(item_id))
    manager.dialog_data["category_name"] = category_model.title
    await manager.next()


async def on_enter_new_category_name(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    message_text: str,
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    category_id = manager.dialog_data["category_id"]
    manager.dialog_data["new_name"] = message_text
    await uow.task_categories.edit_one(id=category_id, data=dict(name=message_text))
    await uow.commit()
    await manager.next()


async def on_confirm_delete_category(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    await uow.task_categories.delete_one(id=manager.dialog_data["category_id"])
    await uow.commit()
    await manager.next()


async def on_start_ai_agent(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    await manager.done(show_mode=ShowMode.NO_UPDATE)
    state: FSMContext = manager.middleware_data["state"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    await call.message.edit_text(
        i18n.get("ai-agent-categories-text"),
        reply_markup=exit_ai_agent_kb().as_markup(),
    )
    await state.set_state(AIAgentMenu.send_query)
    call_data = {
        "message_id": call.message.message_id,
        "inline_message_id": call.inline_message_id,
    }
    await state.set_data({"prompt": "category_prompt", "call_data": call_data})