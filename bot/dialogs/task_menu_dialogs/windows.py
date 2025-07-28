from aiogram.enums import ContentType
from aiogram_dialog import Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Next
from aiogram_dialog.widgets.media import DynamicMedia, MediaScroll
from aiogram_dialog.widgets.text import Format, Case
from magic_filter import F

from ...i18n.utils.i18n_format import I18nFormat
from . import getters, keyboards, on_clicks, states

select_type_of_task_window = Window(
    I18nFormat("select-type-of-task-text"),
    keyboards.select_type_of_task_keyboard(),
    Cancel(I18nFormat("back-btn")),
    state=states.MyTasks.select_type_tasks,
    getter=getters.get_selected_type_of_task,
)

select_task_window = Window(
    I18nFormat("select-task-text"),
    keyboards.select_task_keyboard(),
    Back(I18nFormat("back-btn")),
    state=states.MyTasks.select_task,
    getter=getters.my_tasks_getter,
)

show_task_window = Window(
    I18nFormat("show-task-text"),
    MediaScroll(
        DynamicMedia(selector="item"),
        id="report_media_scroll",
        items="report_media_list",
        when="report_media_list",
    ),
    keyboards.scroll_keyboard("report_media_scroll", Format("{current_page1}/{pages}")),
    keyboards.action_with_task_keyboard(),
    Back(I18nFormat("back-btn")),
    state=states.MyTasks.show_task,
    getter=getters.get_task,
)


enter_report_text_window = Window(
    I18nFormat("enter-report-text"),
    TextInput(
        id="report_text_input",
        on_success=on_clicks.on_enter_report_text,
    ),
    Cancel(I18nFormat("cancel-btn")),
    state=states.CompleteTask.enter_report_text,
)

send_media_window = Window(
    I18nFormat("send-media-for-report-text"),
    MessageInput(
        func=on_clicks.on_send_report_media,
        content_types=[ContentType.PHOTO, ContentType.VIDEO, ContentType.DOCUMENT],
    ),
    MediaScroll(
        DynamicMedia(selector="item"),
        id="report_media_scroll",
        items="report_media_list",
        when="report_media_list",
    ),
    Next(I18nFormat("skip-btn"), when="can_skip"),
    Button(
        I18nFormat("done-send-media-btn"),
        id="done_send_media",
        on_click=on_clicks.on_done_send_media,
        when=F["pages"] >= 1,
    ),
    keyboards.scroll_keyboard("report_media_scroll"),
    Button(
        Format("{delete_media}"),
        id="delete_media",
        on_click=on_clicks.on_delete_media,
        when=F["pages"] >= 1,
    ),
    Back(I18nFormat("back-btn")),
    state=states.CompleteTask.send_media,
    getter=getters.get_sent_media,
)


confirm_complete_task_window = Window(
    Case(
        {
            True: I18nFormat(
                "confirm-complete-task-text-control-point"
            ),
            False: I18nFormat("confirm-complete-task-text"),
        },
        selector='control_point_exist',
    ),
    Button(
        I18nFormat("confirm-btn"),
        id="confirm_complete_task",
        on_click=on_clicks.on_confirm_complete_task_click,
    ),
    Back(I18nFormat("back-btn")),
    state=states.CompleteTask.confirm_action,
    getter=getters.get_task_before_complete,
)
