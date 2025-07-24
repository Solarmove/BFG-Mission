from aiogram.fsm.state import StatesGroup, State  # noqa: F401


class MainMenu(StatesGroup):
    """
    The main menu dialog states.
    """

    select_action = State()


class Registration(StatesGroup):
    enter_full_name = State()
    select_position = State()
