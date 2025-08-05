from abc import ABC, abstractmethod
from arq import ArqRedis
from bot.utils.unitofwork import UnitOfWork


class BaseTools(ABC):
    """Абстрактний базовий клас для всіх інструментів AI агента."""

    def __init__(self, uow: UnitOfWork, arq: ArqRedis, user_id: int):
        self.uow = uow
        self.arq = arq
        self.user_id = user_id

    async def get_user_hierarchy_level(self, user_id: int | None = None) -> int:
        """
        Отримує рівень ієрархії користувача за його ID.
        Args:
            user_id (int): ID користувача, для якого потрібно отримати рівень ієрархії.
        Returns:
            int: Рівень ієрархії користувача.
        """
        async with self.uow:
            user_id = user_id or self.user_id
            level = await self.uow.users.get_user_hierarchy_level(user_id)
            return level

    @abstractmethod
    def get_tools(self) -> list:
        """
        Повертає список інструментів, які надає цей клас.

        Returns:
            list: Список інструментів для AI агента.
        """
        pass
