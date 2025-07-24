import datetime
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload

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

    async def get_user_with_all_data(self, user_id: int):
        """Get a user with all related data."""
        stmt = (
            select(self.model)
            .where(self.model.id == user_id)
            .options(
                selectinload(self.model.work_schedules),
                selectinload(self.model.created_tasks),
                selectinload(self.model.executed_tasks),
                # selectinload(self.model.reports),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

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

    async def get_all_work_schedules_for_date_to_date(
        self, date_from: datetime.date, date_to: datetime.date
    ):
        """Get all work schedules for a given date range."""
        stmt = (
            select(self.model)
            .where(self.model.date >= date_from, self.model.date <= date_to)
            .order_by(self.model.date)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

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

    async def get_all_tasks(
        self,
        creator_id: int | None = None,
        executor_id: int | None = None,
        category_id: int | None = None,
        status: str | None = None,
        start_datetime: datetime.datetime | None = None,
        end_datetime: datetime.datetime | None = None,
    ):
        """Get all tasks with optional filters."""
        stmt = select(self.model).options(
            joinedload(self.model.creator),
            joinedload(self.model.executor),
            joinedload(self.model.category),
            selectinload(self.model.control_points),
            joinedload(self.model.report),
        )
        if creator_id is not None:
            stmt = stmt.where(self.model.creator_id == creator_id)

        if executor_id is not None:
            stmt = stmt.where(self.model.executor_id == executor_id)
        if category_id is not None:
            stmt = stmt.where(self.model.category_id == category_id)
        if status is not None:
            stmt = stmt.where(self.model.status == status)
        if start_datetime is not None:
            stmt = stmt.where(self.model.start_datetime >= start_datetime)
        if end_datetime is not None:
            stmt = stmt.where(self.model.end_datetime <= end_datetime)

        res = await self.session.execute(stmt)
        return res.scalars().all()

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
