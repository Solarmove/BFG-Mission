import operator

from aiogram_dialog.widgets.kbd import (
    Group,
    Select,
    Row,
    Radio,
    ScrollingGroup,
    Button,
    PrevPage,
    CurrentPage,
    NextPage,
)  # noqa: F401
from aiogram_dialog.widgets.text import Format, Const, Text
from magic_filter import F

from . import on_clicks, states  # noqa: F401
from ...i18n.utils.i18n_format import I18nFormat
from ...utils.enum import TaskStatus


def select_type_of_task_keyboard():
    return Group(
        Row(
            Button(
                I18nFormat("ai-agent-btn"),
                id="ai_agent",
                on_click=on_clicks.on_ai_agent_click,
            ),
        ),
        Row(
            Radio(
                unchecked_text=Format("⚪️{item[1]}"),
                checked_text=Format("🔘{item[1]}"),
                id="radio_direction_task",
                items=[
                    ("income", "Вхідні"),
                    ("outcome", "Вихідні"),
                ],
                item_id_getter=operator.itemgetter(0),
                on_click=on_clicks.on_select_task_direction_click,
            ),
        ),
        Group(
            Select(
                Format("{item[1]}"),
                id="select_type_of_task",
                items=[
                    ("active", "В роботі"),
                    ("new", "Нові"),
                    ("done", "Виконані"),
                    ("today", "Сьогоднішні"),
                    ("all", "Всі"),
                ],
                item_id_getter=operator.itemgetter(0),
                on_click=on_clicks.on_select_type_of_task_click,
            ),
            width=2,
        ),
    )


def select_task_keyboard():
    return ScrollingGroup(
        Select(
            Format("{item[1]}"),
            id="select_task",
            items="task_list",
            item_id_getter=operator.itemgetter(0),
            on_click=on_clicks.on_select_task,
        ),
        id="task_scroll",
        width=1,
        height=6,
        hide_on_single_page=True,
    )


def action_with_task_keyboard():
    return Group(
        Button(
            I18nFormat("update-btn"),
            id="update_task",
            on_click=on_clicks.on_update_task_click,
        ),
        Button(
            I18nFormat("cancel-task-btn"),
            id="cancel_task",
            on_click=on_clicks.on_cancel_task_click,
            when=~F["am_i_executor"]
            & F["task_status"].not_in(
                [TaskStatus.CANCELED, TaskStatus.COMPLETED, TaskStatus.OVERDUE]
            ),
        ),
        Button(
            I18nFormat("confirm-btn"),
            id="confirm_task",
            on_click=on_clicks.on_confirm_task_click,
            when="show_accept_task_btn",
        ),
        Button(
            I18nFormat("complete-task-btn"),
            id="complete_task",
            on_click=on_clicks.on_complete_task_click,
            when=F["task_status"].in_([TaskStatus.IN_PROGRESS]) & F["am_i_executor"],
        ),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="complete_control_point",
                items="control_points_list",
                item_id_getter=operator.itemgetter(0),
                on_click=on_clicks.on_select_control_point,
            ),
            id="control_point_scroll",
            width=1,
            height=6,
            hide_on_single_page=True,
            when=F["control_points_list"]
            & F["task_status"].in_([TaskStatus.IN_PROGRESS])
            & F["am_i_executor"],
        ),
    )


def scroll_keyboard(scroll_id: str, custom_text: Text | None = None):
    current_page_text = custom_text or Format("{current_page1}/{pages}")
    return Row(
        PrevPage(
            text=Const("«"),
            scroll=scroll_id,
            when=F["pages"] > 1,
        ),
        CurrentPage(
            text=current_page_text,
            scroll=scroll_id,
            when=F["pages"] > 1,
        ),
        NextPage(
            text=Const("»"),
            scroll=scroll_id,
            when=F["pages"] > 1,
        ),
    )
