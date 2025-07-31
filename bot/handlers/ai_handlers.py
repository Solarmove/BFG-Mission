import logging

from aiogram import Router, F, flags, Bot
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
)
from aiogram_dialog import DialogManager, StartMode, ShowMode
from aiogram_i18n import I18nContext
from arq import ArqRedis
from langchain_openai import ChatOpenAI
from redis import Redis

from bot.dialogs.main_menu_dialogs.states import MainMenu
from bot.keyboards.ai import exit_ai_agent_kb
from bot.middleware.throttling import ThrottlingMiddleware
from bot.services.ai_agent.main import AIAgent
from bot.services.ai_agent.prompts import generate_prompt
from bot.services.ai_agent.tools_manager import Tools
from bot.services.ai_service import run_ai_generation_with_loader
from bot.services.log_service import LogService
from bot.states.ai import AIAgentMenu
from bot.utils.misc import voice_to_text
from bot.utils.unitofwork import UnitOfWork

router = Router()
router.message.middleware(ThrottlingMiddleware(ai=2.5))

logger = logging.getLogger(__name__)


@router.callback_query(F.data == "cancel_ai_agent", AIAgentMenu.send_query)
async def cancel_ai_agent(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: I18nContext,
    dialog_manager: DialogManager,
):
    await state.clear()
    await dialog_manager.start(
        MainMenu.select_action,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.DELETE_AND_SEND,
    )


@router.message(
    AIAgentMenu.send_query,
    F.content_type.in_([ContentType.TEXT, ContentType.VOICE]),
)
@flags.throttling_key("ai")
async def start_ai_agent(
    message: Message,
    uow: UnitOfWork,
    i18n: I18nContext,
    state: FSMContext,
    bot: Bot,
    llm: ChatOpenAI,
    arq: ArqRedis,
    redis: Redis,
    channel_log: LogService,
):
    state_data = await state.get_data()
    print("state_data:", state_data)
    call_data: dict = state_data.get("call_data")
    print("call-data", call_data)
    if call_data and "message_id" in call_data:
        try:
            await bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=call_data["message_id"],
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[]]),
            )
        except TelegramBadRequest as e:
            logger.info("Failed to edit reply markup: %s", e)
    msg = await bot.send_message(
        chat_id=message.chat.id,
        text="<i>Опрацьовуємо запит...</i>",
        reply_markup=exit_ai_agent_kb().as_markup(),
    )
    if message.text:
        message_text = message.text
    elif message.voice:
        message_text = await voice_to_text(bot, message)
    else:
        await message.answer(i18n.get("ai-agent-doesnt-support-this-content-type"))
        return
    task_tools = Tools(uow=UnitOfWork(), arq=arq, bot=bot)
    is_analytics = state_data.get("prompt") == "analytics"
    common_prompt, analytics_prompt = await uow.users.get_user_hierarchy_prompt(
        message.from_user.id
    )
    if not is_analytics:
        prompt = common_prompt
    else:
        prompt = analytics_prompt
    state_data.setdefault("query_history", []).append(message_text)
    base_prompt = generate_prompt(prompt)
    ai_agent = AIAgent(
        model=llm,
        tools=task_tools.get_tools()
        if not is_analytics
        else task_tools.get_tools_for_analytics(),
        prompt=base_prompt,
        redis_client=redis,
        chat_id=message.from_user.id,
        log_service=channel_log,
    )
    if len(state_data["query_history"]) == 1:
        await ai_agent.clear_history()
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    msg = await msg.edit_text("ㅤ", reply_markup=exit_ai_agent_kb().as_markup())
    answer_text = await run_ai_generation_with_loader(ai_agent, msg, message_text, channel_log)
    msg = await msg.edit_text(answer_text, reply_markup=exit_ai_agent_kb().as_markup())
    state_data.update(call_data=dict(message_id=msg.message_id))
    await state.set_data(state_data)
