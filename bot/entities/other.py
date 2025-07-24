from pydantic import BaseModel


class ScheduleCreationResult(BaseModel):
    """
    Represents the result of a schedule creation operation.
    """
    created_count: int
    existing_count: int
