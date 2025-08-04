from typing import Optional

from aiogram import Bot
from aiogram.types import Message, ReplyMarkupUnion
from arq import ArqRedis
from langchain_core.tools import tool

from bot.db.redis import redis_cache
from bot.entities.shared import UserReadExtended
from bot.entities.users import UserRead, PositionRead
from bot.keyboards.task import (
    create_end_task_kb,
    create_show_task_kb,
    create_accept_task_kb,
)
from bot.utils.unitofwork import UnitOfWork

from .base import BaseTools
from ...mailing_service import send_message


class UserTools(BaseTools):
    """Інструменти для роботи з користувачами."""

    def __init__(self, uow: UnitOfWork, arq: ArqRedis, user_id: int, bot: Bot):
        super().__init__(uow, arq, user_id)
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
                ).model_dump(
                    exclude={
                        "position": {
                            "hierarchy_level": {
                                "create_task_prompt",
                                "manage_task_prompt",
                                "work_schedule_prompt",
                                "category_prompt",
                                "analytics_prompt",
                            }
                        }
                    },
                )
            else:
                user = await self.uow.users.get_user_by_id(user_id=user_id)
                if not user:
                    return None
                return UserRead.model_validate(user, from_attributes=True).model_dump(
                    exclude={
                        "position": {
                            "hierarchy_level": {
                                "create_task_prompt",
                                "manage_task_prompt",
                                "work_schedule_prompt",
                                "category_prompt",
                                "analytics_prompt",
                            }
                        }
                    },
                )

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
                UserRead.model_validate(user, from_attributes=True).model_dump(
                    exclude={
                        "position": {
                            "hierarchy_level": {
                                "create_task_prompt",
                                "manage_task_prompt",
                                "work_schedule_prompt",
                                "category_prompt",
                                "analytics_prompt",
                            }
                        }
                    },
                )
                for user in users
            ]

    @redis_cache(120)
    async def get_positions_func(self):
        """
        Отримати всі позиції користувачів.

        Returns:
            list: Список всіх посад користувачів.
        """
        async with self.uow:
            positions = await self.uow.positions.find_all()
            return [
                PositionRead.model_validate(
                    position,
                    from_attributes=True,
                ).model_dump(
                    exclude={
                        "hierarchy_level": {
                            "create_task_prompt",
                            "manage_task_prompt",
                            "work_schedule_prompt",
                            "category_prompt",
                            "analytics_prompt",
                        }
                    },
                )
                for position in positions
            ]

    @redis_cache(120)
    async def get_position_by_id(self, position_id: int) -> PositionRead | None:
        """
        Отримати посаду користувача за її ID.

        :param position_id: ID позиції, яку потрібно отримати.

        Returns:
            PositionRead | None: Позиція або None, якщо позиція не знайдена.
        """
        async with self.uow:
            position = await self.uow.positions.get_by_id(position_id)
            if not position:
                return None
            return PositionRead.model_validate(
                position, from_attributes=True
            ).model_dump(
                exclude={
                    "hierarchy_level": {
                        "create_task_prompt",
                        "manage_task_prompt",
                        "work_schedule_prompt",
                        "category_prompt",
                        "analytics_prompt",
                    }
                },
            )

    @redis_cache(120)
    async def get_user_position(self, user_id: int) -> PositionRead | None:
        """
        Отримати посаду користувача за його ID.
        :param user_id: ID користувача, для якого потрібно отримати позицію.
        """
        async with self.uow:
            user = await self.uow.users.get_user_by_id(user_id)
            if not user:
                return None
            if not user.position_id:
                return
            return PositionRead.model_validate(
                user.position, from_attributes=True
            ).model_dump(
                exclude={
                    "hierarchy_level": {
                        "create_task_prompt",
                        "manage_task_prompt",
                        "work_schedule_prompt",
                        "category_prompt",
                        "analytics_prompt",
                    }
                },
            )

    def get_tools(self) -> list:
        @tool
        async def get_positions(self):
            """
            Отримати всі позиції користувачів.

            Returns:
                list: Список всіх позицій користувачів.
            """
            result = await self.get_positions_func()
            return [PositionRead.model_validate(position) for position in result]

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
        async def get_user_hierarchy(
            user_id: int,
        ) -> int | None:
            """
            Отримати ієрархію користувачів за ID користувача.

            :param user_id: ID користувача, для якого потрібно отримати ієрархію.
            Returns:
                int| None: рівень ієрархії користувача.
                Якщо користувач не знайдений, повертає None.
            """
            user = await self.get_user_dict(user_id, extended=False)
            if user is None:
                return None
            user_model = UserRead.model_validate(user)
            return user_model.position.hierarchy_level.level

        @tool
        async def create_reply_markup_for_accept_task(task_id: int) -> ReplyMarkupUnion:
            """
            Створити клавіатуру для прийняття завдання.

            :param task_id: ID завдання, яке потрібно прийняти з БД. не може бути None

            Returns:
                ReplyMarkupUnion: Клавіатура для прийняття завдання.
            """

            return create_accept_task_kb(task_id)

        @tool
        async def create_reply_markup_for_show_task(task_id: int) -> ReplyMarkupUnion:
            """
            Створити клавіатуру для перегляду завдання.

            :param task_id: ID завдання, яке потрібно переглянути з БД

            Returns:
                ReplyMarkupUnion: Клавіатура для перегляду завдання.
            """

            return create_show_task_kb(task_id)

        @tool
        async def create_reply_markup_for_done_task(task_id: int) -> ReplyMarkupUnion:
            """
            Створити клавіатуру для завершення завдання.

            :param task_id: ID завдання  з БД., яке потрібно завершити

            Returns:
                ReplyMarkupUnion: Клавіатура для завершення завдання.
            """

            return create_end_task_kb(task_id)

        @tool
        async def send_message_func(
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
            msg = await send_message(
                bot=self.bot, chat_id=chat_id, text=text, reply_markup=reply_markup
            )
            return msg

        all_tools = [
            get_all_users_from_db,
            get_user_by_id,
            create_reply_markup_for_accept_task,
            create_reply_markup_for_show_task,
            create_reply_markup_for_done_task,
            send_message_func,
            get_user_hierarchy,
        ]
        return all_tools
