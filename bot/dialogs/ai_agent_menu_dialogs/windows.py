from aiogram.enums import ContentType, ParseMode
from aiogram_dialog import Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Cancel,
    CurrentPage,
    NextPage,
    PrevPage,
    Row,
)
from aiogram_dialog.widgets.text import Case, Const, Format, ScrollingText, Multi
from magic_filter import F

from ...i18n.utils.i18n_format import I18nFormat
from . import getters, on_clicks, states

send_query_window = Window(
    Case(
        {
            "analytics": I18nFormat("ai-agent-analytics-text"),
            "helper": I18nFormat("ai-agent-helper-text"),
        },
        selector="prompt",
    ),
    MessageInput(
        func=on_clicks.on_send_query,
        content_types=[ContentType.TEXT, ContentType.VOICE],
    ),
    Cancel(I18nFormat("back-btn")),
    state=states.AIAgentMenu.send_query,
    # getter=getters.ai_agent_getter,
    parse_mode=ParseMode.MARKDOWN,
)


show_ai_answer_window = Window(
    Multi(
        ScrollingText(Format("{answer}"), id="ai_answer", page_size=2000, when=F["answer"]),
        Format("{process_loading}", when=~F["answer"]),
    ),
    Row(
        PrevPage(
            scroll="ai_answer",
            text=Const("«"),
        ),
        CurrentPage(
            scroll="ai_answer",
        ),
        NextPage(
            scroll="ai_answer",
            text=Const("»"),
        ),
        when=F["answer_len"] > 4000,
    ),
    MessageInput(
        func=on_clicks.on_send_query,
        content_types=[ContentType.TEXT, ContentType.VOICE],
    ),
    Cancel(I18nFormat("back-btn")),
    state=states.AIAgentMenu.answer,
    getter=getters.ai_agent_answer_getter,
    # parse_mode=ParseMode.MARKDOWN_V2,
)
