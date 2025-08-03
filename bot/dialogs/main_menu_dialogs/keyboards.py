from aiogram_dialog.widgets.kbd import (
    Group,
    Start,
    Button,
)
from magic_filter import F

from ..categories_menu_dialogs.states import CategoryMenu

from ..manage_personal_dialogs.states import (
    ManageWorkSchedule,
    CreateRegLink,
)
from ..task_menu_dialogs import states
from ..task_menu_dialogs.states import MyTasks
from ...i18n.utils.i18n_format import I18nFormat
from . import on_clicks


def main_menu_keyboard():
    return Group(
        Button(
            I18nFormat("create-task-btn"),
            id="create_task",
            on_click=on_clicks.on_start_create_task,
        ),
        Group(
            Start(
                I18nFormat("my-tasks-btn"),
                id="my_tasks",
                state=MyTasks.select_type_tasks,
            ),
            Start(
                I18nFormat("work-schedule-btn"),
                id="work_schedule",
                state=ManageWorkSchedule.select_action,
            ),
            Start(
                I18nFormat("create-reg-link-btn"),
                id="create_reg_link",
                state=CreateRegLink.select_position,
                when=F["hierarchy_level"].in_([1, 2]),
            ),
            Start(
                I18nFormat("manage-categories-btn"),
                id="manage_categories",
                state=CategoryMenu.select_action,
                when=F["hierarchy_level"].in_([1, 2]),
            ),
            Button(
                I18nFormat("analytics-btn"),
                id="analytics",
                on_click=on_clicks.on_analytics_click,
            ),
            width=2,
        ),
    )
