import os
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import Message
from aiogram.utils.link import create_tg_link
from openai import AsyncOpenAI

from configreader import config


async def get_user_url(username: str | None, user_id: int, full_name: str):
    """Получает ссылку на пользователя"""
    if username:
        return f"@{username}"
    user_url = create_tg_link("user", id=user_id)
    return f"<a href='{user_url}'>{full_name}</a>"


async def recognize_text(file_path: str) -> str:
    client = AsyncOpenAI(
        api_key=config.openai_api_key,
    )
    with open(file_path, "rb") as audio_file:
        transcription = await client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
    return transcription.text


async def voice_to_text(bot: Bot, message: Message) -> str:
    os.makedirs(".upload_dir", exist_ok=True)
    path_to_voice = f".upload_dir/{message.voice.file_id}.ogg"
    await bot.download(message.voice.file_id, destination=path_to_voice)
    message_text = await recognize_text(path_to_voice)
    os.remove(path_to_voice)
    return message_text


def is_task_hot(task_deadline: datetime) -> bool:
    """Проверяет, горячее ли задание"""
    current_time = datetime.now()
    return task_deadline - current_time <= timedelta(minutes=30)
