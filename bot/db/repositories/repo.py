import datetime
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

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
from bot.utils.enum import Role, TaskStatus
from bot.utils.repository import SQLAlchemyRepository


class UserRepo(SQLAlchemyRepository):
    model = User

    async def get_all_users_with_schedule(self):
        stmt = select(self.model).options(selectinload(self.model.work_schedules))
        res = await self.session.execute(stmt)
        return res.scalars().all()

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

    async def get_user_from_hierarchy(self, level: Role):
        stmt = select(self.model).where(self.model.hierarchy_level <= level)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    @redis_cache(expiration=5)
    async def get_user_from_hierarchy_count(self, level: Role):
        stmt = select(func.count(self.model.id)).where(
            self.model.hierarchy_level <= level
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() or 0


class WorkScheduleRepo(SQLAlchemyRepository):
    model = WorkSchedule

    async def get_count_of_users_on_shift(self):
        datetime_now = datetime.datetime.now()
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.start_time <= datetime_now.time(),
                self.model.end_time >= datetime_now.time(),
                self.model.date == datetime_now.date(),
            )
            .group_by(self.model.user_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() or 0


class TaskCategoryRepo(SQLAlchemyRepository):
    model = TaskCategory


class TaskRepo(SQLAlchemyRepository):
    model = Task

    async def get_my_current_task(self, user_id: int):
        """Get the current task for a user."""
        datetime_now = datetime.datetime.now()
        stmt = (
            select(self.model)
            .where(
                self.model.executor_id == user_id,
                self.model.status == TaskStatus.IN_PROGRESS,
                self.model.start_datetime <= datetime_now,
                self.model.end_datetime >= datetime_now,
            )
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()


class TaskControlPointsRepo(SQLAlchemyRepository):
    model = TaskControlPoints


class TaskReportRepo(SQLAlchemyRepository):
    model = TaskReport


class TaskReportContentRepo(SQLAlchemyRepository):
    model = TaskReportContent
