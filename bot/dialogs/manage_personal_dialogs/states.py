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



class ManageWorkSchedule(StatesGroup):
    """
    State group for managing work schedule.
    """

    select_action = State()  # Main menu state for work schedule management



class ChangeWorkScheduleMany(StatesGroup):
    """
    State group for changing work schedule in bulk.
    """


class ChangeWorkScheduleOne(StatesGroup):
    """
    State group for changing work schedule for one user.
    """

    select_user = State()  # State for selecting a user
    select_date = State()  # State for selecting a date
    select_time = State()  # State for selecting time
    confirm_change = State()  # State for confirming the change