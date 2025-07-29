from aiogram_dialog import Dialog, LaunchMode  # noqa: F401
from . import windows  # noqa: F401


dialogs = [
    Dialog(
        windows.enter_full_name_window,
    ),
    Dialog(windows.main_menu_window, launch_mode=LaunchMode.ROOT),
]
