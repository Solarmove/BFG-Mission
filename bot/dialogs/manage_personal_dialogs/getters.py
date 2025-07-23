from typing import Sequence

from aiogram_dialog import DialogManager  # noqa: F401
from aiogram.types import User

from bot.utils.unitofwork import UnitOfWork
from bot.db.models.models import User as UserModel


async def manage_personal_dialogs_getter(
    dialog_manager: DialogManager, uow: UnitOfWork, event_from_user: User, **kwargs
):
    """
    Get the main menu data for managing personal dialogs.
    """
    personal_list: Sequence[UserModel] = await uow.users.get_all_personal()
    return {
        "personal_amount": len(personal_list),
    }


async def positions_getter(dialog_manager: DialogManager, uow: UnitOfWork, **kwargs):
    return {
        "position_list": [
            ("Директор",),
            ("CEO",),
            ("Асистент СЕО",),
            ("Керуючий",),
            ("HR",),
            ("Головний бухгалтер",),
            ("Бухгалтер",),
            ("Менеджер з продажу",),
            ("Менеджер по флористам",),
            ("Логіст",),
            ("Працівник складу",),
            ("Флорист",),
        ]
    }


async def get_reg_link(dialog_manager: DialogManager, uow: UnitOfWork, **kwargs):
    reg_link = dialog_manager.dialog_data.get("reg_link", "")
    text = (
        "Вас було запрошено зареєструватися в боті.\n\n"
        "Для цього перейдіть за посиланням нижче:"
    )
    return {
        "share_reg_link": f"https://t.me/share/url?url={reg_link}&text={text}",
        "reg_link": dialog_manager.dialog_data.get("reg_link", ""),
    }