from aiogram.enums import ContentType
from aiogram_dialog import Window  # noqa: F401
from aiogram_dialog.widgets.kbd import Cancel, Back, Url  # noqa: F401
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format  # noqa: F401
from aiogram_dialog.widgets.input import TextInput, MessageInput  # noqa: F401

from . import states, getters, keyboards, on_clicks  # noqa: F401
from ...i18n.utils.i18n_format import I18nFormat


create_reg_link_window = Window(
    I18nFormat("select-position-text"),
    keyboards.select_position_keyboard(),
    Cancel(I18nFormat("back-btn")),
    state=states.CreateRegLink.select_position,
    getter=getters.positions_getter,
)

show_link = Window(
    I18nFormat("show-reg-link-text"),
    Url(I18nFormat("send-reg-link-btn"), url=Format("{share_reg_link}")),
    Back(I18nFormat("back-btn")),
    state=states.CreateRegLink.show_link,
    getter=getters.get_reg_link,
)


manage_work_schedule_window = Window(
    I18nFormat("manage-work-schedule-text"),
    keyboards.manage_work_schedule_keyboard(),
    Cancel(I18nFormat("back-btn")),
    state=states.ManageWorkSchedule.select_action,
)


select_month_for_load_schedule_window = Window(
    I18nFormat("select-month-for-load-schedule-text"),
    keyboards.select_month_keyboard(),
    Cancel(I18nFormat("back-btn")),
    state=states.ChangeWorkSchedule.select_month,
    getter=getters.month_getter,
)


select_year_for_load_schedule_window = Window(
    I18nFormat("select-year-for-load-schedule-text"),
    keyboards.select_year_keyboard(),
    Back(I18nFormat("back-btn")),
    state=states.ChangeWorkSchedule.select_year,
    getter=getters.year_getter,
)


load_schedule_many_window = Window(
    DynamicMedia(selector="template_csv_file"),
    I18nFormat("send-excel-file-text"),
    MessageInput(
        func=on_clicks.on_send_csv_file_click, content_types=[ContentType.DOCUMENT]
    ),
    Back(I18nFormat("back-btn")),
    state=states.ChangeWorkSchedule.send_excel_file,
    getter=getters.excel_file_getter,
)


done_load_schedule_window = Window(
    I18nFormat("done-load-schedule-many-text"),
    Cancel(I18nFormat("back-btn")),
    state=states.ChangeWorkSchedule.done,
    getter=getters.load_schedule_data_getter,
)


error_load_work_schedule_window = Window(
    I18nFormat("error-load-work-schedule-many-text"),
    MessageInput(
        func=on_clicks.on_send_csv_file_click, content_types=[ContentType.DOCUMENT]
    ),
    Cancel(I18nFormat("back-btn")),
    state=states.ChangeWorkSchedule.error,
    getter=getters.load_schedule_data_getter,
)


select_month_for_show_work_schedule_window = Window(
    I18nFormat("select-month-for-show-work-schedule-text"),
    keyboards.select_month_keyboard(),
    Cancel(I18nFormat("back-btn")),
    state=states.ShowSchedule.select_month,
    getter=getters.month_getter,
)

select_year_for_show_work_schedule_window = Window(
    I18nFormat("select-year-for-show-work-schedule-text"),
    keyboards.select_year_keyboard(),
    Back(I18nFormat("back-btn")),
    state=states.ShowSchedule.select_year,
    getter=getters.year_getter,
)


show_work_schedule_window = Window(
    I18nFormat("show-work-schedule-text"),
    DynamicMedia(selector="work_schedule_csv_file"),
    Back(I18nFormat("back-btn")),
    state=states.ShowSchedule.show_schedule,
    getter=getters.work_schedule_getter,
)
