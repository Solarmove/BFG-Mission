from pprint import pprint

from aiogram.enums import ContentType
from aiogram_dialog import StartMode, Window, Data, DialogManager
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Next, Start
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format, Multi, List, Const
from magic_filter import F

from ...i18n.utils.i18n_format import I18nFormat
from ...utils.calendar import CustomCalendar
from ..categories_menu_dialogs.keyboards import select_category_keyboard
from ..main_menu_dialogs.states import MainMenu
from . import getters, keyboards, on_clicks, states

create_task_menu_window = Window(
    I18nFormat("select-type-task-creation-text"),
    keyboards.create_task_menu_kb(),
    Cancel(I18nFormat("back-btn")),
    state=states.CreateTaskMenu.select_action,
    getter=getters.get_user_hierarchy,
)

enter_task_title_window = Window(
    I18nFormat("enter-task-title-text"),
    Next(
        I18nFormat("next-btn"),
        id="create_new_category",
        when=F["dialog_data"]["title"],
    ),
    TextInput(
        id="task_title",
        on_success=on_clicks.on_enter_task_title,
    ),
    Cancel(I18nFormat("back-btn")),
    state=states.CreateSingleTask.enter_task_title,
)

enter_task_description_window = Window(
    I18nFormat("enter-task-description-text"),
    Next(
        I18nFormat("next-btn"),
        id="create_new_category",
        when=F["dialog_data"]["description"],
    ),
    TextInput(
        id="task_description",
        on_success=on_clicks.on_enter_task_description,
    ),
    Back(I18nFormat("back-btn")),
    state=states.CreateSingleTask.enter_task_description,
)


select_executor_window = Window(
    I18nFormat("select-executor-text"),
    Next(
        I18nFormat("next-btn"),
        id="create_new_category",
        when=F["dialog_data"]["executor_id"],
    ),
    keyboards.select_executor_keyboard(),
    Back(I18nFormat("back-btn")),
    state=states.CreateSingleTask.select_executor,
    getter=getters.get_executors_list,
)

select_start_date_window = Window(
    I18nFormat("select-start-date-text"),
    CustomCalendar(
        on_click=on_clicks.on_select_start_task_date, id="select_start_date"
    ),
    Next(
        I18nFormat("next-btn"),
        id="create_new_category",
        when=F["dialog_data"]["selected_start_date"],
    ),
    Back(I18nFormat("back-btn")),
    state=states.CreateSingleTask.select_start_date,
    getter=getters.get_start_date_getter,
)

enter_start_date_time_window = Window(
    I18nFormat("enter-start-date-time-text"),
    TextInput(
        id="start_date_time",
        on_success=on_clicks.on_enter_time_start,
    ),
    keyboards.quick_start_times_kb(),
    Next(
        I18nFormat("next-btn"),
        id="create_new_category",
        when=F["dialog_data"]["start_time"],
    ),
    Back(I18nFormat("back-btn")),
    state=states.CreateSingleTask.select_start_date_time,
    getter=getters.start_time_getter,
)


select_end_date_window = Window(
    I18nFormat("select-end-date-text"),
    Next(
        I18nFormat("next-btn"),
        id="create_new_category",
        when=F["dialog_data"]["selected_end_date"],
    ),
    CustomCalendar(on_click=on_clicks.on_select_end_task_date, id="select_end_date"),
    Back(I18nFormat("back-btn")),
    state=states.CreateSingleTask.select_end_date,
    getter=getters.get_end_date_getter,
)


enter_end_date_time_window = Window(
    I18nFormat("enter-end-date-time-text"),
    TextInput(
        id="end_date_time",
        on_success=on_clicks.on_enter_time_end,
    ),
    Next(
        I18nFormat("next-btn"),
        id="create_new_category",
        when=F["dialog_data"]["end_time"],
    ),
    Back(I18nFormat("back-btn")),
    state=states.CreateSingleTask.select_end_date_time,
    getter=getters.end_time_getter,
)


select_category_keyboard_window = Window(
    I18nFormat("select-category-text"),
    select_category_keyboard(on_clicks.on_select_category),
    Next(
        I18nFormat("next-btn"),
        id="create_new_category",
        when=F["dialog_data"]["category_id"],
    ),
    TextInput(
        id="new_category_name",
        on_success=on_clicks.on_enter_new_category_name,
    ),
    Back(I18nFormat("back-btn")),
    state=states.CreateSingleTask.select_category,
    getter=getters.get_categories_list_getter,
)


select_report_media_required_window = Window(
    I18nFormat("select-report-with-media-required-text"),
    Next(
        I18nFormat("next-btn"),
        id="create_new_category",
    ),
    keyboards.report_media_checkbox(),
    Back(I18nFormat("back-btn")),
    state=states.CreateSingleTask.report_with_media_required,
)

