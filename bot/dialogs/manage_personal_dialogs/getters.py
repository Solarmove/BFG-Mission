import datetime
import calendar

from aiogram.enums import ContentType
from aiogram_dialog import DialogManager  # noqa: F401
from aiogram.types import User
from aiogram_dialog.api.entities import MediaAttachment

from bot.services.csv_service import create_work_schedule_csv
from bot.utils.unitofwork import UnitOfWork


async def positions_getter(dialog_manager: DialogManager, uow: UnitOfWork, **kwargs):
    positions = await uow.positions.find_all()
    return {
        "position_list": [
            (position.id, position.title) for position in positions if positions
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
    months = []
    for index, month in enumerate(months_list):
        if index + 1 == datetime.datetime.now().month:
            months.append((index + 1, f"[{month}]"))
        else:
            months.append((index + 1, month))
    return {"months": months}


async def year_getter(
    dialog_manager: DialogManager, uow: UnitOfWork, event_from_user: User, **kwargs
):
    years = []
    for year in range(2025, 2025 + 10):
        if year == datetime.datetime.now().year:
            years.append((year, f"[{year}]"))
        else:
            years.append((year, str(year)))
    return {"years": years}


async def excel_file_getter(
    dialog_manager: DialogManager, uow: UnitOfWork, event_from_user: User, **kwargs
):
    current_month = dialog_manager.dialog_data["month"]
    current_year = dialog_manager.dialog_data["year"]
    date_from = datetime.datetime(year=current_year, month=current_month, day=1)
    days_in_month = calendar.monthrange(current_year, current_month)[1]
    date_to = datetime.datetime(
        year=current_year, month=current_month, day=days_in_month
    )

    users = await uow.users.get_all_users_with_schedule(date_from, date_to)
    template_csv_file_path = create_work_schedule_csv(
        users, month=current_month, year=current_year
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
    month = dialog_manager.dialog_data["month"]
    year = dialog_manager.dialog_data["year"]
    date_from = datetime.datetime(year=year, month=month, day=1)
    days_in_month = calendar.monthrange(year, month)[1]
    date_to = datetime.datetime(year=year, month=month, day=days_in_month)

    users = await uow.users.get_all_users_with_schedule(date_from, date_to)
    path_to_csv_file = create_work_schedule_csv(users, month=month, year=year)

    month_name = calendar.month_name[month].capitalize()

    return {
        "work_schedule_csv_file": MediaAttachment(
            path=path_to_csv_file,
            type=ContentType.DOCUMENT,
        ),
        "month": month_name,
        "year": str(year),
    }
