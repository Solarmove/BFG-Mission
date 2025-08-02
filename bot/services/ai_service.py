import asyncio
import logging
from pprint import pprint

import backoff
import openai
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import Message
from pydantic import ValidationError

from bot.services.ai_agent.main import AIAgent
from bot.services.log_service import LogService


# async def generate_llm_response(
#     ai_agent: AIAgent, message_text: str, log_service: LogService
# ):
#     llm_response_generator = ai_agent.stream_response(message_text)
#     text = ""
#     try:
#         async for chunk in llm_response_generator:
#             if chunk is None:
#                 continue
#             text += chunk
#     except ValidationError as e:
#         await log_service.log_exception(e, extra_info={"message_text": message_text})
#         logging.error("ValidationError occurred while processing LLM response.")
#         text = ("Виникла помилка при обробці запиту.\n\n"
#                 "<b>Будь ласка, повторіть ваш запит ще раз.</b>")
#     return text


async def generate_llm_response(
    ai_agent: AIAgent, message_text: str, log_service: LogService
):
    try:
        llm_response = await ai_agent.invoke(message_text)
    except ValidationError as e:
        await log_service.log_exception(e, extra_info={"message_text": message_text})
        logging.error("ValidationError occurred while processing LLM response.")
        text = (
            "Виникла помилка при обробці запиту.\n\n"
            "<b>Будь ласка, повторіть ваш запит ще раз.</b>"
        )
        return text
    return llm_response


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
    ai_agent: AIAgent, message: Message, message_text: str, channel_log
):
    loading_task = asyncio.create_task(loading_text_decoration(message))
    try:
        text = await generate_llm_response(ai_agent, message_text, channel_log)
    finally:
        loading_task.cancel()
    return text
