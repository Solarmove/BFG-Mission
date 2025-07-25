from aiogram.types import CallbackQuery

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager  # noqa: F401


async def on_select_type_of_task_click(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    task_type = item_id
    manager.dialog_data["task_type"] = task_type
    await manager.next()
