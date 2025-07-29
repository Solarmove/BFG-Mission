from aiogram_dialog import Window  # noqa: F401
from aiogram_dialog.widgets.input import MessageInput, TextInput  # noqa: F401
from aiogram_dialog.widgets.kbd import Back, Cancel  # noqa: F401
from aiogram_dialog.widgets.text import Const, Format, Case, Multi  # noqa: F401
from magic_filter import F

from ...i18n.utils.i18n_format import I18nFormat
from . import getters, keyboards, on_clicks, states  # noqa: F401

enter_full_name_window = Window(
    I18nFormat("enter-full-name-text"),
    TextInput(
        id="full_name",
        on_success=on_clicks.on_enter_full_name_click,
    ),
    state=states.Registration.enter_full_name,
)


main_menu_window = Window(
    Multi(
        Case(
            {
                1: I18nFormat("main-menu-1-level-text"),
                2: I18nFormat("main-menu-2-level-text"),
                3: I18nFormat("main-menu-3-level-text"),
                4: I18nFormat("main-menu-4-level-text"),
            },
            selector="hierarchy_level",
        ),
        Format("{current_task}", F["current_task"] & (F["hierarchy_level"] > 1)),
        sep="\n\n",
    ),
    keyboards.main_menu_keyboard(),
    state=states.MainMenu.select_action,
    getter=getters.main_menu_getter,
)
