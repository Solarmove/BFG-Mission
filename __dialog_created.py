import os

STATES_IMPORTS = """from aiogram.fsm.state import StatesGroup, State # noqa: F401"""

ON_CLICKS_IMPORTS = """from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput # noqa: F401
from aiogram_dialog import DialogManager # noqa: F401"""

GETTERS_IMPORTS = """from aiogram_dialog import DialogManager # noqa: F401
from aiogram.types import User # noqa: F401"""

WINDOWS_IMPORTS = """from aiogram_dialog import Window # noqa: F401
from aiogram_dialog.widgets.kbd import Cancel, Back # noqa: F401
from aiogram_dialog.widgets.text import Const, Format # noqa: F401
from aiogram_dialog.widgets.input import TextInput, MessageInput # noqa: F401
from ...i18n.utils.i18n_format import I18nFormat # noqa: F401
from . import states, getters, keyboards, on_clicks  # noqa: F401
"""

KEYBOARDS_IMPORTS = """from aiogram_dialog.widgets.kbd import Row, Group, Column, ListGroup, ScrollingGroup, Select, Button, Cancel, Back # noqa: F401
from . import on_clicks, states  # noqa: F401"""

INIT_IMPORTS = """from aiogram_dialog import Dialog # noqa: F401
from . import windows # noqa: F401"""


def create_dialog_folder(folder_name: str):
    files_names = {
        "__init__.py",
        "windows.py",
        "states.py",
        "getters.py",
        "on_clicks.py",
        "keyboards.py",
    }
    imports_mapper = {
        "windows.py": WINDOWS_IMPORTS,
        "states.py": STATES_IMPORTS,
        "getters.py": GETTERS_IMPORTS,
        "on_clicks.py": ON_CLICKS_IMPORTS,
        "keyboards.py": KEYBOARDS_IMPORTS,
        "__init__.py": INIT_IMPORTS,
    }
    folder_path = os.path.join("bot", "dialogs", folder_name)
    os.makedirs(folder_path, exist_ok=True)
    for file_name in files_names:
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, "w") as f:
            f.write(imports_mapper[file_name])


def main():
    while True:
        folder_name = input("Enter the name of the dialog folder or 0 for exit: ")
        if folder_name == "0":
            print("Exiting...")
            break
        create_dialog_folder(folder_name)
        print(f"Dialog folder '{folder_name}' created successfully with files.")


if __name__ == "__main__":
    main()
