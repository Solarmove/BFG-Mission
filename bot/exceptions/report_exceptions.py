from bot.exceptions.base import BaseBotException


class ReportBaseException(BaseBotException):
    """Base exception for report-related errors."""

    pass


class ReportPhotoRequiredError(ReportBaseException):
    """Exception raised when a report requires a photo but none is provided."""

    def __init__(self):
        super().__init__("Report requires a photo, but none was provided.")


class ReportVideoRequiredError(ReportBaseException):
    """Exception raised when a report requires a video but none is provided."""

    def __init__(self):
        super().__init__("Report requires a video, but none was provided.")


class ReportFileRequiredError(ReportBaseException):
    """Exception raised when a report requires a file but none is provided."""

    def __init__(self):
        super().__init__("Report requires a file, but none was provided.")