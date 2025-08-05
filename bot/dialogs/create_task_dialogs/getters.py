import datetime
from typing import Sequence

from aiogram_dialog import DialogManager  # noqa: F401
from aiogram.types import User
from arq import ArqRedis

from bot.db.models.models import User as UserDB, TaskCategory
from bot.entities.task import TaskCreate, TaskControlPointCreate
from bot.services.ai_agent.tools import TaskTools
from bot.utils.unitofwork import UnitOfWork


async def get_user_hierarchy(
    dialog_manager: DialogManager, event_from_user: User, uow: UnitOfWork, **kwargs
):
    return {
        "hierarchy_level": await uow.users.get_user_hierarchy_level(event_from_user.id)
    }


async def get_start_date_getter(
    dialog_manager: DialogManager, event_from_user: User, uow: UnitOfWork, **kwargs
):
    executor_id = dialog_manager.dialog_data["executor_id"]
    work_dates = await uow.work_schedules.get_all_work_schedule_in_user(
        int(executor_id)
    )
    return {
        "start_date": datetime.datetime.now().date(),
        "work_dates": [work_date.date for work_date in work_dates],
    }


async def get_end_date_getter(
    dialog_manager: DialogManager, event_from_user: User, uow: UnitOfWork, **kwargs
):
    selected_start_date = dialog_manager.dialog_data["selected_start_date"]
    executor_id = dialog_manager.dialog_data["executor_id"]
    dt_selected_start_date = datetime.datetime.strptime(
        selected_start_date, "%Y-%m-%d"
    ).date()
    work_dates = await uow.work_schedules.get_all_work_schedule_in_user(
        int(executor_id), from_date=dt_selected_start_date
    )
    return {
        "start_date": dt_selected_start_date,
        "work_dates": [work_date.date for work_date in work_dates],
    }


async def get_executors_list(
    dialog_manager: DialogManager, event_from_user: User, uow: UnitOfWork, **kwargs
):
    my_hierarchy_level = await uow.users.get_user_hierarchy_level(event_from_user.id)
    executors_list_model: Sequence[UserDB] = await uow.users.get_users_without_me(
        event_from_user.id, my_hierarchy_level
    )
    return {
        "executors_list": [
            (
                executor.id,
                executor.full_name or executor.full_name_tg,
                executor.position.title,
            )
            for executor in executors_list_model
        ]
    }


async def get_categories_list_getter(
    dialog_manager: DialogManager, event_from_user: User, uow: UnitOfWork, **kwargs
):
    categories_list_model: Sequence[
        TaskCategory
    ] = await uow.task_categories.get_all_categories()
    return {
        "categories_list": [
            (category.id, category.name) for category in categories_list_model
        ]
    }


async def save_task_before(
    dialog_manager: DialogManager,
    event_from_user: User,
    uow: UnitOfWork,
    arq: ArqRedis,
    **kwargs,
):
    task_data = dialog_manager.dialog_data
    task_control_points_list = task_data.get("task_control_points", [])
    task_control_points = []
    for task_point in task_control_points_list:
        task_control_points.append(
            TaskControlPointCreate(
                deadline=datetime.datetime.strptime(
                    task_point["deadline"], "%Y-%m-%d %H:%M"
                ),
                description=task_point.get("description", "Контрольна точка"),
            )
        )
    task_model = TaskCreate(
        creator_id=event_from_user.id,
        executor_id=task_data["executor_id"],
        title=task_data["title"],
        description=task_data["description"],
        start_datetime=datetime.datetime.strptime(
            task_data["start_datetime"], "%Y-%m-%d %H:%M"
        ),
        end_datetime=datetime.datetime.strptime(
            task_data["end_datetime"], "%Y-%m-%d %H:%M"
        ),
        category_id=task_data.get("category_id"),
        photo_required=task_data["photo_required"],
        video_required=task_data["video_required"],
        file_required=task_data["file_required"],
        task_control_points=task_control_points,
    )
    task_tools = TaskTools(
        uow=uow,
        arq=arq,
        user_id=event_from_user.id,
    )
    await task_tools.create_one_task_func(task_model)
    task_category = await uow.task_categories.find_one(id=task_model.category_id)
    executor_model: UserDB = await uow.users.find_one(id=task_model.executor_id)
    creator_model: UserDB = await uow.users.find_one(id=task_model.creator_id)
    return {
        "task_title": task_model.title,
        "task_description": task_model.description,
        "task_category": task_category.name if task_category else "Без категорії",
        "task_executor": executor_model.full_name or executor_model.full_name_tg,
        "task_creator": creator_model.full_name or creator_model.full_name_tg,
        "task_start_datetime": f"{task_model.start_datetime:%Y-%m-%d %H:%M}",
        "task_end_datetime": f"{task_model.end_datetime:%Y-%m-%d %H:%M}",
        "task_photo_required": "✅" if task_model.photo_required else "❌",
        "task_video_required": "✅" if task_model.video_required else "❌",
        "task_file_required": "✅" if task_model.file_required else "❌",
        "control_points": "".join(
            f"\n{index + 1}. {cp.description} - {cp.deadline:%Y-%m-%d %H:%M}\n"
            for index, cp in enumerate(task_model.task_control_points)
        ),
    }


async def get_control_point_deadline_date_getter(
    dialog_manager: DialogManager,
    event_from_user: User,
    uow: UnitOfWork,
    **kwargs,
):
    start_data = dialog_manager.start_data
    start_datetime = datetime.datetime.strptime(
        start_data["task_start_datetime"], "%Y-%m-%d %H:%M"
    )
    end_datetime = datetime.datetime.strptime(
        start_data["task_end_datetime"], "%Y-%m-%d %H:%M"
    )
    executor_id = dialog_manager.start_data["executor_id"]
    work_dates = await uow.work_schedules.get_all_work_schedule_in_user(
        int(executor_id), from_date=start_datetime.date(), to_date=end_datetime.date()
    )
    return {
        "start_date": start_datetime.date(),
        "end_date": end_datetime.date(),
        "work_dates": [work_date.date for work_date in work_dates],
    }


async def start_time_getter(
    dialog_manager: DialogManager, event_from_user: User, **kwargs
):
    datetime_now = datetime.datetime.now()
    start_time_date_str = dialog_manager.dialog_data["selected_start_date"]
    start_time_date = datetime.datetime.strptime(start_time_date_str, "%Y-%m-%d").date()
    return {
        "show_quick_btn": True if datetime_now.date() == start_time_date else False,
    }


async def get_control_points(
    dialog_manager: DialogManager,
    event_from_user: User,
    uow: UnitOfWork,
    **kwargs,
):
    control_points_list = dialog_manager.dialog_data.get("task_control_points", [])
    return {
        "task_control_points_text": [
            f"{index}. {cp['description']} - {cp['deadline']}"
            for index, cp in enumerate(control_points_list)
        ],
        "control_points_list": [
            (index, f"🗑️Контрольна точка {index}")
            for index, cp in enumerate(control_points_list)
        ],
    }
