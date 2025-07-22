from typing import Sequence

from sqlalchemy import select

from bot.db.models.models import (
    TaskReportContent,
    User,
    WorkSchedule,
    TaskCategory,
    Task,
    TaskControlPoints,
    TaskReport,
)
from bot.db.redis import redis_cache
from bot.utils.repository import SQLAlchemyRepository


class UserRepo(SQLAlchemyRepository):
    model = User

    async def get_all_personal(self) -> Sequence[User]:
        """Get all users with hierarchy level >= 2, ordered by full name."""
        stmt = (
            select(self.model)
            .order_by(self.model.full_name)
            .where(self.model.hierarchy_level >= 2)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    @redis_cache(expiration=5)
    async def user_exist(self, user_id: int, update_cache: bool | None = None) -> bool:
        """Check if a user exists in the database."""
        return await self.find_one(id=user_id) is not None

    @redis_cache(expiration=60)
    async def get_user_hierarchy_level(
        self, user_id: int, update_cache: bool | None = None
    ) -> int | None:
        """Get the hierarchy level of a user."""
        stmt = select(self.model.hierarchy_level).where(id=user_id).limit(1)
        res = await self.session.execute(stmt)
        hierarchy_level = res.scalar_one_or_none()
        return hierarchy_level if hierarchy_level is not None else None


class WorkScheduleRepo(SQLAlchemyRepository):
    model = WorkSchedule


class TaskCategoryRepo(SQLAlchemyRepository):
    model = TaskCategory


class TaskRepo(SQLAlchemyRepository):
    model = Task


class TaskControlPointsRepo(SQLAlchemyRepository):
    model = TaskControlPoints


class TaskReportRepo(SQLAlchemyRepository):
    model = TaskReport


class TaskReportContentRepo(SQLAlchemyRepository):
    model = TaskReportContent
    