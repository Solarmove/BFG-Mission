from abc import ABC, abstractmethod
from arq import ArqRedis
from bot.utils.unitofwork import UnitOfWork


class BaseTools(ABC):
    """Абстрактний базовий клас для всіх інструментів AI агента."""

    def __init__(self, uow: UnitOfWork, arq: ArqRedis):
        self.uow = uow
        self.arq = arq

    @abstractmethod
    def get_tools(self) -> list:
        """
        Повертає список інструментів, які надає цей клас.

        Returns:
            list: Список інструментів для AI агента.
        """
        pass
