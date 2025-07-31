import asyncio
import logging
from pprint import pprint

import backoff
import openai
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import Message

from bot.services.ai_agent.main import AIAgent


async def generate_llm_response(ai_agent: AIAgent, message_text: str):
    llm_response_generator = ai_agent.stream_response(message_text)
    text = ""
    async for chunk in llm_response_generator:
        if chunk is None:
            continue
        text += chunk

    return text


async def loading_text_decoration(message: Message):
    stages = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    while True:
        for stage in stages:
            try:
                await message.edit_text(f"{stage} Опрацьовуємо відповідь...")
            except TelegramRetryAfter as e:
                logging.info("TelegramRetryAfter: %s", e)
                await asyncio.sleep(e.retry_after)
                continue
            await asyncio.sleep(1.5)


@backoff.on_exception(backoff.expo, openai.RateLimitError)
async def run_ai_generation_with_loader(
    ai_agent: AIAgent, message: Message, message_text: str
):
    loading_task = asyncio.create_task(loading_text_decoration(message))
    try:
        text = await generate_llm_response(ai_agent, message_text)
    finally:
        loading_task.cancel()
    return text
