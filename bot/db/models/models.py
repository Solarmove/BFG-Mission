from aiogram.enums import ContentType
from sqlalchemy import BIGINT, BOOLEAN, ForeignKey, func, VARCHAR, INTEGER, TEXT
from sqlalchemy.dialects.postgresql import ENUM, TIME, TIMESTAMP, DATE
from sqlalchemy.orm import Mapped, mapped_column, Relationship

from bot.db.base import Base
from bot.utils.enum import TaskStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BIGINT,
        primary_key=True,
        autoincrement=False,
    )
    username: Mapped[str | None] = mapped_column(
        VARCHAR(32),
        nullable=True,
    )
    full_name_tg: Mapped[str | None] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )
    full_name = mapped_column(VARCHAR(255), nullable=True, unique=True)
    position_id: Mapped[int | None] = mapped_column(
        INTEGER,
        ForeignKey("positions.id", ondelete="SET NULL"),
        nullable=True,
    )
    position: Mapped["Positions"] = Relationship(
        back_populates="users",
    )
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
    )
    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )
    work_schedules: Mapped[list["WorkSchedule"]] = Relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    created_tasks: Mapped[list["Task"]] = Relationship(
        back_populates="creator",
        cascade="all, delete-orphan",
        foreign_keys="[Task.creator_id]",
    )
    executed_tasks: Mapped[list["Task"]] = Relationship(
        back_populates="executor",
        cascade="all, delete-orphan",
        foreign_keys="[Task.executor_id]",
    )

    reports: Mapped[list["TaskReport"]] = Relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Positions(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
    )
    title: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, unique=True)
    hierarchy_level: Mapped[int] = mapped_column(INTEGER, nullable=False)

    users: Mapped[list["User"]] = Relationship(
        back_populates="position", cascade="all, delete-orphan"
    )


class WorkSchedule(Base):
    __tablename__ = "work_schedules"

    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_time: Mapped[str] = mapped_column(TIME, nullable=False)
    end_time: Mapped[str] = mapped_column(TIME, nullable=False)
    date = mapped_column(DATE, nullable=False)

    user: Mapped["User"] = Relationship(back_populates="work_schedules")


class TaskCategory(Base):
    __tablename__ = "task_categories"

    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)

    tasks: Mapped[list["Task"]] = Relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
    )
    creator_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    creator: Mapped["User"] = Relationship(
        back_populates="created_tasks",
        foreign_keys="Task.creator_id",
    )
    executor_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    executor: Mapped["User"] = Relationship(
        back_populates="executed_tasks",
        foreign_keys="Task.executor_id",
    )
    title: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    start_datetime = mapped_column(TIMESTAMP, nullable=False)
    end_datetime = mapped_column(TIMESTAMP, nullable=False)
    completed_datetime = mapped_column(TIMESTAMP, nullable=True)
    category_id = mapped_column(
        INTEGER,
        ForeignKey("task_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    photo_required: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    video_required: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    file_required: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    status = mapped_column(ENUM(TaskStatus), nullable=False, default=TaskStatus.NEW)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
    )
    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["TaskCategory"] = Relationship(
        back_populates="tasks",
    )
    control_points: Mapped[list["TaskControlPoints"]] = Relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["TaskReport"]] = Relationship(
        back_populates="task",
    )


class TaskControlPoints(Base):
    __tablename__ = "task_control_points"

    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
    )
    task_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    deadline = mapped_column(TIMESTAMP, nullable=False)
    datetime_complete = mapped_column(TIMESTAMP, nullable=True)
    description: Mapped[str] = mapped_column(TEXT, nullable=False)

    task: Mapped["Task"] = Relationship(back_populates="control_points")
    report: Mapped["TaskReport"] = Relationship(
        back_populates="task_control_point",
    )


class TaskReport(Base):
    __tablename__ = "task_reports"

    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped["User"] = Relationship(
        back_populates="reports",
    )
    task_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_control_point_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey("task_control_points.id", ondelete="CASCADE"),
        nullable=True,
    )
    report_text: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
    )

    task: Mapped["Task"] = Relationship(back_populates="reports")
    content: Mapped[list["TaskReportContent"]] = Relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )
    task_control_point: Mapped["TaskControlPoints"] = Relationship(
        back_populates="report",
    )


class TaskReportContent(Base):
    __tablename__ = "task_report_contents"

    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
    )
    report_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey("task_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    report: Mapped["TaskReport"] = Relationship(
        back_populates="content",
    )
    file_id: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    file_unique_id: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )
    content_type = mapped_column(ENUM(ContentType), nullable=False)
