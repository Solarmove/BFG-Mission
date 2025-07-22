from typing import Optional

from aiogram_dialog import ShowMode
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.widgets.kbd import Back
from aiogram_dialog.widgets.kbd.button import OnClick
from aiogram_dialog.widgets.text import Text

from bot.i18n.utils.i18n_format import I18nFormat


class BackBtn(Back):
    def __init__(
        self,
        text: Text = I18nFormat("back_btn"),
        id: str = "__back__",
        on_click: Optional[OnClick] = None,
        show_mode: Optional[ShowMode] = None,
        when: WhenCondition = None,
    ):
        super().__init__(
            text=text,
            on_click=on_click,
            id=id,
            when=when,
            show_mode=show_mode,
        )


