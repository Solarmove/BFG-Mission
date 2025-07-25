from aiogram.fsm.state import StatesGroup, State


class CreateTask(StatesGroup):
    """
    State group for creating a task.

    Creating task requires the user to enter a query.
    User needs to enter a query
    """

    enter_query = State()  # State for entering the task query


class MyTasks(StatesGroup):
    """
    State group for managing personal tasks.

    This state group is used to manage personal tasks.
    """

    select_type_tasks = State()  # Active or Today or all
    select_task = State()  # Select task to edit
    show_task = State()