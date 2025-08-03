import operator

from aiogram_dialog.widgets.kbd import (
    Row,
    Group,
    Column,
    ScrollingGroup,
    Select,
    Start,
    Button,
)  # noqa: F401
from aiogram_dialog.widgets.text import Format

from . import on_clicks, states  # noqa: F401
from ...i18n.utils.i18n_format import I18nFormat


def category_menu_keyboard():
    return Group(
        Column(
            Button(
                I18nFormat("ai-agent-btn"),
                id="ai_agent_category",
                on_click=on_clicks.on_start_ai_agent,
            ),
        ),
        Group(
            Start(
                I18nFormat("create-category-btn"),
                id="on_create_category",
                state=states.CreateCategory.enter_category_name,
            ),
            Start(
                I18nFormat("edit-category-btn"),
                id="on_edit_category",
                state=states.EditCategory.select_category,
            ),
            Start(
                I18nFormat("delete-category-btn"),
                id="on_delete_category",
                state=states.DeleteCategory.select_category,
            ),
            width=2,
        ),
    )


def select_category_keyboard(on_select_category):
    return ScrollingGroup(
        Select(
            Format("{item[1]}"),
            id="select_category",
            items="categories",
            item_id_getter=operator.itemgetter(0),
            on_click=on_select_category,
        ),
        id="select_category_scroll",
        hide_on_single_page=True,
        height=6,
        width=1,
    )
