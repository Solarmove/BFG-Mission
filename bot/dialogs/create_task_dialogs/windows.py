from aiogram.enums import ContentType
from aiogram_dialog import Window  # noqa: F401
from aiogram_dialog.widgets.kbd import Cancel, Back  # noqa: F401
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format  # noqa: F401
from aiogram_dialog.widgets.input import TextInput, MessageInput  # noqa: F401
from . import states, getters, keyboards, on_clicks  # noqa: F401
from ...i18n.utils.i18n_format import I18nFormat
#
# select_task_type = Window(
#     I18nFormat("select-task-type-text"),
#     keyboards.select_task_type_keyboard(),
#     Cancel(I18nFormat("back-btn")),
#     # state=states.CreateTask,
# )
