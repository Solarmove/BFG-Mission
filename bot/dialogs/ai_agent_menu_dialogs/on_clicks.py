import asyncio
import random
import re
from aiogram import Bot
from aiogram.types import Message
from aiogram_dialog import DialogManager, BaseDialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_i18n import I18nContext
from arq import ArqRedis
from langchain_openai import ChatOpenAI
from redis.asyncio import Redis

from ...services.ai_agent.main import AIAgent
from ...services.ai_agent.prompts import get_prompt_from_hierarchy_level
from ...services.ai_agent.tools_manager import Tools
from ...utils.consts import waiting_phrases
from ...utils.misc import voice_to_text
from ...utils.unitofwork import UnitOfWork
from . import states


async def invoke_ai_agent(
    manager: BaseDialogManager, ai_agent: AIAgent, message_text: str
):
    llm_response_generator = ai_agent.stream_response(message_text)
    result_text = ""
    buffer = ""
    async for chunk in llm_response_generator:
        if chunk is None:
            await asyncio.sleep(0.5)
            await manager.update({"answer": random.choice(waiting_phrases)})
            continue
        print(chunk)
        result_text += chunk
        buffer += result_text
        if len(result_text) % 10 == 0:
            await manager.update({"answer": result_text})
    if buffer:
        await manager.update({"answer": result_text})


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
    task_tools = Tools(uow=UnitOfWork(), arq=arq, bot=bot)
    user_hierarchy_level = manager.dialog_data["hierarchy_level"]
    prompt = get_prompt_from_hierarchy_level(user_hierarchy_level)
    ai_agent = AIAgent(
        model=llm,
        tools=task_tools.get_tools(),
        prompt=prompt,
        redis_client=redis,
        chat_id=message.from_user.id,
    )
    await ai_agent.clear_history()
    return await on_send_query(message, widget, manager)


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
    task_tools = Tools(uow=UnitOfWork(), arq=arq, bot=bot)
    user_hierarchy_level = manager.dialog_data["hierarchy_level"]
    prompt = get_prompt_from_hierarchy_level(user_hierarchy_level)
    ai_agent = AIAgent(
        model=llm,
        tools=task_tools.get_tools(),
        prompt=prompt,
        redis_client=redis,
        chat_id=message.from_user.id,
    )

    if message.text:
        message_text = message.text
    elif message.voice:
        message_text = await voice_to_text(bot, message)
    else:
        await message.answer(i18n.get("ai-agent-doesnt-support-this-content-type"))
        return
    # llm_response = await ai_agent.invoke(message_text)
    manager.dialog_data["answer"] = random.choice(waiting_phrases)
    await manager.switch_to(states.AIAgentMenu.answer)
    asyncio.create_task(invoke_ai_agent(manager.bg(), ai_agent, message_text))

