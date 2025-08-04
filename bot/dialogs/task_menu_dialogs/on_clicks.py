import datetime
import logging

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_i18n import I18nContext

from configreader import KYIV
from ...db.models.models import TaskControlPoints
from ...entities.shared import TaskReadExtended
from ...keyboards.ai import exit_ai_agent_kb
from ...services.log_service import LogService
from ...services.mailing_service import send_message
from ...services.task_services import (
    _create_task_report,
    _complete_control_point,
    _complete_task,
    _handle_completion_error,
    _send_completion_notifications,
    _log_completion,
    is_completed_in_time_func,
    get_overdue_time,
)
from ...states.ai import AIAgentMenu
from ...utils.enum import TaskStatus
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
    channel_log: LogService = manager.middleware_data.get("channel_log")
    start_data = manager.start_data or {}
    task_id = manager.dialog_data.get("task_id", start_data.get("task_id"))
    task_model = await uow.tasks.find_one(id=task_id)
    if task_model.status != TaskStatus.NEW:
        await call.answer(
            i18n.get("task-already-confirmed-or-canceled"), show_alert=True
        )
        return
    try:
        await uow.tasks.edit_one(id=task_id, data=dict(status=TaskStatus.IN_PROGRESS))
        await uow.commit()
    except Exception as e:
        logger.info(f"Error while confirming task: {e}")
        await channel_log.error(
            "Помилка при підтвердженні завдання",
            extra_info={
                "ID завдання": task_id,
                "Помилка": f"<blockquote>{e}</blockquote>",
                "Користувач": call.from_user.full_name,
                "Username": f"@{call.from_user.username}"
                if call.from_user.username
                else "Немає",
            },
        )
        await call.answer(i18n.get("task-confirmed-error"))
        return
    task_model_dict: dict = await uow.tasks.get_task_by_id(task_id, update_cache=True)
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
    task_model.end_datetime = task_model.end_datetime.replace(tzinfo=KYIV)
    await channel_log.info(
        "Користувач підтвердив завдання",
        extra_info={
            "Завдання": task_model.title,
            "Дедлайн": task_model.end_datetime.strftime("%Y-%m-%d %H:%M"),
            "Виконавець": task_model.executor.full_name
            or task_model.executor.full_name_tg,
            "Хто створив": task_model.creator.full_name
            or task_model.creator.full_name_tg,
        },
    )


