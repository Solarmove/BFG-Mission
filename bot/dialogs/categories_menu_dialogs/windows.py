from aiogram_dialog import Window  # noqa: F401
from aiogram_dialog.widgets.kbd import Cancel, Back, Button  # noqa: F401
from aiogram_dialog.widgets.text import Const, Format  # noqa: F401
from aiogram_dialog.widgets.input import TextInput, MessageInput  # noqa: F401
from . import states, getters, keyboards, on_clicks  # noqa: F401
from ...i18n.utils.i18n_format import I18nFormat

category_menu_window = Window(
    I18nFormat("category-menu-text"),
    keyboards.category_menu_keyboard(),
    Cancel(I18nFormat("back-btn")),
    state=states.CategoryMenu.select_action,
    getter=getters.category_menu_getter,
)


create_category_window = Window(
    I18nFormat("create-category-text"),
    TextInput(id="category_name", on_success=on_clicks.on_enter_category_name),
    Cancel(I18nFormat("cancel-btn")),
    state=states.CreateCategory.enter_category_name,
    getter=getters.category_menu_getter,
)


edit_category_window = Window(
    I18nFormat("edit-category-text"),
    keyboards.select_category_keyboard(on_clicks.on_select_category),
    Cancel(I18nFormat("cancel-btn")),
    state=states.EditCategory.select_category,
    getter=getters.categories_getter,
)

enter_new_name_category_window = Window(
    I18nFormat("enter-new-name-category-text"),
    TextInput(id="new_category_name", on_success=on_clicks.on_enter_new_category_name),
    Back(I18nFormat("cancel-btn")),
    state=states.EditCategory.enter_new_name,
)

done_edit_category_window = Window(
    I18nFormat("done-edit-category-text"),
    Cancel(I18nFormat("back-btn")),
    state=states.EditCategory.done,
    getter=getters.get_edited_category_getter,
)


select_category_for_delete = Window(
    I18nFormat("select-category-for-delete-text"),
    keyboards.select_category_keyboard(on_clicks.on_select_category),
    Cancel(I18nFormat("cancel-btn")),
    state=states.DeleteCategory.select_category,
    getter=getters.categories_getter,
)

confirm_delete_category_window = Window(
    I18nFormat("confirm-delete-category-text"),
    Button(
        I18nFormat("confirm-btn"),
        id="confirm_delete_category",
        on_click=on_clicks.on_confirm_delete_category,
    ),
    Back(I18nFormat("back-btn")),
    state=states.DeleteCategory.confirm_deletion,
    getter=getters.get_category_for_delete,
)

done_delete_category_window = Window(
    I18nFormat("done-delete-category-text"),
    Cancel(I18nFormat('close-btn')),
    state=states.DeleteCategory.done,
    getter=getters.get_category_for_delete,
)
