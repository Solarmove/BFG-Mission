from typing import Literal

from aiogram import Bot
from arq import ArqRedis

from bot.utils.unitofwork import UnitOfWork

from .tools import (
    CategoryTools,
    DateTimeTools,
    TaskTools,
    UserTools,
    WorkScheduleTools,
)


class Tools:
    """Головний клас для управління всіма інструментами AI агента."""

    def __init__(self, uow: UnitOfWork, arq: ArqRedis, bot: Bot, user_id: int):
        self.uow = uow
        self.arq = arq
        self.bot = bot
        self.user_id = user_id

        # Ініціалізація всіх інструментів
        self.datetime_tools = DateTimeTools(self.uow, self.arq, self.user_id)
        self.user_tools = UserTools(uow, arq, self.user_id, self.bot)
        self.work_schedule_tools = WorkScheduleTools(self.uow, self.arq, self.user_id)
        self.category_tools = CategoryTools(self.uow, self.arq, self.user_id)
        self.create_task_tools = TaskTools(self.uow, self.arq, self.user_id)
        self.manage_task_tools = TaskTools(self.uow, self.arq, self.user_id)
        self.all_task_tools = TaskTools(self.uow, self.arq, self.user_id)

    def get_tools(
        self,
        prompt_arg: Literal[
            "manage_task_prompt",
            "work_schedule_prompt",
            "create_task_prompt",
            "category_prompt",
            "analytics_prompt",
        ],
    ):
        """
        Повертає всі доступні інструменти з усіх категорій.

        Returns:
            list: Список всіх інструментів для AI агента.
        """
        analytics_tools = [
            *self.datetime_tools.get_tools(),
            *self.user_tools.get_tools(),
            *self.work_schedule_tools.get_tools(),
            *self.category_tools.get_tools(),
            *self.manage_task_tools.get_tools(),
        ]
        create_task_tools = [
            *self.datetime_tools.get_tools(),
            *self.user_tools.get_tools(),
            *self.work_schedule_tools.get_tools(),
            *self.category_tools.get_tools(),
            *self.create_task_tools.get_tools(),
        ]

        work_schedule_tools = [
            *self.datetime_tools.get_tools(),
            *self.user_tools.get_tools(),
            *self.work_schedule_tools.get_tools(),
        ]

        manage_task_tools = [
            *self.datetime_tools.get_tools(),
            *self.user_tools.get_tools(),
            *self.category_tools.get_tools(),
            *self.manage_task_tools.get_tools(),
        ]

        categories_tools = [
            *self.category_tools.get_tools(),
        ]

        tools_mapper = {
            "manage_task_prompt": manage_task_tools,
            "work_schedule_prompt": work_schedule_tools,
            "create_task_prompt": create_task_tools,
            "category_prompt": categories_tools,
            "analytics_prompt": analytics_tools,
        }

        return tools_mapper[prompt_arg]

    def get_datetime_tools(self):
        """
        Повертає інструменти для роботи з датою та часом.

        Returns:
            list: Список інструментів для роботи з датою та часом.
        """
        return self.datetime_tools.get_tools()