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
    user_model: UserModel = await uow.users.find_one(id=event_from_user.id)
    users_count = None
    users_on_shift = None
    current_task_text = None
    if user_model.hierarchy_level < 4:
        users_count = await uow.users.get_user_from_hierarchy_count(
            user_model.hierarchy_level
        )
        users_on_shift = await uow.work_schedules.get_count_of_users_on_shift()
    if user_model.hierarchy_level > 1:
        current_task: Task = await uow.tasks.get_my_current_task(user_model.id)
        if current_task:
            current_task_text = i18n.get(
                "my_current_task",
                task_title=current_task.title,
                end_datetime=current_task.end_datetime,
            )
    return {
        "datetime_now": datetime.datetime.now(),
        "full_name": user_model.full_name or user_model.full_name_tg,
        "username": user_model.username,
        "position": user_model.position_title,
        "hierarchy_level": user_model.hierarchy_level,
        "users_count": users_count,
        "users_on_shift_count": users_on_shift,
        "current_task": current_task_text,
    }
