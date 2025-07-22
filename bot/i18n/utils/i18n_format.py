import os
from typing import Any, Dict, Protocol

from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.widgets.text import Text
from fluent.runtime import FluentLocalization, FluentResourceLoader

from bot.db.redis import set_user_locale
from bot.middleware.i18n_dialog import I18nDialogMiddleware
from configreader import config


class Values(Protocol):
    def __getitem__(self, item: Any) -> Any:
        raise NotImplementedError


def default_format_text(text: str, data: Values) -> str:
    return text.format_map(data)


async def update_locale(locale: str, user_id: int, manager: DialogManager) -> None:
    loader = FluentResourceLoader(config.path_to_locales)
    LOCALES = ["uk"]
    l10ns = {
        locale: FluentLocalization(
            [
                locale,
            ],
            ["messages.ftl"],
            loader,
        )
        for locale in LOCALES
    }

    await set_user_locale(user_id=user_id, locale=locale)
    l10n = l10ns[locale]
    # we use fluent.runtime here, but you can create custom functions

    manager.middleware_data[config.i18n_format_key] = l10n.format_value


class I18nFormat(Text):
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
    LOCALES = ["uk"]
    l10ns = {
        locale: FluentLocalization([locale, "uk"], ["messages.ftl"], loader)
        for locale in LOCALES
    }
    return I18nDialogMiddleware(l10ns, "uk", config.i18n_format_key)
