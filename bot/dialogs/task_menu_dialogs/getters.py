import datetime
from pprint import pprint

from aiogram.types import User  # noqa: F401
from aiogram_dialog import DialogManager  # noqa: F401
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.kbd import ManagedRadio
from aiogram_i18n import I18nContext

from bot.db.models.models import TaskControlPoints
from bot.entities.shared import TaskReadExtended
from bot.entities.task import TaskRead
from bot.utils.enum import TaskStatus
from bot.utils.misc import is_task_hot
from bot.utils.unitofwork import UnitOfWork
from configreader import KYIV


async def get_selected_type_of_task(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    event_from_user: User,
    i18n: I18nContext,
    **kwargs: dict,
):
    if dialog_manager.dialog_data.get("task_direction") is None:
        widget: ManagedRadio = dialog_manager.find("radio_direction_task")
        await widget.set_checked("income")

    task_type = dialog_manager.dialog_data.get("task_type")
    direction_mapper = {
        "income": "Вхідні",
        "outcome": "Вихідні",
    }
    task_type_mapper = {
        "active": "В роботі",
        "new": "Нові",
        "done": "Виконані",
        "today": "Сьогоднішні",
        "all": "Всі",
        None: "Всі",
    }
    task_direction = direction_mapper[
        dialog_manager.dialog_data.get("task_direction", "income")
    ]
    task_type_text = task_type_mapper[task_type]
    return {
        "task_type": task_type_text,
        "task_direction": task_direction,
    }


async def my_tasks_getter(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    event_from_user: User,
    i18n: I18nContext,
    **kwargs: dict,
):
    task_type = dialog_manager.dialog_data.get("task_type")
    task_direction = dialog_manager.dialog_data.get("task_direction", "income")
    if task_direction == "outcome":
        creator_id = event_from_user.id
        executor_id = None
        date_find_to = None
    else:
        creator_id = None
        executor_id = event_from_user.id
        date_find_to = datetime.datetime.now().date()
    task_find_filter = dict(
        executor_id=executor_id,
        creator_id=creator_id,
        date_find_to=date_find_to,
        without_task_status=[TaskStatus.CANCELED],
    )
    if task_type in ["active", "new", "done"]:
        task_status_mapper = {
            "active": TaskStatus.IN_PROGRESS,
            "new": TaskStatus.NEW,
            "done": TaskStatus.COMPLETED,
        }

        task_find_filter = dict(
            executor_id=executor_id,
            creator_id=creator_id,
            status=task_status_mapper[task_type],
            date_find_to=date_find_to,
            without_task_status=[TaskStatus.CANCELED],
        )
    elif task_type == "today":
        task_find_filter = dict(
            executor_id=executor_id,
            creator_id=creator_id,
            start_datetime=datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=KYIV
            ),
            end_datetime=datetime.datetime.now().replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=KYIV
            ),
            date_find_to=date_find_to,
            without_task_status=[TaskStatus.CANCELED],
        )

    elif task_type == "all":
        task_find_filter = dict(
            executor_id=executor_id,
            creator_id=creator_id,
            date_find_to=date_find_to,
            without_task_status=[TaskStatus.CANCELED],
        )

    my_tasks = await uow.tasks.get_all_task_simple(**task_find_filter)
    my_tasks = [TaskRead.model_validate(task) for task in my_tasks]
    task_status_mapper = {
        TaskStatus.IN_PROGRESS: i18n.get("task-status-in-progress-emoji"),
        TaskStatus.NEW: i18n.get("task-status-new-emoji"),
        TaskStatus.COMPLETED: i18n.get("task-status-completed-emoji"),
        TaskStatus.CANCELED: i18n.get("task-status-canceled-emoji"),
        TaskStatus.OVERDUE: i18n.get("task-status-overdue-emoji"),
    }
    user_level = await uow.users.get_user_hierarchy_level(event_from_user.id)
    return {
        "show_ai": user_level <= 3,
        "task_list": [
            (
                task.id,
                f"{'🔥' if is_task_hot(task.end_datetime) else ''}"
                f"{task_status_mapper.get(task.status, '')} {task.title} ",
            )
            for task in my_tasks
        ],
        **await get_selected_type_of_task(
            dialog_manager, uow, event_from_user, i18n, **kwargs
        ),
    }


def show_task_accept_btn(task: TaskReadExtended, user_id: int) -> bool:
    if task.status != TaskStatus.NEW:
        return False
    if task.executor_id != user_id:
        return False
    if task.start_datetime > datetime.datetime.now(KYIV):
        return False
    return True


