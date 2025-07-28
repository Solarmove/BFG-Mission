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

    def __init__(self, uow: UnitOfWork, arq: ArqRedis, bot: Bot):
        self.uow = uow
        self.arq = arq
        self.bot = bot

        # Ініціалізація всіх інструментів
        self.datetime_tools = DateTimeTools(uow, arq)
        self.user_tools = UserTools(uow, arq, bot)
        self.work_schedule_tools = WorkScheduleTools(uow, arq)
        self.category_tools = CategoryTools(uow, arq)
        self.task_tools = TaskTools(uow, arq, bot)

    def get_tools(self):
        """
        Повертає всі доступні інструменти з усіх категорій.

        Returns:
            list: Список всіх інструментів для AI агента.
        """
        all_tools = [
            *self.datetime_tools.get_tools(),
            *self.user_tools.get_tools().all_tools,
            *self.work_schedule_tools.get_tools().all_tools,
            *self.category_tools.get_tools().all_tools,
            *self.task_tools.get_tools().all_tools,
        ]

        print(all_tools)
        return all_tools

    def get_tools_for_analytics(self):
        """
        Повертає інструменти, які використовуються для аналітики.

        Returns:
            list: Список інструментів для аналітики.
        """
        analytics_tools = [
            *self.datetime_tools.get_tools(),
            *self.user_tools.get_tools().analytics_tools,
            *self.work_schedule_tools.get_tools().analytics_tools,
            *self.category_tools.get_tools().analytics_tools,
            *self.task_tools.get_tools().analytics_tools,
        ]

        return analytics_tools
