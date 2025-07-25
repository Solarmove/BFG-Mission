from aiogram_dialog import Dialog  # noqa: F401
from . import windows  # noqa: F401


dialogs = [Dialog(windows.send_query_window, windows.show_ai_answer_window)]