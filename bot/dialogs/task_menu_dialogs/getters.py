import datetime

from aiogram_dialog import DialogManager  # noqa: F401
from aiogram.types import User  # noqa: F401

from bot.utils.enum import TaskStatus
from bot.utils.unitofwork import UnitOfWork


async def my_tasks_getter(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    event_from_user: User,
    **kwargs: dict,
):
    task_type = dialog_manager.dialog_data.get("task_type")
    if task_type in ["active", 'new', 'done']:
        task_status_mapper = {
            "active": TaskStatus.IN_PROGRESS,
            "new": TaskStatus.NEW,
            "done": TaskStatus.COMPLETED,
        }
        my_tasks = await uow.tasks.get_all_tasks(
            executor_id=event_from_user.id, status=task_status_mapper[task_type]
        )
    elif task_type == "today":
        my_tasks = await uow.tasks.get_all_tasks(
            executor_id=event_from_user.id,
            start_datetime=datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
            end_datetime=datetime.datetime.now().replace(
                hour=23, minute=59, second=59, microsecond=999999
            ),
        )
    elif task_type == "all":
        my_tasks = await uow.tasks.get_all_tasks(executor_id=event_from_user.id)

    return
