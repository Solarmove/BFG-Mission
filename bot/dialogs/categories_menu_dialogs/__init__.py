from aiogram_dialog import Dialog  # noqa: F401
from . import windows  # noqa: F401


dialogs = [
    Dialog(
        windows.category_menu_window,
    ),
    Dialog(
        windows.create_category_window,
    ),
    Dialog(
        windows.edit_category_window,
        windows.enter_new_name_category_window,
        windows.done_edit_category_window,
    ),
    Dialog(
        windows.select_category_for_delete,
        windows.confirm_delete_category_window,
        windows.done_delete_category_window,
    ),
]
