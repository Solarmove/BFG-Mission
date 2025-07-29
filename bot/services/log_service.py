import logging
from datetime import datetime
from enum import StrEnum
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from configreader import config

logger = logging.getLogger(__name__)


class LogLevel(StrEnum):
    """Enum for different log levels"""

    DEBUG = "🔍 НАЛАГОДЖЕННЯ"
    INFO = "ℹ️ ІНФОРМАЦІЯ"
    WARNING = "⚠️ ПОПЕРЕДЖЕННЯ"
    ERROR = "❌ ПОМИЛКА"
    CRITICAL = "🚨 КРИТИЧНО"


class LogService:
    """
    Log service class that sends logs to a Telegram channel.

    This service allows sending different types of logs (info, warning, error, etc.)
    to a configured Telegram channel with proper formatting and error handling.
    """

    def __init__(self, bot: Bot = Bot(config.bot_config.bot_token)) -> None:
        """
        Initialize the log service.

        :param bot: The Bot instance to use for sending messages.
        """
        self.bot = bot
        self.channel_id = config.bot_config.bot_channel_id
        self.info_thread_id = config.bot_config.info_logs_channel_thread_id
        self.error_thread_id = config.bot_config.error_logs_channel_thread_id
        self.debug_thread_id = config.bot_config.debug_logs_channel_thread_id
        self.warning_thread_id = config.bot_config.warning_logs_channel_thread_id
        self.critical_thread_id = config.bot_config.critical_logs_channel_thread_id



    @staticmethod
    def _format_message(
        level: LogLevel, message: str, extra_info: Optional[dict] = None
    ) -> str:
        """
        Format the log message with timestamp and additional information.

        :param level: The log level.
        :param message: The main log message.
        :param extra_info: Optional dictionary with additional information.
        :return: Formatted message string.
        """
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        formatted_msg = f"{level.value}\n📅 {timestamp}\n💬 {message}"

        if extra_info:
            formatted_msg += "\n\n<blockquote>📋 Додаткова інформація:"
            for key, value in extra_info.items():
                formatted_msg += f"\n• {key}: {value}"
        formatted_msg += "</blockquote>"
        return formatted_msg

    def get_thread_id(self, level: LogLevel) -> int:
        """
        Get the thread ID for the specified log level.

        :param level: The log level.
        :return: Corresponding thread ID.
        """
        if level == LogLevel.INFO:
            return self.info_thread_id
        elif level == LogLevel.ERROR:
            return self.error_thread_id
        elif level == LogLevel.DEBUG:
            return self.debug_thread_id
        elif level == LogLevel.WARNING:
            return self.warning_thread_id
        elif level == LogLevel.CRITICAL:
            return self.critical_thread_id
        else:
            raise ValueError(f"Unknown log level: {level}")

    async def _send_log(
        self, level: LogLevel, message: str, extra_info: Optional[dict] = None
    ) -> bool:
        """
        Send a log message to the configured channel.

        :param level: The log level.
        :param message: The log message.
        :param extra_info: Optional additional information.
        :return: True if message was sent successfully, False otherwise.
        """
        try:
            formatted_message = self._format_message(level, message, extra_info)

            await self.bot.send_message(
                chat_id=self.channel_id,
                text=formatted_message,
                message_thread_id=self.get_thread_id(level),
                parse_mode="HTML",
            )
            return True

        except TelegramAPIError as e:
            logger.error(f"Не вдалося відправити лог до каналу {self.channel_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Неочікувана помилка при відправці логу: {e}")
            return False

    async def debug(self, message: str, extra_info: Optional[dict] = None) -> bool:
        """
        Send a debug log message.

        :param message: The debug message.
        :param extra_info: Optional additional information.
        :return: True if message was sent successfully, False otherwise.
        """
        return await self._send_log(LogLevel.DEBUG, message, extra_info)

    async def info(self, message: str, extra_info: Optional[dict] = None) -> bool:
        """
        Send an info log message.

        :param message: The info message.
        :param extra_info: Optional additional information.
        :return: True if message was sent successfully, False otherwise.
        """
        return await self._send_log(LogLevel.INFO, message, extra_info)

    async def warning(self, message: str, extra_info: Optional[dict] = None) -> bool:
        """
        Send a warning log message.

        :param message: The warning message.
        :param extra_info: Optional additional information.
        :return: True if message was sent successfully, False otherwise.
        """
        return await self._send_log(LogLevel.WARNING, message, extra_info)

    async def error(self, message: str, extra_info: Optional[dict] = None) -> bool:
        """
        Send an error log message.

        :param message: The error message.
        :param extra_info: Optional additional information.
        :return: True if message was sent successfully, False otherwise.
        """
        return await self._send_log(LogLevel.ERROR, message, extra_info)

    async def critical(self, message: str, extra_info: Optional[dict] = None) -> bool:
        """
        Send a critical log message.

        :param message: The critical message.
        :param extra_info: Optional additional information.
        :return: True if message was sent successfully, False otherwise.
        """
        return await self._send_log(LogLevel.CRITICAL, message, extra_info)

    async def log_exception(
        self, exception: Exception, context: str = "", extra_info: Optional[dict] = None
    ) -> bool:
        """
        Log an exception with context information.

        :param exception: The exception to log.
        :param context: Additional context about where the exception occurred.
        :param extra_info: Optional additional information.
        :return: True if message was sent successfully, False otherwise.
        """
        exception_info = {
            "Тип помилки": type(exception).__name__,
            "Повідомлення помилки": str(exception),
        }

        if extra_info:
            exception_info.update(extra_info)

        message = f"Виникла помилка"
        if context:
            message += f" в {context}"

        return await self._send_log(LogLevel.ERROR, message, exception_info)

    async def log_user_action(
        self, user_id: int, action: str, details: Optional[dict] = None
    ) -> bool:
        """
        Log a user action for monitoring purposes.

        :param user_id: The ID of the user who performed the action.
        :param action: Description of the action performed.
        :param details: Optional additional details about the action.
        :return: True if message was sent successfully, False otherwise.
        """
        action_info = {
            "ID користувача": user_id,
            "Дія": action,
        }

        if details:
            action_info.update(details)

        return await self._send_log(
            LogLevel.INFO, "Зафіксовано дію користувача", action_info
        )
