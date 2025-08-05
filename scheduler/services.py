import datetime
import logging
from typing import Literal

from aiogram import Bot
from aiogram_i18n.cores import FluentRuntimeCore

from bot.db.redis import get_user_locale
from bot.entities.shared import TaskReadExtended
from bot.keyboards.task import create_show_task_kb, create_end_task_kb
from bot.services.mailing_service import send_message
from bot.utils.enum import TaskStatus
from configreader import KYIV

logger = logging.getLogger(__name__)


async def send_task_ending_soon_notification(
    task_model_extended: TaskReadExtended,
    core: FluentRuntimeCore,
    bot: Bot,
):
    if task_model_extended.status != TaskStatus.IN_PROGRESS:
        logger.info(f"Unnecessary notification for task {task_model_extended.id} ")
        return
    locale = await get_user_locale(task_model_extended.executor_id)
    message_text = core.get(
        "task_ending_soon_executor_notification",
        locale,
        task_title=task_model_extended.title,
    )
    datetime_now = datetime.datetime.now(KYIV)
    forecast_task_date = task_model_extended.end_datetime.replace(
        tzinfo=KYIV
    ) - datetime.timedelta(minutes=30)

    if forecast_task_date.date() != datetime_now.date():
        logger.info(
            f"Task {task_model_extended.id} end time is in the past, skipping notification."
        )
        return
    if forecast_task_date.time().hour != datetime_now.hour:
        logger.info(
            f"Task {task_model_extended.id} end time is not in the current hour, skipping notification."
        )
        return
    if forecast_task_date.time().minute != datetime_now.minute:
        logger.info(
            f"Task {task_model_extended.id} end time is not in the current minute, skipping notification."
        )
        return
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
):
    datetime_now = datetime.datetime.now(KYIV)
    forecast_task_date = task_model_extended.end_datetime.replace(tzinfo=KYIV)

    if forecast_task_date.date() != datetime_now.date():
        logger.info(
            f"Task {task_model_extended.id} end time is in the past, skipping notification."
        )
        return
    if forecast_task_date.time().hour != datetime_now.hour:
        logger.info(
            f"Task {task_model_extended.id} end time is not in the current hour, skipping notification."
        )
        return
    if forecast_task_date.time().minute != datetime_now.minute:
        logger.info(
            f"Task {task_model_extended.id} end time is not in the current minute, skipping notification."
        )
        return

    executor_full_name = "Без виконавця"
    if task_model_extended.executor:
        executor_full_name = (
            task_model_extended.executor.full_name
            or task_model_extended.executor.full_name_tg
        )
    if task_model_extended.status in [
        TaskStatus.OVERDUE,
        TaskStatus.COMPLETED,
        TaskStatus.CANCELED,
    ]:
        logger.info(f"Unnecessary notification for task {task_model_extended.id} ")
        return

    text_mapper = {
        "creator": "task_overdue_creator_notification",
        "executor": "task_overdue_executor_notification",
    }
    kwargs_dict = {
        "creator": {
            "executor_full_name": executor_full_name,
            "task_title": task_model_extended.title,
        },
        "executor": {
            "task_title": task_model_extended.title,
        },
    }
    user_id_mapper = {
        "creator": task_model_extended.creator_id,
        "executor": task_model_extended.executor_id,
    }
    message_text = core.get(
        text_mapper[notification_for],
        locale,
        **kwargs_dict[notification_for],
    )

    await send_message(
        bot,
        user_id_mapper[notification_for],
        message_text,
        reply_markup=create_show_task_kb(task_id=task_model_extended.id),
    )


async def send_task_started_notification(
    task_model_extended: TaskReadExtended,
    core: FluentRuntimeCore,
    bot: Bot,
):
    datetime_now = datetime.datetime.now(KYIV)
    forecast_job_date = task_model_extended.start_datetime.replace(tzinfo=KYIV)

    if forecast_job_date.date() != datetime_now.date():
        logger.info(
            f"Task {task_model_extended.id} end time is in the past, skipping notification."
        )
        return
    if forecast_job_date.time().hour != datetime_now.hour:
        logger.info(
            f"Task {task_model_extended.id} end time is not in the current hour, skipping notification."
        )
        return
    if forecast_job_date.time().minute != datetime_now.minute:
        logger.info(
            f"Task {task_model_extended.id} end time is not in the current minute, skipping notification."
        )
        return
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


async def send_task_created_notification(
    task_model_extended: TaskReadExtended,
    core: FluentRuntimeCore,
    bot: Bot,
):
    user_id = task_model_extended.executor_id
    locale = await get_user_locale(user_id)
    creator_name = "Без творця"
    executor_name = "Без виконавця"
    if task_model_extended.creator:
        creator_name = (
            task_model_extended.creator.full_name
            or task_model_extended.creator.full_name_tg
        )
    if task_model_extended.executor:
        executor_name = (
            task_model_extended.executor.full_name
            or task_model_extended.executor.full_name_tg
        )
    message_text = core.get(
        "task_created_notification",
        locale,
        task_title=task_model_extended.title,
        task_category=task_model_extended.category.name
        if task_model_extended.category
        else "Без категорії",
        task_creator=creator_name,
        task_executor=executor_name,
        task_start_datetime=task_model_extended.start_datetime.strftime(
            "%Y-%m-%d %H:%M"
        ),
        task_end_datetime=task_model_extended.end_datetime.strftime("%Y-%m-%d %H:%M"),
        control_points="".join(
            [
                f"\n{cp.description} - {cp.deadline.strftime('%Y-%m-%d %H:%M')}"
                for cp in task_model_extended.control_points
            ]
        )
        if task_model_extended.control_points
        else "Немає",
        task_photo_required="Так" if task_model_extended.photo_required else "Ні",
        task_video_required="Так" if task_model_extended.video_required else "Ні",
        task_file_required="Так" if task_model_extended.file_required else "Ні",
    )
    await send_message(
        bot,
        user_id,
        message_text,
        reply_markup=create_show_task_kb(task_id=task_model_extended.id),
    )
