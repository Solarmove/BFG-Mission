from bot.exceptions.base import BaseBotException


class UserBaseException(BaseBotException):
    """Base class for all user-related exceptions."""

    def __init__(self, message: str):
        super().__init__(message)


class UserWithFullNameAlreadyExists(UserBaseException):
    """Exception raised when a user with the same full name already exists."""

    def __init__(self, full_name: str):
        super.__init__(f"User with full name '{full_name}' already exists.")
