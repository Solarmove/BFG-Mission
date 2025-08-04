import datetime
from langchain_core.tools import tool

from configreader import KYIV
from .base import BaseTools


class DateTimeTools(BaseTools):
    """Інструменти для роботи з датою та часом."""

    def get_tools(self) -> list:
        @tool
        async def get_datetime():
            """Отримати поточну дату та час у Києві."""

            datetime_now = datetime.datetime.now().replace(tzinfo=KYIV)
            return datetime_now

        return [get_datetime]
