from aiogram_dialog.widgets.kbd import (
    Group,
    Start,
)
from magic_filter import F

from ...i18n.utils.i18n_format import I18nFormat
from ..ai_agent_menu_dialogs.states import AIAgentMenu
from ..categories_menu_dialogs.states import CategoryMenu
from ..manage_personal_dialogs.states import ManagePersonalMenu
from ..task_menu_dialogs.states import MyTasks


def main_menu_keyboard():
    return Group(
        Start(
            I18nFormat("ai-agent-btn"),
            id="ai_agent",
            state=AIAgentMenu.send_query,
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
                when=F["hierarchy_level"] == 1,
            ),
            Start(
                I18nFormat("manage-categories-btn"),
                id="manage_categories",
                state=CategoryMenu.select_action,
                when=F["hierarchy_level"] == 1,
            ),
            width=2,
        ),
    )
