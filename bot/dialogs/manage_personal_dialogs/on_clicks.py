import logging
import os.path
from contextlib import suppress

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.deep_linking import create_start_link
from aiogram_i18n import I18nContext

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager, ShowMode  # noqa: F401

from ...exceptions.user_exceptions import InvalidCSVFile
from ...keyboards.ai import exit_ai_agent_kb
from ...services.csv_service import parse_work_schedule_csv
from ...states.ai import AIAgentMenu
from ...utils.unitofwork import UnitOfWork

logger = logging.getLogger(__name__)


async def select_position_click(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    position_id = int(item_id)
    bot: Bot = manager.middleware_data["bot"]

    link = await create_start_link(bot, f"position={position_id}", encode=True)
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


async def on_start_ai_agent(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    await manager.done(show_mode=ShowMode.NO_UPDATE)
    state: FSMContext = manager.middleware_data["state"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    await call.message.edit_text(
        i18n.get("ai-agent-work-schedule-text"),
        reply_markup=exit_ai_agent_kb().as_markup(),
    )
    await state.set_state(AIAgentMenu.send_query)
    call_data = {
        "message_id": call.message.message_id,
        "inline_message_id": call.inline_message_id,
    }
    await state.set_data({"prompt": "work_schedule_prompt", "call_data": call_data})