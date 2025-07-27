import datetime

from pydantic import BaseModel


class TaskReportRead(BaseModel):
    """
    Represents a task report read model.
    This model is used to read task reports from the database.
    """

    id: int
    user_id: int
    task_id: int
    task_control_point_id: int | None = None
    report_text: str
    created_at: datetime.datetime