import datetime

from langchain_core.tools import tool

from bot.services.ai_agent.tools import BaseTools
from bot.utils.enum import TaskStatus


class AnalyticTools(BaseTools):
    def get_tools(self):
        @tool
        async def get_analytic_for_user(
            user_id: int,
            date_from: datetime.date,
            date_to: datetime.date,
            task_status: TaskStatus | None = None,
        ):
            async with self.uow:
                ...

        return []
