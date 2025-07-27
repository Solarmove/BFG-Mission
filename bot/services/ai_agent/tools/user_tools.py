from typing import Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, Message, ReplyMarkupUnion
from aiogram.utils.keyboard import InlineKeyboardBuilder
from arq import ArqRedis
from langchain_core.tools import tool

from bot.db.redis import redis_cache
from bot.entities.shared import UserReadExtended
from bot.entities.users import UserRead
from bot.utils.unitofwork import UnitOfWork

from .base import BaseTools


class UserTools(BaseTools):
    """Інструменти для роботи з користувачами."""

    def __init__(self, uow: UnitOfWork, arq: ArqRedis, bot: Bot):
        super().__init__(uow, arq)
        self.uow = uow
        self.arq = arq
        self.bot = bot

    @redis_cache(15)
    async def get_user_dict(
        self, user_id: int, extended: bool = False
    ) -> UserRead | UserReadExtended | None:
        """
        Отримати користувача за його ID.

        :param user_id: ID користувача, якого потрібно отримати.
        :param extended: Якщо True, повертає розширену інформацію про користувача, включаючи робочі графіки та завдання.

        Returns:
            UserRead | UserReadExtended | None: Користувач або None, якщо користувач не знайдений.
        """
        async with self.uow:
            if extended:
                user = await self.uow.users.get_user_with_all_data(user_id=user_id)
                if not user:
                    return None
                return UserReadExtended.model_validate(
                    user, from_attributes=True
                ).model_dump()
            else:
                user = await self.uow.users.get_user_by_id(user_id=user_id)
                if not user:
                    return None
                return UserRead.model_validate(user, from_attributes=True).model_dump()

    @redis_cache(15)
    async def get_all_users_dict(self) -> list[UserRead]:
        """
        Отримати всіх користувачів з бази даних.

        Returns:
            list: Список всіх користувачів.
        """
        async with self.uow:
            users = await self.uow.users.get_all_users()
            return [
                UserRead.model_validate(user, from_attributes=True).model_dump()
                for user in users
            ]

    def get_tools(self) -> list:
        @tool
        async def get_all_users_from_db() -> list[UserRead]:
            """
            Отримати всіх користувачів з бази даних.

            Returns:
                list: List of all users.
            """
            result = await self.get_all_users_dict()
            return [UserRead.model_validate(user) for user in result]

        @tool
        async def get_user_by_id(
            user_id: int, extended: bool = False
        ) -> UserRead | UserReadExtended | None:
            """
            Отримати користувача за його ID.

            :param user_id: ID користувача, якого потрібно отримати.
            :param extended: Якщо True, повертає розширену інформацію про користувача, включаючи робочі графіки та завдання.

            Returns:
                UserRead | UserReadExtended | None: Користувач або None, якщо користувач не знайдений.

            """
            result = await self.get_user_dict(user_id, extended)
            if result is None:
                return None
            if extended:
                return UserReadExtended.model_validate(result)
            return UserRead.model_validate(result)

        @tool
        async def create_reply_markup_for_accept_task(task_id: int) -> ReplyMarkupUnion:
            """
            Створити клавіатуру для прийняття завдання.

            :param task_id: ID завдання, яке потрібно прийняти з БД

            Returns:
                ReplyMarkupUnion: Клавіатура для прийняття завдання.
            """

            kb = InlineKeyboardBuilder()
            kb.add(
                InlineKeyboardButton(
                    text="Прийняти завдання",
                    callback_data=f"accept_task:{task_id}",
                )
            )
            return kb.as_markup()

        @tool
        async def create_reply_markup_for_show_task(task_id: int) -> ReplyMarkupUnion:
            """
            Створити клавіатуру для перегляду завдання.

            :param task_id: ID завдання, яке потрібно переглянути з БД

            Returns:
                ReplyMarkupUnion: Клавіатура для перегляду завдання.
            """

            kb = InlineKeyboardBuilder()
            kb.add(
                InlineKeyboardButton(
                    text="Переглянути завдання",
                    callback_data=f"show_task:{task_id}",
                )
            )
            return kb.as_markup()

        @tool
        async def create_reply_markup_for_done_task(task_id: int) -> ReplyMarkupUnion:
            """
            Створити клавіатуру для завершення завдання.

            :param task_id: ID завдання  з БД., яке потрібно завершити

            Returns:
                ReplyMarkupUnion: Клавіатура для завершення завдання.
            """

            kb = InlineKeyboardBuilder()
            kb.add(
                InlineKeyboardButton(
                    text="Завершити завдання",
                    callback_data=f"done_task:{task_id}",
                )
            )
            return kb.as_markup()

        @tool
        async def send_message(
            chat_id: int, text: str, reply_markup: Optional[ReplyMarkupUnion] = None
        ) -> Message:
            """
            Відправити повідомлення користувачу за його ID з БД.

            :param chat_id: ID чату користувача, якому потрібно відправити повідомлення.
            :param text: Текст повідомлення.
            :param reply_markup: Додаткові кнопки або клавіатура для повідомлення (необов'язково).

            Returns:
                Message: Відправлене повідомлення.
            """
            msg = await self.bot.send_message(
                chat_id=chat_id, text=text, reply_markup=reply_markup
            )
            return msg

        return [
            get_all_users_from_db,
            get_user_by_id,
            create_reply_markup_for_accept_task,
            create_reply_markup_for_show_task,
            create_reply_markup_for_done_task,
            send_message,
        ]
