from aiogram import Bot
from arq import ArqRedis
from bot.utils.unitofwork import UnitOfWork
from .tools import (
    DateTimeTools,
    UserTools,
    WorkScheduleTools,
    CategoryTools,
    TaskTools,
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
        self.task_tools = TaskTools(uow, arq)

    def get_tools(self):
        """
        Повертає всі доступні інструменти з усіх категорій.

        Returns:
            list: Список всіх інструментів для AI агента.
        """
        all_tools = [
            *self.datetime_tools.get_tools(),
            *self.user_tools.get_tools(),
            *self.work_schedule_tools.get_tools(),
            *self.category_tools.get_tools(),
            *self.task_tools.get_tools(),
        ]

        print(all_tools)
        return all_tools