async def get_task(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    event_from_user: User,
    i18n: I18nContext,
    **kwargs: dict,
):
    report_content_list = []
    report_text_list = []
    start_data = dialog_manager.start_data or {}
    task_id = dialog_manager.dialog_data.get("task_id", start_data.get("task_id"))
    task_dict = await uow.tasks.get_task_by_id(task_id, update_cache=True)
    task = TaskReadExtended.model_validate(task_dict)
    if task.reports:
        for report in task.reports:
            report_content_model = await uow.task_report_contents.find_all(
                report_id=report.id
            )
            report_text_list.append(report.report_text)
            for content in report_content_model:
                report_content_list.append(
                    MediaAttachment(
                        file_id=MediaId(
                            file_id=content.file_id,
                            file_unique_id=content.file_unique_id,
                        ),
                        type=content.content_type,
                    )
                )  # Append the report itself to the content list

    task_emoji_status_mapper = {
        TaskStatus.IN_PROGRESS: i18n.get("task-status-in-progress-emoji"),
        TaskStatus.NEW: i18n.get("task-status-new-emoji"),
        TaskStatus.COMPLETED: i18n.get("task-status-completed-emoji"),
        TaskStatus.CANCELED: i18n.get("task-status-canceled-emoji"),
        TaskStatus.OVERDUE: i18n.get("task-status-overdue-emoji"),
    }
    task_status_mapper = {
        TaskStatus.IN_PROGRESS: i18n.get("task-status-in-progress"),
        TaskStatus.NEW: i18n.get("task-status-new"),
        TaskStatus.COMPLETED: i18n.get("task-status-completed"),
        TaskStatus.CANCELED: i18n.get("task-status-canceled"),
        TaskStatus.OVERDUE: i18n.get("task-status-overdue"),
    }
    dialog_manager.dialog_data["photo_required"] = task.photo_required
    dialog_manager.dialog_data["video_required"] = task.video_required
    dialog_manager.dialog_data["file_required"] = task.file_required
    dialog_manager.dialog_data["title"] = task.title
    pprint(task)
    data = {
        "report_media_list": report_content_list,
        "report_texts": "\n".join(
            [
                f"<blockquote>{index + 1}. {report_text}</blockquote>"
                for index, report_text in enumerate(report_text_list)
            ]
        )
        if report_text_list
        else i18n.get("task-no-reports"),
        "task_title": task.title,
        "task_description": task.description or i18n.get("task-no-description"),
        "task_start_datetime": task.start_datetime.strftime("%d.%m.%Y, %H:%M"),
        "task_end_datetime": task.end_datetime.strftime("%d.%m.%Y, %H:%M"),
        "task_category": task.category.name
        if task.category
        else i18n.get("task-no-category"),
        "task_photo_required": i18n.get("task-photo-required-yes")
        if task.photo_required
        else i18n.get("task-photo-required-no"),
        "task_video_required": i18n.get("task-video-required-yes")
        if task.video_required
        else i18n.get("task-video-required-no"),
        "task_file_required": i18n.get("task-file-required-yes")
        if task.file_required
        else i18n.get("task-file-required-no"),
        "task_creator": task.creator.full_name or task.creator.full_name_tg,
        "task_executor": task.executor.full_name or task.executor.full_name_tg,
        "task_completed_datetime": (
            task.completed_datetime.strftime("%d.%m.%Y, %H:%M")
            if task.completed_datetime
            else i18n.get("task-not-completed")
        ),
        "control_points": "\n".join(
            f'▶️ {index + 1}. "{cp.description}"\n'
            f"<b>Дедлайн</b>: <i>{cp.deadline.strftime('%d.%m.%Y, %H:%M')}</i>\n"
            f"<b>Виконано:</b> {cp.datetime_complete.strftime('%d.%m.%Y, %H:%M') if cp.datetime_complete else i18n.get('control-point-not-completed')}"
            for index, cp in enumerate(task.control_points)
        )
        if task.control_points
        else i18n.get("task-no-control-points"),
        "task_status_emoji": task_emoji_status_mapper[task.status],
        "task_status_text": task_status_mapper[task.status],
        "task_status": task.status,
        "is_task_hot": "🔥" if is_task_hot(task.end_datetime) else "",
        "am_i_executor": task.executor_id == event_from_user.id,
        "control_points_list": [
            (cp.id, f'Завершити "{cp.description[:20]}"')
            for index, cp in enumerate(task.control_points)
            if cp.datetime_complete is None
        ]
        if task.control_points
        else [],
        "show_accept_task_btn": show_task_accept_btn(task, event_from_user.id),
    }
    return data


async def get_sent_media(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    event_from_user: User,
    i18n: I18nContext,
    **kwargs: dict,
):
    scroll: ManagedScroll = dialog_manager.find("report_media_scroll")
    current_page = await scroll.get_page()
    return {
        "report_media_list": [
            MediaAttachment(
                file_id=MediaId(
                    file_id=media["file_id"],
                    file_unique_id=media["file_unique_id"],
                ),
                type=media["content_type"],
            )
            for media in dialog_manager.dialog_data.get("report_media_list", [])
        ],
        "pages": len(dialog_manager.dialog_data.get("report_media_list", [])),
        "delete_media": i18n.get("delete-media-btn", media_number=current_page + 1),
        "can_skip": dialog_manager.start_data["photo_required"] is False
        and dialog_manager.start_data["video_required"] is False
        and dialog_manager.start_data["file_required"] is False,
    }


async def get_task_before_complete(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    event_from_user: User,
    i18n: I18nContext,
    **kwargs: dict,
):
    control_point_description = None
    if dialog_manager.start_data.get("control_point_id", False):
        control_point: TaskControlPoints = await uow.task_control_points.find_one(
            id=dialog_manager.start_data["control_point_id"]
        )
        control_point_description = control_point.description
    return {
        "task_title": dialog_manager.start_data["title"],
        "control_point_description": control_point_description,
        "control_point_exist": True
        if dialog_manager.start_data.get("control_point_id", False)
        else False,
    }
