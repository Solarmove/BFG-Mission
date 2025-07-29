from aiogram.fsm.state import StatesGroup, State  # noqa: F401


class CategoryMenu(StatesGroup):
    """
    State group for managing task categories.
    """

    select_action = State()  # Main menu state for category management


class CreateCategory(StatesGroup):
    enter_category_name = State()  # State for entering category name


class EditCategory(StatesGroup):
    """
    State group for editing task categories.
    """

    select_category = State()  # State for selecting a category to edit
    enter_new_name = State()  # State for entering new category name
    done = State()


class DeleteCategory(StatesGroup):
    """
    State group for deleting task categories.
    """

    select_category = State()  # State for selecting a category to delete
    confirm_deletion = State()  # State for confirming deletion of the category
    done = State()  # State indicating deletion is complete
