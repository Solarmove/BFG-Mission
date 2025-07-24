from .main_menu_dialogs import dialogs as main_menu_dialogs
from .manage_personal_dialogs import dialogs as manage_personal_dialogs
from .categories_menu_dialogs import dialogs as categories_menu_dialogs
from .task_menu_dialogs import dialogs as task_menu_dialogs

dialog_routers = [
    *main_menu_dialogs,
    *task_menu_dialogs,
    *manage_personal_dialogs,
    *categories_menu_dialogs,
]
