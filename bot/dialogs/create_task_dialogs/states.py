from aiogram.fsm.state import StatesGroup, State


class CreateTaskMenu(StatesGroup):
    """
    State for the main menu of the task creation dialog.
    """

    select_action = State()


class CreateSingleTask(StatesGroup):
    enter_task_title = State()
    enter_task_description = State()
    select_executor = State()
    select_start_date = State()
    select_start_date_time = State()
    select_end_date = State()
    select_end_date_time = State()
    select_category = State()
    report_with_media_required = State()
    need_add_control_point = State()
    done = State()


class AddControlPoint(StatesGroup):
    """
    State for adding a control point to the task.
    """

    enter_description = State()
    select_deadline_date = State()
    select_deadline_time = State()
    add_more = State()


class CreateRegularTasks(StatesGroup):
    """
    State for creating multiple tasks.
    """

    ...
