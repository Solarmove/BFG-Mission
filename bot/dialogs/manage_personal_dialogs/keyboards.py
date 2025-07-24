from aiogram_dialog.widgets.kbd import (
    Group,
    ScrollingGroup,
    Select,
    Start,
)  # noqa: F401
from aiogram_dialog.widgets.text import Format

from . import on_clicks, states  # noqa: F401
from ...i18n.utils.i18n_format import I18nFormat


def manage_personal_dialogs_keyboard():
    return Group(
        Start(
            I18nFormat("create-reg-link-btn"),
            id="create_reg_link",
            state=states.CreateRegLink.select_position,
        ),
        Start(
            I18nFormat("manage-work-schedule-btn"),
            id="manage_work_schedule",
            state=states.ManageWorkSchedule.select_action,
        ),
    )


def select_position_keyboard():
    return ScrollingGroup(
        Select(
            Format("{item[0]}"),
            items="position_list",
            id="select_position",
            on_click=on_clicks.select_position_click,
            item_id_getter=lambda item: item[0],
        ),
        id="select_position_keyboard",
        height=5,
        width=1,
        hide_on_single_page=True,
    )


def manage_work_schedule_keyboard():
    return Group(
        Start(
            I18nFormat("load-schedule-btn"),
            id="load_schedule",
            state=states.ChangeWorkSchedule.select_month,
        ),
        Start(
            I18nFormat("show-schedule-btn"),
            id="show_schedule",
            state=states.ShowSchedule.select_month,
        ),
    )


def select_month_keyboard():
    return ScrollingGroup(
        Select(
            Format("{item[1]}"),
            id="select_month",
            on_click=on_clicks.select_month_click,
            items="months",
            item_id_getter=lambda item: item[0],
        ),
        id="select_month_scroll",
        width=3,
        height=6,
        hide_on_single_page=True,
    )


def select_year_keyboard():
    return ScrollingGroup(
        Select(
            Format("{item[1]}"),
            id="select_year",
            on_click=on_clicks.select_year_click,
            items="years",
            item_id_getter=lambda item: item[0],
        ),
        id="select_year_scoll",
        width=3,
        height=6,
        hide_on_single_page=True,
    )
