from typing import Any, Dict, Protocol

from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.widgets.text import Text
from fluent.runtime import FluentLocalization, FluentResourceLoader

from bot.src.middleware.i18n_dialog import I18nDialogMiddleware
from configreader import config


class Values(Protocol):
    def __getitem__(self, item: Any) -> Any:
        raise NotImplementedError


def default_format_text(text: str, data: Values) -> str:
    return text.format_map(data)


class I18NFormat(Text):
    def __init__(self, text: str, when: WhenCondition = None):
        super().__init__(when)
        self.text = text

    async def _render_text(self, data: Dict, manager: DialogManager) -> str:
        format_text = manager.middleware_data.get(
            config.i18n_format_key,
            default_format_text,
        )
        return format_text(self.text, data)


def make_i18n_middleware(path_to_locales: str) -> I18nDialogMiddleware:
    loader = FluentResourceLoader(path_to_locales)
    LOCALES = ["uk", 'ru', 'en']
    l10ns = {
        locale: FluentLocalization(
            [locale, 'uk', 'ru', 'en'],
            ["messages.ftl"],
            loader,
        )
        for locale in LOCALES
    }
    return I18nDialogMiddleware(l10ns, "ru", config.i18n_format_key)
