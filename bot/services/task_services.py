import datetime
import logging

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram_i18n import I18nContext

from bot.db.models.models import TaskControlPoints
from bot.entities.shared import TaskReadExtended
from bot.services.log_service import LogService
from bot.services.mailing_service import send_message
from bot.utils.enum import TaskStatus
from bot.utils.misc import humanize_timedelta
from bot.utils.unitofwork import UnitOfWork

logger = logging.getLogger(__name__)


async def _create_task_report(
    uow: UnitOfWork,
    call: CallbackQuery,
    task_id: int,
    control_point_id: int | None,
    report_text: str,
    report_media_list: list,
) -> tuple[int, MediaGroupBuilder]:
    """Створює звіт про виконання завдання або контрольної точки"""
    report_id = await uow.task_reports.add_one(
        data=dict(
            user_id=call.from_user.id,
            task_id=task_id,
            task_control_point_id=control_point_id,
            report_text=report_text,
        )
    )

    media_group_builder = MediaGroupBuilder()
    for media in report_media_list:
        if media["content_type"] == ContentType.PHOTO:
            media_group_builder.add_photo(
                media=media["file_id"],
            )
        elif media["content_type"] == ContentType.VIDEO:
            media_group_builder.add_video(
                media=media["file_id"],
            )
        elif media["content_type"] == ContentType.DOCUMENT:
            media_group_builder.add_document(
                media=media["file_id"],
            )
        await uow.task_report_contents.add_one(
            data=dict(
                report_id=report_id,
                file_id=media["file_id"],
                file_unique_id=media["file_unique_id"],
                content_type=media["content_type"],
            )
        )

    return report_id, media_group_builder


async def _complete_task(
    uow: UnitOfWork,
    task_id: int,
    datetime_complete: datetime.datetime,
    is_completed_in_time: bool,
):
    """Завершує завдання"""
    await uow.tasks.edit_one(
        id=task_id,
        data={
            "status": TaskStatus.COMPLETED
            if is_completed_in_time
            else TaskStatus.OVERDUE,
            "completed_datetime": datetime_complete,
        },
    )


async def _complete_control_point(
    uow: UnitOfWork,
    control_point_id: int,
    datetime_complete: datetime.datetime,
):
    """Завершує контрольну точку"""
    await uow.task_control_points.edit_one(
        id=control_point_id,
        data={"datetime_complete": datetime_complete},
    )


async def _send_completion_notifications(
    bot: Bot,
    i18n: I18nContext,
    task_model: TaskReadExtended,
    report_text: str,
    media_group_builder: MediaGroupBuilder,
    is_completed_in_time: bool,
    overdue_time: datetime.timedelta,
    is_control_point: bool,
    control_point_model: TaskControlPoints,
) -> str:
    """Відправляє сповіщення про завершення завдання або контрольної точки"""
    if is_control_point:
        text_for_creator_key = (
            "control-point-completed-in-time-notification"
            if is_completed_in_time
            else "control-point-completed-overdue-notification"
        )
        text_for_executor_key = (
            "control-point-completed-in-time-alert"
            if is_completed_in_time
            else "control-point-completed-overdue-alert"
        )
        i18n_kwargs = dict(
            control_point_description=control_point_model.description,
            task_title=task_model.title,
            executor_full_name=task_model.executor.full_name
            or task_model.executor.full_name_tg,
            report_text=report_text,
        )
        if not is_completed_in_time:
            i18n_kwargs["overdue_time"] = humanize_timedelta(overdue_time)
    else:
        text_for_creator_key = (
            "task-completed-in-time-notification"
            if is_completed_in_time
            else "task-completed-overdue-notification"
        )
        text_for_executor_key = (
            "task-completed-in-time-alert"
            if is_completed_in_time
            else "task-completed-overdue-alert"
        )
        i18n_kwargs = dict(
            task_title=task_model.title,
            executor_full_name=task_model.executor.full_name
            or task_model.executor.full_name_tg,
            report_text=report_text,
        )
        if not is_completed_in_time:
            i18n_kwargs["overdue_time"] = humanize_timedelta(overdue_time)
    text_for_creator = (
        i18n.get(text_for_creator_key, **i18n_kwargs)
        if is_completed_in_time
        else i18n.get(text_for_creator_key, **i18n_kwargs)
    )
    text_for_executor = (
        i18n.get(text_for_executor_key, **i18n_kwargs)
        if is_completed_in_time
        else i18n.get(text_for_executor_key, **i18n_kwargs)
    )

    await send_message(
        bot,
        task_model.creator_id,
        text=text_for_creator,
        media_group=media_group_builder,
    )

    return text_for_executor


async def _log_completion(
    channel_log: LogService,
    task_model: TaskReadExtended,
    control_point_id: int | None,
    report_text: str,
    is_control_point: bool,
):
    """Логує завершення завдання або контрольної точки"""
    log_message = (
        "Користувач завершив контрольну точку"
        if is_control_point
        else "Користувач завершив завдання"
    )

    await channel_log.info(
        log_message,
        extra_info={
            "Завдання": task_model.title,
            "Дедлайн": task_model.end_datetime.strftime("%Y-%m-%d %H:%M"),
            "Виконавець": task_model.executor.full_name
            or task_model.executor.full_name_tg,
            "Хто створив": task_model.creator.full_name
            or task_model.creator.full_name_tg,
            "Контрольна точка ID": control_point_id,
            "Звіт": report_text,
        },
    )


async def _handle_completion_error(
    call: CallbackQuery,
    i18n: I18nContext,
    channel_log: LogService,
    task_id: int,
    error: Exception,
    is_control_point: bool,
):
    """Обробляє помилки при завершенні завдання або контрольної точки"""
    logger.info(
        f"Error while completing {'control point' if is_control_point else 'task'}: {error}"
    )
    await call.answer(i18n.get("task-completed-error"))

    message = (
        "Помилка при завершенні контрольної точки"
        if is_control_point
        else "Помилка при завершенні завдання"
    )

    await channel_log.error(
        message,
        extra_info={
            "ID завдання": task_id,
            "Помилка": f"<blockquote>{error}</blockquote>",
            "Користувач": call.from_user.full_name,
            "Username": f"@{call.from_user.username}"
            if call.from_user.username
            else "Немає",
        },
    )


def is_completed_in_time_func(
    task_model: TaskReadExtended,
    date_complete: datetime.datetime,
    control_point_model: TaskControlPoints | None = None,
) -> bool:
    """Перевіряє, чи завдання або контрольна точка завершено вчасно"""
    if control_point_model:
        return control_point_model.deadline >= date_complete
    return task_model.end_datetime >=date_complete


def get_overdue_time(
    task_model: TaskReadExtended,
    date_complete: datetime.datetime,
    control_point_model: TaskControlPoints | None = None,
) -> datetime.timedelta:
    """Повертає час прострочення завдання або контрольної точки"""
    if control_point_model:
        return control_point_model.deadline - date_complete
    return task_model.end_datetime - date_complete
