import asyncio
import logging

from aiogram import Bot
from aiogram.types import Message
from aiogram_dialog import BaseDialogManager, DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_i18n import I18nContext
from arq import ArqRedis
from langchain_openai import ChatOpenAI
from redis.asyncio import Redis

from ...services.ai_agent.main import AIAgent
from ...services.ai_agent.prompts import get_prompt_from_hierarchy_level, get_prompt
from ...services.ai_agent.tools_manager import Tools
from ...services.log_service import LogService
from ...utils.misc import voice_to_text
from ...utils.unitofwork import UnitOfWork
from . import states


logger = logging.getLogger(__name__)


async def invoke_ai_agent(
    manager: BaseDialogManager,
    ai_agent: AIAgent,
    message_text: str,
    log_service: LogService,
):
    try:
        llm_response_generator = ai_agent.stream_response(message_text)
        result_text = ""
        buffer = ""
        async for chunk, process_chunk in llm_response_generator:
            if process_chunk:
                await manager.update({"answer": process_chunk})
                continue
            if chunk is None:
                continue
            result_text += chunk
            buffer += result_text
            await manager.update({"answer": result_text})
        if buffer:
            await manager.update({"answer": result_text})
    except Exception as e:
        logger.info("Error while invoking AI agent: %s", e)
        await log_service.log_exception(
            e,
            context="AI agent. Загальний",
            extra_info={"Запит": message_text, "Помилка": str(e)},
        )
        raise


async def common_run(
    manager: BaseDialogManager,
    ai_agent: AIAgent,
    message_text: str,
    log_service: LogService,
):
    # запускаем индикатор загрузки
    loading_task = asyncio.create_task(loading_text_decoration(manager))
    try:
        # ждём окончания AI-агента
        await invoke_ai_agent(manager, ai_agent, message_text, log_service)
    finally:
        # отменяем таск индикатора, как только агент отработает
        loading_task.cancel()


async def loading_text_decoration(
    manager: BaseDialogManager,
):
    stages = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    for i in range(300):
        for stage in stages:
            await manager.update(
                {"process_loading": f"{stage} Опрацьовуємо відповідь..."}
            )
            await asyncio.sleep(1)


async def on_send_first_message_query(
    message: Message, widget: MessageInput, manager: DialogManager
):
    """
    Handles the first message query from the user.
    """
    llm: ChatOpenAI = manager.middleware_data["llm"]
    arq: ArqRedis = manager.middleware_data["arq"]
    redis: Redis = manager.middleware_data["redis"]
    bot: Bot = manager.middleware_data["bot"]
    start_data = manager.start_data or {}
    channel_log: LogService = manager.middleware_data["channel_log"]
    task_tools = Tools(uow=UnitOfWork(), arq=arq, bot=bot)
    user_hierarchy_level = manager.dialog_data["hierarchy_level"]
    is_analytics = start_data.get("prompt") == "analytics"
    prompt = get_prompt(user_hierarchy_level, is_analytics=is_analytics)
    ai_agent = AIAgent(
        model=llm,
        tools=task_tools.get_tools()
        if not is_analytics
        else task_tools.get_tools_for_analytics(),
        prompt=prompt,
        redis_client=redis,
        chat_id=message.from_user.id,
        log_service=channel_log,
    )
    await ai_agent.clear_history()
    await on_send_query(message, widget, manager)


async def on_send_query(message: Message, widget: MessageInput, manager: DialogManager):
    """
    Handles the sending of a query to the AI agent.
    """
    bot: Bot = manager.middleware_data["bot"]
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    i18n: I18nContext = manager.middleware_data["i18n"]
    llm: ChatOpenAI = manager.middleware_data["llm"]
    arq: ArqRedis = manager.middleware_data["arq"]
    redis: Redis = manager.middleware_data["redis"]
    bot: Bot = manager.middleware_data["bot"]
    start_data = manager.start_data or {}
    channel_log: LogService = manager.middleware_data["channel_log"]
    task_tools = Tools(uow=UnitOfWork(), arq=arq, bot=bot)
    user_hierarchy_level = manager.dialog_data["hierarchy_level"]
    is_analytics = start_data.get("prompt") == "analytics"
    prompt = get_prompt(user_hierarchy_level, is_analytics=is_analytics)
    ai_agent = AIAgent(
        model=llm,
        tools=task_tools.get_tools()
        if not is_analytics
        else task_tools.get_tools_for_analytics(),
        prompt=prompt,
        redis_client=redis,
        chat_id=message.from_user.id,
        log_service=channel_log,
    )
    if message.text:
        message_text = message.text
    elif message.voice:
        message_text = await voice_to_text(bot, message)
    else:
        await message.answer(i18n.get("ai-agent-doesnt-support-this-content-type"))
        return
    await manager.switch_to(states.AIAgentMenu.answer)
    asyncio.create_task(
        invoke_ai_agent(manager.bg(), ai_agent, message_text, channel_log)
    )
