import datetime
from langchain_core.tools import tool
from .base import BaseTools


class DateTimeTools(BaseTools):
    """Інструменти для роботи з датою та часом."""
    
    def get_tools(self) -> list:
        @tool
        async def get_datetime():
            """Отримати поточну дату та час."""
            return datetime.datetime.now()

        return [get_datetime]