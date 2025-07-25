from typing import Optional

from aiogram import Bot
from aiogram.types import Message, ReplyMarkupUnion, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from arq import ArqRedis
from langchain_core.tools import tool
from bot.entities.shared import UserReadExtended
from bot.entities.task import TaskRead
from bot.entities.users import UserRead, WorkScheduleRead
from bot.utils.unitofwork import UnitOfWork
from .base import BaseTools


class UserTools(BaseTools):
    """Інструменти для роботи з користувачами."""

    def __init__(self, uow: UnitOfWork, arq: ArqRedis, bot: Bot):
        super().__init__(uow, arq)
        self.uow = uow
        self.arq = arq
        self.bot = bot

    def get_tools(self) -> list:
        @tool
        async def get_all_users_from_db() -> list[UserRead]:
            """
            Отримати всіх користувачів з бази даних.

            Returns:
                list: List of all users.
            """

            async with self.uow:
                users = await self.uow.users.find_all()
                users_list = [
                    UserRead(
                        id=user.id,
                        username=user.username,
                        full_name_tg=user.full_name_tg,
                        full_name=user.full_name,
                        position_id=user.position_id,
                        position=user.position,
                        created_at=user.created_at,
                        updated_at=user.updated_at,
                    )
                    for user in users
                ]
                return users_list

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
            async with self.uow:
                if extended:
                    user = await self.uow.users.get_user_with_all_data(user_id=user_id)
                    if not user:
                        return None
                    return UserReadExtended(
                        id=user.id,
                        username=user.username,
                        full_name_tg=user.full_name_tg,
                        full_name=user.full_name,
                        position_id=user.position_id,
                        position=user.position,
                        created_at=user.created_at,
                        updated_at=user.updated_at,
                        work_schedules=[
                            WorkScheduleRead(
                                id=ws.id,
                                user_id=ws.user_id,
                                start_time=ws.start_time,
                                end_time=ws.end_time,
                                date=ws.date,
                            )
                            for ws in user.work_schedules
                        ],
                        created_tasks=[
                            TaskRead(
                                id=task.id,
                                creator_id=task.creator_id,
                                executor_id=task.executor_id,
                                title=task.title,
                                description=task.description,
                                start_datetime=task.start_datetime,
                                end_datetime=task.end_datetime,
                                completed_datetime=task.completed_datetime,
                                category_id=task.category_id,
                                photo_required=task.photo_required,
                                video_required=task.video_required,
                                file_required=task.file_required,
                                status=task.status,
                            )
                            for task in user.created_tasks
                        ],
                        executed_tasks=[
                            TaskRead(
                                id=task.id,
                                creator_id=task.creator_id,
                                executor_id=task.executor_id,
                                title=task.title,
                                description=task.description,
                                start_datetime=task.start_datetime,
                                end_datetime=task.end_datetime,
                                completed_datetime=task.completed_datetime,
                                category_id=task.category_id,
                                photo_required=task.photo_required,
                                video_required=task.video_required,
                                file_required=task.file_required,
                                status=task.status,
                            )
                            for task in user.executed_tasks
                        ],
                    )
                else:
                    user = await self.uow.users.get_user_by_id(user_id=user_id)
                    if not user:
                        return None
                    return UserRead(
                        id=user.id,
                        username=user.username,
                        full_name_tg=user.full_name_tg,
                        full_name=user.full_name,
                        position_id=user.position_id,
                        position=user.position,
                        created_at=user.created_at,
                        updated_at=user.updated_at,
                    )

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
