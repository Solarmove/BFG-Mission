import operator

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


def select_task_type_keyboard():
    return Group(
        Select(
            Format("{item[1]}"),
            id="select_task_type",
            item_id_getter=operator.itemgetter(0),
            items=[("massive", "Щоденні завдання"), ("single", "З датою та часом")],
            on_click=on_clicks.on_select_task_type_click,
        ),
        width=2,
    )
