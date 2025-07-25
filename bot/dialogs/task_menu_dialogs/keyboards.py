import operator

from aiogram_dialog.widgets.kbd import (
    Group,
    Select,
)  # noqa: F401
from aiogram_dialog.widgets.text import Format

from . import on_clicks, states  # noqa: F401


def select_type_of_task_keyboard():
    return Group(
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
    )
