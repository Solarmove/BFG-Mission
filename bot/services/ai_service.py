import asyncio

import backoff
import openai
from aiogram.types import Message

from bot.services.ai_agent.main import AIAgent


async def generate_llm_response(ai_agent: AIAgent, message: Message, message_text: str):
    llm_response_generator = ai_agent.stream_response(message_text)
    result_text = ""
    buffer = ""
    async for chunk, process_chunk in llm_response_generator:
        if process_chunk:
            await message.edit_text(chunk)
            continue
        if chunk is None:
            continue
        result_text += chunk
        buffer += result_text
        await message.edit_text(result_text)
    if buffer:
        await message.edit_text(buffer)


async def loading_text_decoration(message: Message):
    stages = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    for i in range(300):
        for stage in stages:
            await message.edit_text(f"{stage} Опрацьовуємо відповідь...")
            await asyncio.sleep(1)


@backoff.on_exception(backoff.expo, openai.RateLimitError)
async def run_ai_generation_with_loader(
    ai_agent: AIAgent, message: Message, message_text: str
):
    # запускаем индикатор загрузки
    loading_task = asyncio.create_task(loading_text_decoration(message))
    try:
        # ждём окончания AI-агента
        await generate_llm_response(ai_agent, message, message_text)
    finally:
        # отменяем таск индикатора, как только агент отработает
        loading_task.cancel()
