import logging

from aiogram import Bot
from aiogram.types import ReplyMarkupUnion
from aiogram.utils.media_group import MediaGroupBuilder

logger = logging.getLogger(__name__)


async def send_message(
    bot: Bot,
    chat_id: int,
    text: str,
    media_group: MediaGroupBuilder | None = None,
    reply_markup: ReplyMarkupUnion | None = None,
):
    """
    Sends a message to a specified chat.

    :param bot: The Bot instance to use for sending the message.
    :param chat_id: The ID of the chat where the message will be sent.
    :param text: The text of the message to send.
    :param media_group: An optional MediaGroupBuilder instance containing media to send.
                        If provided, the media will be sent as a media group.
                        If not provided, only the text message will be sent.
    :param reply_markup: Optional reply markup for the message (e.g., inline keyboard).
                        If provided, it will be attached to the message.
    """
    try:
        if not media_group:
            await bot.send_message(
                chat_id=chat_id, text=text, reply_markup=reply_markup
            )
        else:
            media_group.caption = text
            media_group_built = media_group.build()
            if media_group_built:
                await bot.send_media_group(chat_id=chat_id, media=media_group_built)
            else:
                logger.warning(
                    f"No media to send in chat {chat_id}. Sending text only."
                )
                await bot.send_message(
                    chat_id=chat_id, text=text, reply_markup=reply_markup
                )
    except Exception as e:
        logger.error(f"Failed to send message to chat {chat_id}: {e}")
