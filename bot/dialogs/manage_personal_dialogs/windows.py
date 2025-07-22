from aiogram_dialog import Window  # noqa: F401
from aiogram_dialog.widgets.kbd import Cancel, Back  # noqa: F401
from aiogram_dialog.widgets.text import Const, Format  # noqa: F401
from aiogram_dialog.widgets.input import TextInput, MessageInput  # noqa: F401
from bot.utils.i18n_utils.i18n_format import I18nFormat  # noqa: F401
from . import states, getters, keyboards, on_clicks  # noqa: F401


manage_personal_dialogs_window = Window(
    I18nFormat("manage-personal-menu-text"),
    keyboards.manage_personal_dialogs_keyboard(),
    Cancel(I18nFormat("back-btn")),
    state=states.ManagePersonalMenu.select_action,
    getter=getters.manage_personal_dialogs_getter,
)


create_reg_link_window = Window(
    I18nFormat("select-position-text"),
    keyboards.select_position_keyboard(),
    Back(Const("Back")),
    state=states.CreateRegLink.select_position,
    getter=getters.positions_getter,
)