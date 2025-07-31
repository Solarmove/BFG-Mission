import datetime
from langchain_core.tools import tool
from .base import BaseTools
import pytz


class DateTimeTools(BaseTools):
    """Інструменти для роботи з датою та часом."""

    def get_tools(self) -> list:
        @tool
        async def get_datetime():
            """Отримати поточну дату та час у Києві."""
            tz = pytz.timezone("Europe/Kyiv")
            return datetime.datetime.now(tz)

        return [get_datetime]
