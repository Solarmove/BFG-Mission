import datetime

from aiogram_dialog import DialogManager  # noqa: F401
from aiogram.types import User  # noqa: F401
from aiogram_i18n import I18nContext

from bot.utils.consts import get_positions_titles
from bot.utils.unitofwork import UnitOfWork
from bot.db.models.models import User as UserModel, Task


async def positions_getter(dialog_manager: DialogManager, **kwargs):
    """
    Get the titles of positions based on the user's hierarchy level.
    """
    hierarchy_level = dialog_manager.start_data.get("hierarchy_level")
    return {"positions": get_positions_titles(hierarchy_level)}


async def main_menu_getter(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    event_from_user: User,
    i18n: I18nContext,
    **kwargs,
):
    """
    Get the main menu data for the user.
    """
    user_model: UserModel = await uow.users.get_user_by_id(user_id=event_from_user.id)
    current_task_text = ""

    if user_model.position.hierarchy_level.level > 1:
        current_tasks: list[Task] = await uow.tasks.get_task_in_work(user_model.id)
        current_task_text = ""
        if current_tasks:
            current_task_text += i18n.get("task_in_work")
            for task in current_tasks:
                current_task_text += i18n.get(
                    "task_data_text",
                    task_title=task.title,
                    task_deadline=task.end_datetime.strftime("%d.%m.%Y, %H:%M"),
                )
    return {
        "datetime_now": datetime.datetime.now(),
        "full_name": user_model.full_name or user_model.full_name_tg,
        "username": user_model.username,
        "position": user_model.position.title,
        "hierarchy_level": user_model.position.hierarchy_level.level,
        "current_task": current_task_text,
    }
