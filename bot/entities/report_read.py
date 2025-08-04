import datetime

from pydantic import BaseModel, field_validator

from configreader import KYIV


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

    @field_validator("created_at", mode="before")
    def normalize_to_kyiv(cls, v: datetime.datetime) -> datetime:
        if isinstance(v, datetime.datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=KYIV)  # наивное = время в Киеве
            else:
                v = v.astimezone(KYIV)  # приводим к Киеву, если было в другой зоне
        return v
