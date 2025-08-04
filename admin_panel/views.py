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

model_views = [
    ModelView(User, icon="fa fa-user"),
    ModelView(HierarchyLevel, icon="fa fa-sitemap"),
    ModelView(Positions, icon="fa fa-briefcase"),
    ModelView(WorkSchedule, icon="fa fa-calendar"),
    ModelView(TaskCategory, icon="fa fa-tasks"),
    ModelView(Task, icon="fa fa-clipboard-list"),
    ModelView(TaskControlPoints, icon="fa fa-map-marker-alt"),
    ModelView(TaskReport, icon="fa fa-file-alt"),
    ModelView(TaskReportContent, icon="fa fa-file-text"),
]
