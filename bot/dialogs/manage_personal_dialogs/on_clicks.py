import logging
import os.path
from contextlib import suppress

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.utils.deep_linking import create_start_link

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager  # noqa: F401

from ...exceptions.user_exceptions import InvalidCSVFile
from ...services.csv_service import parse_work_schedule_csv
from ...utils.consts import positions_map
from ...utils.unitofwork import UnitOfWork

logger = logging.getLogger(__name__)


async def select_position_click(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    position_hierarchy_level = positions_map[item_id]
    bot: Bot = manager.middleware_data["bot"]

    link = await create_start_link(
        bot, f"level={position_hierarchy_level}", encode=True
    )
    manager.dialog_data["reg_link"] = link
    await manager.next()


async def select_month_click(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    manager.dialog_data["month"] = int(item_id)
    await manager.next()


async def select_year_click(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    manager.dialog_data["year"] = int(item_id)
    await manager.next()


async def on_send_csv_file_click(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    if not message.document:
        return
    if message.document.mime_type != "text/csv":
        return await message.answer("Файл повинен бути .csv файлом.")
    bot: Bot = manager.middleware_data["bot"]
    with suppress(FileNotFoundError):
        os.remove(manager.dialog_data["path_to_csv_file"])
    await bot.download(
        message.document.file_id,
        os.path.join("csv_files", message.document.file_name),
    )
    path_to_file = os.path.join("csv_files", message.document.file_name)
    logger.info(f"File {message.document.file_id} was uploaded")
    logger.info(">>> File name: %s", message.document.file_name)
    logger.info(">>> File size: %s", message.document.file_size)
    logger.info(">>> File mime type: %s", message.document.mime_type)
    try:
        stat_data = await parse_work_schedule_csv(path_to_file, uow)
    except InvalidCSVFile as e:
        return await message.answer(str(e))
    manager.dialog_data["stat_data"] = stat_data
    if stat_data.get("errors"):
        await manager.switch_to(states.ChangeWorkSchedule.error)
    else:
        await manager.switch_to(
            states.ChangeWorkSchedule.done,
        )
    return
