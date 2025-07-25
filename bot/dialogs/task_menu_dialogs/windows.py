from aiogram_dialog import Window  # noqa: F401
from aiogram_dialog.widgets.kbd import Cancel, Back  # noqa: F401
from aiogram_dialog.widgets.text import Const, Format  # noqa: F401
from aiogram_dialog.widgets.input import TextInput, MessageInput  # noqa: F401
from ...i18n.utils.i18n_format import I18nFormat  # noqa: F401
from . import states, getters, keyboards, on_clicks  # noqa: F401


select_type_of_task_window = Window(
    I18nFormat("select-type-of-task-text"),
    keyboards.select_type_of_task_keyboard(),
    Cancel(I18nFormat("back-btn")),
    state=states.MyTasks.select_type_tasks,
)

select_task_window = Window(
I18nFormat("select-task-text"),
    keyboards.select_task_keyboard(),
    Cancel(I18nFormat("back-btn")),
    state=states.MyTasks.select_task,
    getter=getters.my_tasks_getter,
)