async def on_cancel_task_click(
    call: CallbackQuery, widget: Button, manager: DialogManager
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    bot: Bot = manager.middleware_data["bot"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    channel_log: LogService = manager.middleware_data.get("channel_log")
    start_data = manager.start_data or {}
    task_id = manager.dialog_data.get("task_id", start_data.get("task_id"))
    try:
        await uow.tasks.edit_one(id=task_id, data=dict(status=TaskStatus.CANCELED))
        await uow.commit()
    except Exception as e:
        logger.info(f"Error while canceling task: {e}")
        await call.answer(i18n.get("task-canceled-error"))
        await channel_log.error(
            "Помилка при скасуванні завдання",
            extra_info={
                "ID завдання": task_id,
                "Помилка": f"<blockquote>{e}</blockquote>",
                "Користувач": call.from_user.full_name,
                "Username": f"@{call.from_user.username}"
                if call.from_user.username
                else "Немає",
            },
        )
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
    task_model.end_datetime = task_model.end_datetime.replace(tzinfo=KYIV)
    await channel_log.info(
        "Користувач скасував завдання",
        extra_info={
            "Завдання": task_model.title,
            "Дедлайн": task_model.end_datetime.strftime("%Y-%m-%d %H:%M"),
            "Виконавець": task_model.executor.full_name
            or task_model.executor.full_name_tg,
            "Хто створив": task_model.creator.full_name
            or task_model.creator.full_name_tg,
        },
    )


async def on_complete_task_click(
    call: CallbackQuery, widget: Button, manager: DialogManager
):
    start_data = manager.start_data or {}
    uow: UnitOfWork = manager.middleware_data["uow"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    task_id = manager.dialog_data.get("task_id", start_data.get("task_id"))
    task_model = await uow.tasks.find_one(id=task_id)
    if task_model.status in [
        TaskStatus.COMPLETED,
        TaskStatus.OVERDUE,
        TaskStatus.CANCELED,
    ]:
        await call.answer(
            i18n.get("task-already-completed-or-canceled"), show_alert=True
        )
        return
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
    uow: UnitOfWork = manager.middleware_data["uow"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    control_point_model: TaskControlPoints = await uow.task_control_points.find_one(
        id=int(item_id)
    )
    if control_point_model.datetime_complete is not None:
        await call.answer(i18n.get("control-point-already-completed"), show_alert=True)
        return
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
    channel_log: LogService = manager.middleware_data.get("channel_log")
    start_data = manager.start_data or {}
    task_id = manager.dialog_data.get("task_id", start_data.get("task_id"))
    control_point_id = manager.start_data.get("control_point_id")
    task_model_dict: dict = await uow.tasks.get_task_by_id(task_id, update_cache=True)
    control_point_model = None
    task_model = TaskReadExtended.model_validate(task_model_dict)
    report_text = manager.dialog_data.get("report_text", "")
    report_media_list = manager.dialog_data.get("report_media_list", [])

    datetime_complete = datetime.datetime.now().replace(tzinfo=KYIV)
    is_control_point = bool(control_point_id)
    if is_control_point:
        control_point_model = await uow.task_control_points.find_one(
            id=control_point_id
        )

    is_completed_in_time = is_completed_in_time_func(
        task_model, datetime_complete, control_point_model
    )
    overdue_time = get_overdue_time(task_model, datetime_complete, control_point_model)

    try:
        # Створюємо звіт
        report_id, media_group_builder = await _create_task_report(
            uow,
            call,
            task_id,
            control_point_id,
            report_text,
            report_media_list,
        )

        # Завершуємо завдання або контрольну точку
        if is_control_point:
            await _complete_control_point(
                uow,
                control_point_id,
                datetime_complete,
            )
        else:
            await _complete_task(
                uow,
                task_id,
                datetime_complete,
                is_completed_in_time,
            )

        await uow.commit()
    except Exception as e:
        await _handle_completion_error(
            call,
            i18n,
            channel_log,
            task_id,
            e,
            is_control_point,
        )
        return

    # Відправляємо сповіщення
    text_for_executor = await _send_completion_notifications(
        bot,
        i18n,
        task_model,
        report_text,
        media_group_builder,
        is_completed_in_time,
        overdue_time,
        is_control_point,
        control_point_model,
    )

    await call.answer(text_for_executor, show_alert=True)

    # Логуємо завершення
    await _log_completion(
        channel_log, task_model, control_point_id, report_text, is_control_point
    )

    await manager.done()


async def on_update_task_click(
    call: CallbackQuery, widget: Button, manager: DialogManager
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    start_data = manager.start_data or {}
    task_id = manager.dialog_data.get("task_id", start_data.get("task_id"))

    await uow.tasks.get_task_by_id(task_id, update_cache=True)
    await call.answer(i18n.get("task-updated-alert"))


async def on_ai_agent_click(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    """
    Handle the click event for the AI Agent button.
    """
    await manager.done(show_mode=ShowMode.NO_UPDATE)
    state: FSMContext = manager.middleware_data["state"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    await call.message.edit_text(
        i18n.get("ai-agent-manage-task-text"),
        reply_markup=exit_ai_agent_kb().as_markup(),
    )
    await state.set_state(AIAgentMenu.send_query)
    call_data = {
        "message_id": call.message.message_id,
        "inline_message_id": call.inline_message_id,
    }
    await state.set_data({"prompt": "manage_task_prompt", "call_data": call_data})
