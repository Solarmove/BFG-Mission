from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.utils.deep_linking import create_start_link

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager  # noqa: F401

from ...utils.consts import positions_map


async def select_position_click(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    position_hierarchy_level = positions_map[item_id]
    bot: Bot = manager.middleware_data["bot"]

    link = await create_start_link(
        bot, f"level={position_hierarchy_level}", encode=True
    )
    manager.dialog_data["reg_link"] = link