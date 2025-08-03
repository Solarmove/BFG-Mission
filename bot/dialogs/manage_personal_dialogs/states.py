from aiogram.fsm.state import StatesGroup, State


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


class ChangeWorkSchedule(StatesGroup):
    """
    State group for changing work schedule in bulk.
    """

    select_month = State()
    select_year = State()
    send_excel_file = State()  # State for sending Excel file
    done = State()
    error = State()


class ShowSchedule(StatesGroup):
    """
    State group for showing work schedule.
    """

    select_month = State()
    select_year = State()
    show_schedule = State()
