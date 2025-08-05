from aiogram_dialog import Dialog, LaunchMode  # noqa: F401
from . import windows  # noqa: F401


dialogs = [
    Dialog(windows.create_task_menu_window),
    Dialog(
        windows.enter_task_title_window,
        windows.enter_task_description_window,
        windows.select_executor_window,
        windows.select_start_date_window,
        windows.enter_start_date_time_window,
        windows.select_end_date_window,
        windows.enter_end_date_time_window,
        windows.select_category_keyboard_window,
        windows.select_report_media_required_window,
        windows.need_add_control_point_window,
        windows.done_create_single_task_window,
        on_process_result=windows.on_process_result,
        launch_mode=LaunchMode.SINGLE_TOP,
    ),
    Dialog(
        windows.enter_cp_description_window,
        windows.select_cp_deadline_date_window,
        windows.enter_cp_deadline_time_window,
        windows.add_more_cp_window,
        on_process_result=windows.on_process_result,
    ),
    Dialog(
        windows.send_regular_tasks_csv_file_window,
        windows.show_parse_regular_tasks_result_window,
    ),
]
