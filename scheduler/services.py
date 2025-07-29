import logging
from typing import Literal

from aiogram import Bot
from aiogram_i18n.cores import FluentRuntimeCore

from bot.db.redis import get_user_locale
from bot.entities.shared import TaskReadExtended
from bot.keyboards.task import create_show_task_kb, create_end_task_kb
from bot.services.mailing_service import send_message
from bot.utils.enum import TaskStatus

logger = logging.getLogger(__name__)


async def send_task_ending_soon_notification(
    task_model_extended: TaskReadExtended,
    core: FluentRuntimeCore,
    bot: Bot,
):
    locale = await get_user_locale(task_model_extended.executor_id)
    message_text = core.get(
        "task_ending_soon_executor_notification",
        locale,
        task_title=task_model_extended.title,
    )
    await send_message(
        bot,
        task_model_extended.executor_id,
        message_text,
        reply_markup=create_end_task_kb(task_id=task_model_extended.id),
    )


async def send_task_overdue_notification(
    task_model_extended: TaskReadExtended,
    notification_for: Literal["creator", "executor"],
    locale: str,
    core: FluentRuntimeCore,
    bot: Bot,
    user_id: int,
):
    if task_model_extended.status == TaskStatus.OVERDUE:
        logger.info(f"Unnecessary notification for task {task_model_extended.id} ")
        return

    text_mapper = {
        "creator": "task_overdue_creator_notification",
        "executor": "task_overdue_executor_notification",
    }
    kwargs_dict = {
        "creator": {
            "executor_full_name": task_model_extended.executor.full_name,
            "task_title": task_model_extended.title,
        },
        "executor": {
            "task_title": task_model_extended.title,
        },
    }
    message_text = core.get(
        text_mapper[notification_for],
        locale,
        **kwargs_dict[notification_for],
    )

    await send_message(
        bot,
        user_id,
        message_text,
        reply_markup=create_show_task_kb(task_id=task_model_extended.id),
    )


async def send_task_started_notification(
    task_model_extended: TaskReadExtended,
    core: FluentRuntimeCore,
    bot: Bot,
):
    if task_model_extended.status != TaskStatus.NEW:
        logger.info(f"Unnecessary notification for task {task_model_extended.id} ")
        return
    locale = await get_user_locale(task_model_extended.executor_id)
    message_text = core.get(
        "task_started_now_executor_notification",
        locale,
        task_title=task_model_extended.title,
    )
    await send_message(
        bot,
        task_model_extended.executor_id,
        message_text,
        reply_markup=create_show_task_kb(task_id=task_model_extended.id),
    )


async def send_task_updated_notification(
    task_model_extended: TaskReadExtended,
    core: FluentRuntimeCore,
    bot: Bot,
):
    locale = await get_user_locale(task_model_extended.executor_id)
    message_text = core.get(
        "task_updated_notification",
        locale,
        task_title=task_model_extended.title,
    )
    await send_message(
        bot,
        task_model_extended.executor_id,
        message_text,
        reply_markup=create_show_task_kb(task_id=task_model_extended.id),
    )
