from enum import StrEnum, IntEnum


class Role(IntEnum):
    DIRECTOR = 1
    CEO = 2
    ADMINISTRATOR = 3
    MANAGER = 4


class TaskStatus(StrEnum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    OVERDUE = "OVERDUE"
    