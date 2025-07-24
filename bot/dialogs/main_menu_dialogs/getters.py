from aiogram_dialog import DialogManager  # noqa: F401
from aiogram.types import User  # noqa: F401

from bot.utils.consts import get_positions_titles
from bot.utils.unitofwork import UnitOfWork
from bot.db.models.models import User as UserModel


async def positions_getter(dialog_manager: DialogManager, **kwargs):
    """
    Get the titles of positions based on the user's hierarchy level.
    """
    hierarchy_level = dialog_manager.start_data.get("hierarchy_level")
    return {"positions": get_positions_titles(hierarchy_level)}


async def main_menu_getter(
    dialog_manager: DialogManager, uow: UnitOfWork, event_from_user: User, **kwargs
):
    """
    Get the main menu data for the user.
    """
    user_model: UserModel = await uow.users.find_one(id=event_from_user.id)

    return {
        "full_name": user_model.full_name,
        "position_title": user_model.position_title,
        "hierarchy_level": user_model.hierarchy_level,
    }
