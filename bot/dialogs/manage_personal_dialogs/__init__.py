from aiogram_dialog import Dialog  # noqa: F401
from . import windows  # noqa: F401


dialogs = [
    Dialog(
        windows.create_reg_link_window,
        windows.show_link,
    ),
    Dialog(windows.manage_work_schedule_window),
    Dialog(
        windows.select_month_for_load_schedule_window,
        windows.select_year_for_load_schedule_window,
        windows.load_schedule_many_window,
        windows.done_load_schedule_window,
        windows.error_load_work_schedule_window,
    ),
    Dialog(
        windows.select_month_for_show_work_schedule_window,
        windows.select_year_for_show_work_schedule_window,
        windows.show_work_schedule_window,
    ),
]
