import datetime
import logging

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_i18n import I18nContext

from ...db.models.models import Task
from ...entities.shared import TaskReadExtended
from ...services.mailing_service import send_message
from ...utils.enum import TaskStatus
from ...utils.misc import humanize_timedelta
from ...utils.unitofwork import UnitOfWork
from . import states

logger = logging.getLogger(__name__)


async def on_select_task_direction_click(
    call: CallbackQuery, widget: Button, manager: DialogManager, item_id: str
):
    manager.dialog_data["task_direction"] = item_id


async def on_select_type_of_task_click(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    task_type = item_id
    manager.dialog_data["task_type"] = task_type
    await manager.next()


async def on_select_task(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    manager.dialog_data["task_id"] = int(item_id)
    await manager.next()


async def on_confirm_task_click(
    call: CallbackQuery, widget: Button, manager: DialogManager
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    bot: Bot = manager.middleware_data["bot"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    start_data = manager.start_data or {}
    task_id = manager.dialog_data.get("task_id", start_data.get("task_id"))

    try:
        await uow.tasks.edit_one(id=task_id, data=dict(status=TaskStatus.IN_PROGRESS))
        await uow.commit()
    except Exception as e:
        logger.info(f"Error while confirming task: {e}")
        await call.answer(i18n.get("task-confirmed-error"))
        return
    task_model_dict: dict = await uow.tasks.get_task_by_id(task_id)
    task_model = TaskReadExtended.model_validate(task_model_dict)
    await send_message(
        bot,
        task_model.creator_id,
        text=i18n.get(
            "task-confirmed-notification",
            task_title=task_model.title,
            executor_full_name=task_model.executor.full_name
            or task_model.executor.full_name_tg,
        ),
    )
    await call.answer(
        i18n.get("task-confirmed-alert", task_title=task_model.title), show_alert=True
    )


async def on_cancel_task_click(
    call: CallbackQuery, widget: Button, manager: DialogManager
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    bot: Bot = manager.middleware_data["bot"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    start_data = manager.start_data or {}
    task_id = manager.dialog_data.get("task_id", start_data.get("task_id"))
    try:
        await uow.tasks.edit_one(id=task_id, data=dict(status=TaskStatus.CANCELED))
        await uow.commit()
    except Exception as e:
        logger.info(f"Error while canceling task: {e}")
        await call.answer(i18n.get("task-canceled-error"))
        return
    task_model_dict: dict = await uow.tasks.get_task_by_id(task_id)
    task_model = TaskReadExtended.model_validate(task_model_dict)
    await send_message(
        bot,
        task_model.executor_id,
        text=i18n.get(
            "task-canceled-notification",
            task_title=task_model.title,
            creator_full_name=task_model.creator.full_name
            or task_model.creator.full_name_tg,
        ),
    )
    await call.answer(
        i18n.get("task-canceled-alert", task_title=task_model.title),
        show_alert=True,
    )


async def on_complete_task_click(
    call: CallbackQuery, widget: Button, manager: DialogManager
):
    start_data = manager.start_data or {}
    await manager.start(
        states.CompleteTask.enter_report_text,
        data={
            "task_id": manager.dialog_data.get("task_id", start_data.get("task_id")),
            "control_point_id": manager.dialog_data.get(
                "control_point_id", start_data.get("control_point_id")
            ),
            "photo_required": manager.dialog_data.get(
                "photo_required", start_data.get("photo_required")
            ),
            "video_required": manager.dialog_data.get(
                "video_required", start_data.get("video_required")
            ),
            "file_required": manager.dialog_data.get(
                "file_required", start_data.get("file_required")
            ),
            "title": manager.dialog_data.get("title", start_data.get("title")),
        },
    )


async def on_select_control_point(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    start_data = manager.start_data or {}
    task_id = manager.dialog_data.get("task_id", start_data.get("task_id"))
    await manager.start(
        states.CompleteTask.enter_report_text,
        data={
            "control_point_id": int(item_id),
            "task_id": task_id,
            "photo_required": manager.dialog_data["photo_required"],
            "video_required": manager.dialog_data["video_required"],
            "file_required": manager.dialog_data["file_required"],
            "title": manager.dialog_data.get("title"),
        },
    )


async def on_enter_report_text(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    message_text: str,
):
    manager.dialog_data["report_text"] = message_text
    await manager.next()


async def on_send_report_media(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
):
    if message.photo:
        media_data = {
            "file_id": message.photo[-1].file_id,
            "file_unique_id": message.photo[-1].file_unique_id,
            "content_type": message.content_type,
        }
    elif message.video:
        media_data = {
            "file_id": message.video.file_id,
            "file_unique_id": message.video.file_unique_id,
            "content_type": message.content_type,
        }
    elif message.document:
        media_data = {
            "file_id": message.document.file_id,
            "file_unique_id": message.document.file_unique_id,
            "content_type": message.content_type,
        }
    else:
        return

    manager.dialog_data.setdefault("report_media_list", []).append(media_data)


async def on_delete_media(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    i18n: I18nContext = manager.middleware_data["i18n"]
    scroll: ManagedScroll = manager.find("report_media_scroll")
    current_page = await scroll.get_page()
    del manager.dialog_data["report_media_list"][current_page]
    await call.answer(
        i18n.get("media-deleted-alert", media_number=current_page + 1),
        show_alert=True,
    )


async def on_done_send_media(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    i18n: I18nContext = manager.middleware_data["i18n"]
    media_list = manager.dialog_data.get("report_media_list", [])

    # Создаем множество типов контента из загруженных медиа для быстрого поиска
    uploaded_content_types = {media["content_type"] for media in media_list}

    # Проверяем каждый требуемый тип медиа
    required_checks = [
        (
            manager.dialog_data.get("photo_required"),
            ContentType.PHOTO,
            "photo-required-error",
        ),
        (
            manager.dialog_data.get("video_required"),
            ContentType.VIDEO,
            "video-required-error",
        ),
        (
            manager.dialog_data.get("file_required"),
            ContentType.DOCUMENT,
            "file-required-error",
        ),
    ]

    for is_required, content_type, error_key in required_checks:
        if is_required and content_type not in uploaded_content_types:
            await call.answer(i18n.get(error_key), show_alert=True)
            return

    # Если все проверки пройдены, переходим к следующему диалогу
    await manager.next()


async def on_confirm_complete_task_click(
    call: CallbackQuery, widget: Button, manager: DialogManager
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    bot: Bot = manager.middleware_data["bot"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    start_data = manager.start_data or {}
    task_id = manager.dialog_data.get("task_id", start_data.get("task_id"))
    control_point_id = manager.start_data.get("control_point_id")
    task_model_dict: dict = await uow.tasks.get_task_by_id(task_id, update_cache=True)
    print(task_id)
    print(task_model_dict)
    task_model = TaskReadExtended.model_validate(task_model_dict)
    report_text = manager.dialog_data.get("report_text", "")
    report_media_list = manager.dialog_data.get("report_media_list", [])
    datetime_complete = datetime.datetime.now()
    is_completed_in_time = datetime_complete <= task_model.end_datetime
    overdue_time = task_model.end_datetime - datetime_complete
    try:
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
        if not control_point_id:
            await uow.tasks.edit_one(
                id=task_id,
                data={
                    "status": TaskStatus.COMPLETED
                    if is_completed_in_time
                    else TaskStatus.OVERDUE,
                    "completed_datetime": datetime_complete,
                },
            )
        else:
            await uow.task_control_points.edit_one(
                id=control_point_id,
                data={"datetime_complete": datetime_complete},
            )
        await uow.commit()
    except Exception as e:
        logger.info(f"Error while completing task: {e}")
        await call.answer(i18n.get("task-completed-error"))
        return
    text_for_creator = (
        i18n.get(
            "task-completed-in-time-notification",
            task_title=task_model.title,
            executor_full_name=task_model.executor.full_name
            or task_model.executor.full_name_tg,
            report_text=report_text,
        )
        if is_completed_in_time
        else i18n.get(
            "task-completed-overdue-notification",
            task_title=task_model.title,
            executor_full_name=task_model.executor.full_name
            or task_model.executor.full_name_tg,
            overdue_time=humanize_timedelta(overdue_time),
            report_text=report_text,
        )
    )
    await send_message(
        bot,
        task_model.creator_id,
        text=text_for_creator,
        media_group=media_group_builder,
    )
    text_for_executor = (
        i18n.get(
            "task-completed-in-time-alert",
            task_title=task_model.title,
        )
        if is_completed_in_time
        else i18n.get(
            "task-completed-overdue-alert",
            task_title=task_model.title,
            overdue_time=humanize_timedelta(overdue_time),
        )
    )
    await call.answer(text_for_executor, show_alert=True)
    await manager.done()