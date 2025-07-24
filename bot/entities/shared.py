from typing import Optional

from bot.entities.task import TaskRead, TaskCategoryRead, TaskControlPointRead
from bot.entities.users import UserRead, WorkScheduleRead


class TaskReadExtended(TaskRead):
    """Розширена модель для читання даних завдання, включає контрольні точки звіту та категорію."""

    category: Optional["TaskCategoryRead"] = None
    """Категорія завдання. Може бути None, якщо категорія була видалена."""
    creator: Optional["UserRead"] = None
    """Користувач, який створив завдання."""
    executor: Optional["UserRead"] = None
    """Користувач, який виконує завдання."""
    task_control_points: list["TaskControlPointRead"] | None = None
    """Список контрольних точок звіту завдання. Може бути None, якщо контрольні точки не передбачені."""


class UserReadExtended(UserRead):
    """Розширена модель для читання даних користувача з бази даних, включає робочі графіки,
    створені та виконані завдання."""

    work_schedules: list["WorkScheduleRead"] = []
    """Список робочих графіків користувача. Використовується для відображення робочого часу користувача."""
    created_tasks: list["TaskRead"] = []
    """Список завдань, створених користувачем. Використовується для відстеження завдань, які користувач створив."""
    executed_tasks: list["TaskRead"] = []
    # reports: list["TaskReportRead"] = []