need_add_control_point_window = Window(
    Multi(
        I18nFormat("need-add-control-point-text"),
        Multi(
            Const("<blockquote><b>Контрольні точки:</b>"),
            List(
                Format("<i>{item}</i>"),
                items="task_control_points_text",
                id="task_control_points_list",
                # page_size=1,
            ),
            Const("</blockquote>"),
        ),
        sep="\n\n",
    ),
    keyboards.delete_control_points_kb(),
    Next(
        I18nFormat("next-btn"),
        id="create_new_category",
        when=F["dialog_data"]["task_control_points"].len() > 0,
    ),
    Next(
        I18nFormat("without-control-point-btn"),
        id="without_control_point",
        on_click=on_clicks.on_without_control_point,
        # when=F["dialog_data"]["task_control_points"].len() <= 0,
    ),
    Button(
        I18nFormat("add-control-point-btn"),
        id="add_control_point",
        on_click=on_clicks.on_add_control_point,
    ),
    Back(I18nFormat("back-btn")),
    state=states.CreateSingleTask.need_add_control_point,
    getter=getters.get_control_points,
)


done_create_single_task_window = Window(
    Multi(
        I18nFormat("done-create-single-task-text"),
        I18nFormat("new-task-data-text"),
        sep="\n\n",
    ),
    Start(
        I18nFormat("add-one-more-task-btn"),
        id="add_one_more_task",
        state=states.CreateSingleTask.enter_task_title,
    ),
    Start(
        I18nFormat("back-to-main-menu-btn"),
        id="back_to_main_menu",
        state=MainMenu.select_action,
        mode=StartMode.RESET_STACK,
    ),
    state=states.CreateSingleTask.done,
    getter=getters.save_task_before,
)


enter_cp_description_window = Window(
    I18nFormat("enter-control-point-description-text"),
    TextInput(
        id="control_point_description",
        on_success=on_clicks.on_enter_control_point_description,
    ),
    Cancel(I18nFormat("cancel-btn")),
    Back(
        I18nFormat("back-btn"),
        on_click=on_clicks.on_back_to_cp_description_window,
        when=F["dialog_data"]["task_control_points"].len() > 0,
    ),
    state=states.AddControlPoint.enter_description,
)


select_cp_deadline_date_window = Window(
    I18nFormat("select-control-point-deadline-date-text"),
    CustomCalendar(
        on_click=on_clicks.on_select_control_point_deadline_date,
        id="select_control_point_deadline_date",
    ),
    Back(I18nFormat("back-btn")),
    state=states.AddControlPoint.select_deadline_date,
    getter=getters.get_control_point_deadline_date_getter,
)

enter_cp_deadline_time_window = Window(
    I18nFormat("enter-control-point-deadline-time-text"),
    TextInput(
        id="control_point_deadline_time",
        on_success=on_clicks.on_enter_control_point_deadline_time,
    ),
    Back(I18nFormat("back-btn")),
    state=states.AddControlPoint.select_deadline_time,
)

add_more_cp_window = Window(
    I18nFormat("add-more-control-point-text"),
    Button(
        I18nFormat("add-another-control-point-btn"),
        id="add_another_control_point",
        on_click=on_clicks.on_add_another_control_point,
    ),
    Button(
        I18nFormat("done-btn"),
        id="done_add_control_point",
        on_click=on_clicks.on_done_add_control_point,
    ),
    Back(I18nFormat("back-btn")),
    Cancel(I18nFormat("cancel-btn")),
    state=states.AddControlPoint.add_more,
)


async def on_process_result(data: Data, result: dict, manager: DialogManager):
    pprint(result)
    if result:
        manager.dialog_data["task_control_points"] = result.get(
            "task_control_points", []
        )


send_regular_tasks_csv_file_window = Window(
    I18nFormat("send-regular-tasks-csv-file-text"),
    DynamicMedia(selector="csv_file"),
    MessageInput(
        func=on_clicks.on_send_csv_file_click, content_types=[ContentType.DOCUMENT]
    ),
    Cancel(I18nFormat("back-btn")),
    state=states.CreateRegularTasks.send_csv_file,
    getter=getters.excel_file_getter,
)


show_parse_regular_tasks_result_window = Window(
    Multi(
        I18nFormat("parse-regular-tasks-result-text"),
        Format(
            "Виправіть помилки у файлі знизу та надішліть його знову.",
            when="errors",
        ),
        sep="\n",
    ),
    Button(
        I18nFormat("delete-create-task-btn"),
        id="delete_create_task",
        on_click=on_clicks.on_delete_create_task,
        when=F["created_count"] > 0,
    ),
    DynamicMedia(selector="csv_file", when=F["csv_file"]),
    MessageInput(
        func=on_clicks.on_recheck_csv_file_click, content_types=[ContentType.DOCUMENT]
    ),
    Back(I18nFormat("back-btn")),
    Cancel(I18nFormat("back-to-main-menu-btn")),
    state=states.CreateRegularTasks.show_result,
    getter=getters.get_pared_data,
)
