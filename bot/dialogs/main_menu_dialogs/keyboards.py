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
from ..create_task_dialogs.states import CreateTask
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
        # Start(
        #     I18nFormat("create-new-task-btn"),
        #     id="create_new_task",
        #     # state=CreateTask.select_task_type,
        # ),
        Button(
            I18nFormat("my-tasks-btn"),
            id="my_tasks",
            # on_click=on_clicks.my_tasks_click,
        ),
        Button(
            I18nFormat("manage-personal"),
            id="manage_personal",
            on_click=on_clicks.manage_personal_click,
            when=F["hierarchy_level"] == 1,
        ),
    )
