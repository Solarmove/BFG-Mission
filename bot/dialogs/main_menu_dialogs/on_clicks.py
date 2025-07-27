from aiogram.types import Message

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager, StartMode  # noqa: F401

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
    if position_model.hierarchy_level == 1:
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
