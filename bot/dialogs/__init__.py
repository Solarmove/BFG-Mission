from .main_menu_dialogs import dialogs as main_menu_dialogs
from .manage_personal_dialogs import dialogs as manage_personal_dialogs
from .create_task_dialogs import dialogs as create_task_dialogs


dialog_routers = [
    *main_menu_dialogs,
    *manage_personal_dialogs,
    # *create_task_dialogs,
]
