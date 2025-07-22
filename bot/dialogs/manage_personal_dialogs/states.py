from aiogram.fsm.state import StatesGroup, State  # noqa: F401


class ManagePersonalMenu(StatesGroup):
    """
    State group for managing personal menu.
    """

    select_action = State()  # Main menu state for personal management


class CreateRegLink(StatesGroup):
    """
    State group for creating registration link.
    """

    select_position = State()  # State for selecting position
    show_link = State()  # State for showing the generated link