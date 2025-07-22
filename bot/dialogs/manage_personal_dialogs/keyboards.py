from aiogram_dialog.widgets.kbd import (
    Row,
    Group,
    Column,
    ListGroup,
    ScrollingGroup,
    Select,
    Button,
    Cancel,
    Back,
)  # noqa: F401
from aiogram_dialog.widgets.text import Format

from . import on_clicks, states  # noqa: F401
from ...i18n.utils.i18n_format import I18nFormat


def manage_personal_dialogs_keyboard():
    return Group(
        Button(
            I18nFormat("create-reg-link-btn"),
            id="create_reg_link",
            on_click=on_clicks.create_reg_link_click,
        )
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