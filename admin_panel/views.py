from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView
from bot.db.models.models import (
    User,
    HierarchyLevel,
    Positions,
    WorkSchedule,
    TaskCategory,
    Task,
    TaskReportContent,
    TaskReport,
    TaskControlPoints,
)


class UserView(ModelView):
    exclude_fields_from_list = [
        "work_schedules",
        "created_tasks",
        "executed_tasks",
        "reports",
    ]
    exclude_fields_from_detail = [
        "work_schedules",
        "created_tasks",
        "executed_tasks",
        "reports",
    ]

    async def repr(self, obj: User, request: Request) -> str:
        return obj.full_name or obj.full_name_tg


model_views = [
    UserView(User, icon="fa fa-user"),
    ModelView(HierarchyLevel, icon="fa fa-sitemap"),
    ModelView(Positions, icon="fa fa-briefcase"),
    ModelView(WorkSchedule, icon="fa fa-calendar"),
    ModelView(TaskCategory, icon="fa fa-tasks"),
    ModelView(Task, icon="fa fa-clipboard-list"),
    ModelView(TaskControlPoints, icon="fa fa-map-marker-alt"),
    ModelView(TaskReport, icon="fa fa-file-alt"),
    ModelView(TaskReportContent, icon="fa fa-file-text"),
]
