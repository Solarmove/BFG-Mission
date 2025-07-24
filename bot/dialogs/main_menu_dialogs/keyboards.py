from aiogram_dialog.widgets.kbd import (
    Group,
    ScrollingGroup,
    Select,
    Button,
    Start,
)  # noqa: F401
from aiogram_dialog.widgets.text import Format
from magic_filter import F

from . import on_clicks, states  # noqa: F401
from ..ai_agent_menu_dialogs.states import AIAgentMenu
from ..categories_menu_dialogs.states import CategoryMenu
from ..manage_personal_dialogs.states import ManagePersonalMenu
from ...i18n.utils.i18n_format import I18nFormat


def select_position_keyboard():
    return ScrollingGroup(
        Select(
            Format("{item}"),
            id="select_position",
            on_click=on_clicks.on_select_position_click,
            items="positions",
            item_id_getter=lambda item: item,
        ),
        id="select_position_scroll",
        width=1,
        height=6,
        hide_on_single_page=True,
    )


def main_menu_keyboard():
    return Group(
        Start(
            I18nFormat("ai-agent-btn"),
            id="ai_agent",
            state=AIAgentMenu.send_query,
        ),
        Button(
            I18nFormat("my-tasks-btn"),
            id="my_tasks",
            # on_click=on_clicks.my_tasks_click,
            when=F["hierarchy_level"] > 1,
        ),
        Start(
            I18nFormat("manage-personal-btn"),
            id="manage_personal",
            state=ManagePersonalMenu.select_action,
            when=F["hierarchy_level"] == 1,
        ),
        Start(
            I18nFormat("manage-categories-btn"),
            id="manage_categories",
            state=CategoryMenu.select_action,
            when=F["hierarchy_level"] == 1,
        ),
    )
