from aiogram_dialog import DialogManager  # noqa: F401
from aiogram.types import User  # noqa: F401

from bot.utils.unitofwork import UnitOfWork


async def category_menu_getter(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    **kwargs: dict,
):
    categories = await uow.task_categories.find_all()
    return {
        "categories": "\n".join(
            [f" - {category.name}" for category in categories if categories]
        )
        if categories
        else "Категорій немає",
    }


async def categories_getter(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    **kwargs: dict,
):
    categories = await uow.task_categories.find_all()
    return {
        "categories": [
            (category.id, category.name) for category in categories if categories
        ]
    }


async def get_edited_category_getter(dialog_manager: DialogManager, **kwargs):
    return {
        "category_name": dialog_manager.dialog_data["new_name"],
    }

async def get_category_for_delete(dialog_manager: DialogManager, **kwargs):
    return {
        "category_name": dialog_manager.dialog_data["category_name"],
    }
