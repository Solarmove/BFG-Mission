from bot.exceptions.base import BaseBotException


class TaskBaseException(BaseBotException):
    """Base class for all task-related exceptions."""

    def __init__(self, message: str):
        super().__init__(message)


class CreateTaskForHigherHierarchyUserError(TaskBaseException):
    """Exception raised when attempting to create a task for a user with higher hierarchy level."""

    def __init__(self, creator_level: str, executor_level: str):
        super().__init__(
            f"Cannot create task: executor's hierarchy level '{executor_level}' "
            f"is higher than creator's level '{creator_level}'"
        )


class TaskNotFoundError(TaskBaseException):
    """Exception raised when a task is not found."""

    def __init__(self, task_id: int):
        super().__init__(f"Task with ID {task_id} not found.")


class CantMakeTaskForYourselfError(TaskBaseException):
    """Exception raised when a user tries to create a task for themselves."""

    def __init__(self, user_id: int):
        super().__init__(f"User with ID {user_id} cannot create a task for themselves.")


class YouCantCreateTask(TaskBaseException):
    """Exception raised when a user tries to create a task but is not allowed to do so."""

    def __init__(self, user_id: int):
        super().__init__(f"User with ID {user_id} is not allowed to create tasks.")


