import operator

from aiogram_dialog.widgets.kbd import (
    Row,
    Group,
    ScrollingGroup,
    Select,
    Button,
    Start,
    Checkbox,
)  # noqa: F401
from aiogram_dialog.widgets.text import Format
from magic_filter import F

from . import on_clicks, states  # noqa: F401
from ...i18n.utils.i18n_format import I18nFormat


def create_task_menu_kb():
    return Group(
        Row(
            Button(
                I18nFormat("ai-agent-btn"),
                id="create_task",
                on_click=on_clicks.on_start_create_task,
            ),
            when=F["hierarchy_level"].in_([1, 2]),
        ),
        Row(
            Start(
                I18nFormat("create-one-task-btn"),
                id="create_one_task_btn",
                state=states.CreateSingleTask.enter_task_title,
            ),
            Start(
                I18nFormat("create-regular-tasks-btn"),
                id="create_regular_tasks_btn",
                state=states.CreateRegularTasks.send_csv_file,
            ),
        ),
    )


def select_executor_keyboard():
    return ScrollingGroup(
        Select(
            Format("{item[1]} ({item[2]})"),
            id="select_executor",
            items="executors_list",
            item_id_getter=operator.itemgetter(0),
            on_click=on_clicks.on_select_executor,
            type_factory=int,
        ),
        id="select_executor_scroll",
        width=1,
        height=6,
        hide_on_single_page=True,
    )


def report_media_checkbox():
    return Group(
        Checkbox(
            I18nFormat("need_photo_checkbox_btn"),
            I18nFormat("dont_need_photo_checkbox_btn"),
            id="report_with_photo_required",
            on_click=on_clicks.on_change_photo_required,
        ),
        Checkbox(
            I18nFormat("need_video_checkbox_btn"),
            I18nFormat("dont_need_video_checkbox_btn"),
            id="report_with_video_required",
            on_click=on_clicks.on_change_video_required,
        ),
        Checkbox(
            I18nFormat("need_file_checkbox_btn"),
            I18nFormat("dont_need_file_checkbox_btn"),
            id="report_with_file_required",
            on_click=on_clicks.on_change_file_required,
        ),
    )


def quick_start_times_kb():
    return Group(
        Button(
            I18nFormat("time-start-now-btn"),
            id="start_now",
            on_click=on_clicks.on_select_time_start_now,
            when="show_quick_btn",
        ),
        Button(
            I18nFormat("time-start-15-min-btn"),
            id="quick_time_15m",
            on_click=on_clicks.on_quick_time_15m,
            when="show_quick_btn",
        ),
        Button(
            I18nFormat("time-start-30-min-btn"),
            id="quick_time_30m",
            on_click=on_clicks.on_quick_time_30m,
            when="show_quick_btn",
        ),
        Button(
            I18nFormat("time-start-1-hour-btn"),
            id="quick_time_1h",
            on_click=on_clicks.on_quick_time_1h,
            when="show_quick_btn",
        ),
        Button(
            I18nFormat("time-start-2-hours-btn"),
            id="quick_time_2h",
            on_click=on_clicks.on_quick_time_2h,
            when="show_quick_btn",
        ),
        width=2,
    )


def quick_end_times_kb():
    return Group(
        Button(
            I18nFormat("time-to-schedule-end-btn"),
            id="time-to-schedule-end-btn",
            on_click=on_clicks.on_time_to_schedule_end,
            when="show_quick_btn",
        ),
        width=2,
    )


def delete_control_points_kb():
    return ScrollingGroup(
        Select(
            Format("{item[1]}"),
            id="delete_control_point",
            items="control_points_list",
            item_id_getter=operator.itemgetter(0),
            on_click=on_clicks.on_delete_control_point,
            type_factory=int,
        ),
        id="delete_control_point_scroll",
        hide_on_single_page=True,
        height=6,
        width=1,
    )
