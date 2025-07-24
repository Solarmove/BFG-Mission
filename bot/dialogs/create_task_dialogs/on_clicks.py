import logging

from aiogram.types import CallbackQuery, Message

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager  # noqa: F401

logger = logging.getLogger(__name__)


async def on_select_task_type_click(
    call: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: str,
):
    if item_id == "massive":
        await manager.start(states.MassiveCreateTask.send_excel_file)
    else:
        await manager.start(states.CreateSingleTask.select_user)


async def on_send_excel_file_click(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
):
    if not message.document:
        return
    logger.info(f"File {message.document.file_id} was uploaded")
    logger.info(">>> File name: %s", message.document.file_name)
    logger.info(">>> File size: %s", message.document.file_size)
    logger.info(">>> File mime type: %s", message.document.mime_type)
