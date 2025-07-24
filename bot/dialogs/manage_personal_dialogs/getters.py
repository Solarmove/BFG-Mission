from typing import Sequence
import calendar
import locale

from aiogram.enums import ContentType
from aiogram_dialog import DialogManager  # noqa: F401
from aiogram.types import User
from aiogram_dialog.api.entities import MediaAttachment

from bot.services.csv_service import create_work_schedule_csv
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


async def month_getter(
    dialog_manager: DialogManager, uow: UnitOfWork, event_from_user: User, **kwargs
):
    months_list = [
        "Cічень",
        "Лютий",
        "Березень",
        "Квітень",
        "Травень",
        "Червень",
        "Липень",
        "Серпень",
        "Вересень",
        "Жовтень",
        "Листопад",
        "Грудень",
    ]
    return {"months": [(index + 1, month) for index, month in enumerate(months_list)]}


async def year_getter(
    dialog_manager: DialogManager, uow: UnitOfWork, event_from_user: User, **kwargs
):
    return {"years": [(i, i) for i in range(2025, 2025 + 10)]}


async def excel_file_getter(
    dialog_manager: DialogManager, uow: UnitOfWork, event_from_user: User, **kwargs
):
    users_list = await uow.users.get_all_users_with_schedule()
    current_month = dialog_manager.dialog_data["month"]
    current_year = dialog_manager.dialog_data["year"]
    template_csv_file_path = create_work_schedule_csv(
        users_list, month=current_month, year=current_year
    )
    dialog_manager.dialog_data["path_to_csv_file"] = template_csv_file_path
    return {
        "template_csv_file": MediaAttachment(
            path=template_csv_file_path,
            type=ContentType.DOCUMENT,
        ),
    }


async def load_schedule_data_getter(
    dialog_manager: DialogManager, uow: UnitOfWork, event_from_user: User, **kwargs
):
    load_stat_data = dialog_manager.dialog_data["stat_data"]
    return {
        **load_stat_data,
        "errors_text": "\n -".join(load_stat_data.get("errors", [])),
        "errors_count": len(load_stat_data.get("errors", [])),
    }


async def work_schedule_getter(
    dialog_manager: DialogManager, uow: UnitOfWork, event_from_user: User, **kwargs
):
    user_id = event_from_user.id
    month = dialog_manager.dialog_data["month"]
    year = dialog_manager.dialog_data["year"]
    users = await uow.users.get_all_users_with_schedule()
    path_to_csv_file = create_work_schedule_csv(users, month=month, year=year)

    locale.setlocale(locale.LC_TIME, "uk_UA.UTF-8")
    month_name = calendar.month_name[month].capitalize()

    return {
        "work_schedule_csv_file": MediaAttachment(
            path=path_to_csv_file,
            type=ContentType.DOCUMENT,
        ),
        "month": month_name,
        "year": year,
    }
