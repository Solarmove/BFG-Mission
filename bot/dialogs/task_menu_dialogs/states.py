from aiogram.fsm.state import StatesGroup, State


class MyTasks(StatesGroup):
    """
    State group for managing personal tasks.

    This state group is used to manage personal tasks.
    """

    select_type_tasks = State()  # Active or Today or all
    select_task = State()  # Select task to edit
    show_task = State()


class CompleteTask(StatesGroup):
    """
    State group for completing a task.

    This state group is used to complete a task.
    """

    enter_report_text = State()  # Enter report text
    send_media = State()  # Send media files
    confirm_action = State()  # Confirm completion of task
