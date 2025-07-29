import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from bot.db.models.models import (
    Positions,
    Task,
    TaskCategory,
    TaskControlPoints,
    TaskReport,
    TaskReportContent,
    User,
    WorkSchedule,
)
from bot.db.redis import redis_cache
from bot.entities.shared import TaskReadExtended
from bot.entities.task import TaskRead
from bot.utils.enum import Role, TaskStatus
from bot.utils.repository import SQLAlchemyRepository


class UserRepo(SQLAlchemyRepository):
    model = User

    async def get_all_users(self):
        stmt = select(self.model).options(joinedload(self.model.position))
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_user_by_id(self, user_id: int) -> model | None:
        stmt = (
            select(self.model)
            .where(self.model.id == user_id)
            .options(joinedload(self.model.position))
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_user_full_name(self, user_id: int) -> str | None:
        """Get the full name of a user by their ID."""
        stmt = select(self.model.full_name).where(self.model.id == user_id).limit(1)
        res = await self.session.execute(stmt)
        full_name = res.scalar_one_or_none()
        return full_name

    async def get_user_with_all_data(self, user_id: int):
        """Get a user with all related data."""
        stmt = (
            select(self.model)
            .where(self.model.id == user_id)
            .options(
                joinedload(self.model.position),
                selectinload(self.model.work_schedules),
                selectinload(self.model.created_tasks),
                selectinload(self.model.executed_tasks),
                # selectinload(self.model.reports),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_all_users_with_schedule(
        self,
    ):
        stmt = select(self.model).options(
            selectinload(self.model.work_schedules), joinedload(self.model.position)
        )
        res = await self.session.execute(stmt)
        return res.unique().scalars().all()

    @redis_cache(expiration=5)
    async def user_exist(self, user_id: int, update_cache: bool | None = None) -> bool:
        """Check if a user exists in the database."""
        return await self.find_one(id=user_id) is not None

    @redis_cache(expiration=60)
    async def get_user_hierarchy_level(
        self, user_id: int, update_cache: bool | None = None
    ) -> int | None:
        """Get the hierarchy level of a user."""
        stmt = (
            select(self.model)
            .where(self.model.id == user_id)
            .options(joinedload(self.model.position))
        )
        res = await self.session.execute(stmt)
        result = res.scalar_one_or_none()
        return result.position.hierarchy_level if result is not None else None

    async def get_user_from_hierarchy(self, level: Role):
        stmt = (
            select(self.model)
            .join(
                Positions,
                self.model.position_id == Positions.id,
            )
            .where(
                Positions.hierarchy_level <= level,
            )
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    @redis_cache(expiration=5)
    async def get_user_from_hierarchy_count(self, level: Role):
        stmt = (
            select(func.count(self.model.id))
            .join(
                Positions,
                self.model.position_id == Positions.id,
            )
            .where(
                Positions.hierarchy_level <= level,
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() or 0


class WorkScheduleRepo(SQLAlchemyRepository):
    model = WorkSchedule

    async def get_all_work_schedules_for_date_to_date(
        self,
        date_from: datetime.date,
        date_to: datetime.date,
        user_id: int | None = None,
    ):
        """Get all work schedules for a given date range."""
        stmt = (
            select(self.model)
            .where(self.model.date >= date_from, self.model.date <= date_to)
            .order_by(self.model.date)
        )
        if user_id is not None:
            stmt = stmt.where(self.model.user_id == user_id)
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

    @redis_cache(expiration=30)
    async def get_task_by_id(self, task_id: int, update_cache: bool | None = None):
        """Get a task by its ID."""
        stmt = (
            select(self.model)
            .where(self.model.id == task_id)
            .options(
                joinedload(self.model.creator).joinedload(User.position),
                joinedload(self.model.executor).joinedload(User.position),
                joinedload(self.model.category),
                joinedload(self.model.control_points),
                joinedload(self.model.reports),
            )
        )
        res = await self.session.execute(stmt)
        result = res.unique().scalar_one_or_none()
        if result is None:
            return None
        task_model = TaskReadExtended.model_validate(result, from_attributes=True)
        return task_model.model_dump() if task_model else None

    @redis_cache(expiration=30)
    async def get_all_task_simple(
        self,
        creator_id: int | None = None,
        executor_id: int | None = None,
        category_id: int | None = None,
        status: TaskStatus | None = None,
        start_datetime: datetime.datetime | None = None,
        end_datetime: datetime.datetime | None = None,
    ):
        """Get all tasks with optional filters."""
        stmt = select(self.model)
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
        stmt = stmt.order_by(self.model.created_at.desc())
        res = await self.session.execute(stmt)
        result = res.scalars().all()
        return [
            TaskRead.model_validate(task, from_attributes=True).model_dump()
            for task in result
        ]

    async def get_all_tasks(
        self,
        creator_id: int | None = None,
        executor_id: int | None = None,
        category_id: int | None = None,
        status: TaskStatus | None = None,
        start_datetime: datetime.datetime | None = None,
        end_datetime: datetime.datetime | None = None,
    ):
        """Get all tasks with optional filters."""
        stmt = select(self.model).options(
            joinedload(self.model.creator).joinedload(User.position),
            joinedload(self.model.executor).joinedload(User.position),
            joinedload(self.model.category),
            selectinload(self.model.control_points),
            joinedload(self.model.reports),
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
        stmt = stmt.order_by(self.model.created_at.desc())
        res = await self.session.execute(stmt)
        return res.unique().scalars().all()

    async def get_task_in_work(self, user_id: int):
        """Get the current task for a user."""
        datetime_now = datetime.datetime.now()
        stmt = (
            select(self.model)
            .where(
                self.model.executor_id == user_id,
                self.model.status == TaskStatus.IN_PROGRESS,
            )
            .order_by(self.model.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()


class TaskControlPointsRepo(SQLAlchemyRepository):
    model = TaskControlPoints


class TaskReportRepo(SQLAlchemyRepository):
    model = TaskReport


class TaskReportContentRepo(SQLAlchemyRepository):
    model = TaskReportContent


class PositionRepo(SQLAlchemyRepository):
    model = Positions


class AnalyticsRepo(SQLAlchemyRepository):
    """
    Repository for analytics-related operations.
    This is a placeholder for future analytics-related methods.
    """

    model = Task

    async def get_task_by_condition(
        self,
        creator_id: int | None = None,
        executor_id: int | None = None,
        status: TaskStatus | None = None,
        start_datetime: datetime.datetime | None = None,
        end_datetime: datetime.datetime | None = None,
    ):
        """
        Get tasks based on various conditions.
        This method can be extended to include more complex analytics queries.
        """
        stmt = select(self.model).options(
            joinedload(self.model.creator).joinedload(User.position),
            joinedload(self.model.executor).joinedload(User.position),
            joinedload(self.model.category),
            selectinload(self.model.control_points),
            joinedload(self.model.reports),
        )
        if creator_id is not None:
            stmt = stmt.where(self.model.creator_id == creator_id)
        if executor_id is not None:
            stmt = stmt.where(self.model.executor_id == executor_id)
        if status is not None:
            stmt = stmt.where(self.model.status == status)
        if start_datetime is not None:
            stmt = stmt.where(self.model.start_datetime >= start_datetime)
        if end_datetime is not None:
            stmt = stmt.where(self.model.end_datetime <= end_datetime)
        res = await self.session.execute(stmt)
        result = res.scalars().all()
        return [
            TaskReadExtended.model_validate(task, from_attributes=True).model_dump()
            for task in result
        ]
