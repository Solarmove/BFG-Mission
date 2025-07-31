from aiogram_dialog.widgets.kbd import (
    Group,
    Start,
    Button,
)
from magic_filter import F

from ..ai_agent_menu_dialogs.states import AIAgentMenu
from ..categories_menu_dialogs.states import CategoryMenu
from ..manage_personal_dialogs.states import ManagePersonalMenu
from ..task_menu_dialogs.states import MyTasks
from ...i18n.utils.i18n_format import I18nFormat
from . import on_clicks

def main_menu_keyboard():
    return Group(
        Button(
            I18nFormat("ai-agent-btn"),
            id="ai_agent",
            on_click=on_clicks.on_ai_agent_click,
            # state=AIAgentMenu.send_query,
            # data={'prompt': 'helper'}
        ),
        Group(
            Start(
                I18nFormat("my-tasks-btn"),
                id="my_tasks",
                state=MyTasks.select_type_tasks,
            ),
            Start(
                I18nFormat("manage-personal-btn"),
                id="manage_personal",
                state=ManagePersonalMenu.select_action,
                when=F["hierarchy_level"].in_([1, 2]),
            ),
            Start(
                I18nFormat("manage-categories-btn"),
                id="manage_categories",
                state=CategoryMenu.select_action,
                when=F["hierarchy_level"].in_([1, 2]),
            ),
            width=2,
        ),
        Button(
            I18nFormat("analytics-btn"),
            id="analytics",
            on_click=on_clicks.on_analytics_click,
        ),
    )
