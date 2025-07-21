from abc import ABC, abstractmethod
from typing import Type

from sqlalchemy.ext.asyncio.session import AsyncSession, async_sessionmaker

from bot.db.base import async_session_maker
from bot.db.repositories.repo import (
    UserRepo,
    GroupRepo,
    TaskRepo,
    GroupPartisipantsRepo,
    ReportRepo,
)


class IUnitOfWork(ABC):


    @abstractmethod
    def __init__(self): ...

    @abstractmethod
    async def __aenter__(self): ...

    @abstractmethod
    async def __aexit__(self, *args): ...

    @abstractmethod
    async def commit(self): ...

    @abstractmethod
    async def rollback(self): ...


class UnitOfWork(IUnitOfWork):
    session_factory: async_sessionmaker[AsyncSession] = None

    def __call__(self, *args, **kwargs):
        ...

    def __init__(self):
        if not self.session_factory:
            self.session_factory = async_session_maker

    async def __aenter__(self):
        self.session = self.session_factory()
        self.transaction = await self.session.begin()
        return self

    async def __aexit__(self, exc_type, *args):
        if exc_type:
            await self.transaction.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
