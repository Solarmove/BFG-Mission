from aiogram_dialog import Dialog
from . import windows


dialogs = [
    Dialog(
        windows.select_type_of_task_window,
        windows.select_task_window,
        windows.show_task_window,
    ),
    Dialog(
        windows.enter_report_text_window,
        windows.send_media_window,
        windows.confirm_complete_task_window,
    ),
]
