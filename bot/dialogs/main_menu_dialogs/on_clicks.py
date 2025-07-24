from aiogram.types import CallbackQuery, Message

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager, StartMode  # noqa: F401

from ..manage_personal_dialogs.states import ManagePersonalMenu
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
    hierarchy_level = manager.start_data.get("hierarchy_level")
    if hierarchy_level == 1:
        await uow.users.edit_one(
            id=message.from_user.id, data=dict(full_name=full_name)
        )
        await uow.commit()
        await manager.start(states.MainMenu.select_action, mode=StartMode.RESET_STACK)
        return
    manager.dialog_data["full_name"] = full_name
    await manager.next()


async def on_select_position_click(
    call: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: str,
):
    """
    Handle the click event when the user selects a position.
    """
    uow: UnitOfWork = manager.middleware_data["uow"]
    hierarchy_level = manager.start_data.get("hierarchy_level")
    position_title = item_id
    await uow.users.add_one(
        data=dict(
            id=call.from_user.id,
            full_name=manager.dialog_data.get("full_name"),
            full_name_tg=call.from_user.full_name,
            username=call.from_user.username,
            position_title=position_title,
            hierarchy_level=hierarchy_level,
        ),
    )
    await uow.commit()

    await manager.start(states.MainMenu.select_action)

