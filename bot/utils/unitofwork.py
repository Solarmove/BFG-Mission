from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio.session import AsyncSession, async_sessionmaker

from bot.db.base import async_session_maker
from bot.db.repositories.repo import (
    TaskCategoryRepo,
    TaskControlPointsRepo,
    TaskReportContentRepo,
    TaskReportRepo,
    TaskRepo,
    UserRepo,
    WorkScheduleRepo,
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

    def __init__(self):
        if not self.session_factory:
            self.session_factory = async_session_maker

    async def __aenter__(self):
        self.session = self.session_factory()
        self.users = UserRepo(self.session)
        self.work_schedules = WorkScheduleRepo(self.session)
        self.task_categories = TaskCategoryRepo(self.session)
        self.tasks = TaskRepo(self.session)
        self.task_control_points = TaskControlPointsRepo(self.session)
        self.task_reports = TaskReportRepo(self.session)
        self.task_report_contents = TaskReportContentRepo(self.session)
        return self

    async def __aexit__(self, exc_type, *args):
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
