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
from aiogram_dialog.widgets.text import Case, Const, Format, ScrollingText
from magic_filter import F

from ...i18n.utils.i18n_format import I18nFormat
from . import getters, on_clicks, states

send_query_window = Window(
    Case(
        {
            1: I18nFormat("ai-agent-send-query-text-1"),
            2: I18nFormat("ai-agent-send-query-text-2"),
            3: I18nFormat("ai-agent-send-query-text-3"),
            4: I18nFormat("ai-agent-send-query-text-4"),
        },
        selector="hierarchy_level",
    ),
    MessageInput(
        func=on_clicks.on_send_first_message_query,
        content_types=[ContentType.TEXT, ContentType.VOICE],
    ),
    Cancel(I18nFormat("back-btn")),
    state=states.AIAgentMenu.send_query,
    getter=getters.ai_agent_getter,
    parse_mode=ParseMode.MARKDOWN,
)


show_ai_answer_window = Window(
    ScrollingText(
        Format("{answer}"),
        id="ai_answer",
        page_size=2000,
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
        when=F["answer_len"] > 2000,
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
