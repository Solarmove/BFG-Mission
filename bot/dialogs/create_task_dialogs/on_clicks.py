import datetime
from _pydatetime import date

from aiogram.exceptions import TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram_i18n import I18nContext

from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select, ManagedCalendar, ManagedCheckbox  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager, ShowMode, ChatEvent  # noqa: F401

from ...keyboards.ai import exit_ai_agent_kb
from ...states.ai import AIAgentMenu
from ...utils.unitofwork import UnitOfWork


async def on_start_create_task(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    await manager.done(show_mode=ShowMode.NO_UPDATE)
    state: FSMContext = manager.middleware_data["state"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    try:
        await call.message.edit_text(
            i18n.get("ai-agent-create-task-text"),
            reply_markup=exit_ai_agent_kb().as_markup(),
        )
    except TelegramRetryAfter:
        await call.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[]])
        )
        await call.message.answer(
            i18n.get("ai-agent-create-task-text"),
            reply_markup=exit_ai_agent_kb().as_markup(),
        )

    await state.set_state(AIAgentMenu.send_query)
    call_data = {
        "message_id": call.message.message_id,
        "inline_message_id": call.inline_message_id,
    }
    await state.set_data({"prompt": "create_task_prompt", "call_data": call_data})


async def on_enter_task_title(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    message_text: str,
):
    i18n: I18nContext = manager.middleware_data["i18n"]
    if len(message_text) > 255:
        await message.answer(i18n.get("task-title-too-long-error"))
        return
    manager.dialog_data["title"] = message_text
    await manager.next()


async def on_enter_task_description(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    message_text: str,
):
    i18n: I18nContext = manager.middleware_data["i18n"]
    if len(message_text) > 600:
        await message.answer(i18n.get("task-description-too-long-error"))
        return
    manager.dialog_data["description"] = message_text
    await manager.next()


async def on_select_executor(
    call: CallbackQuery, widget: Select, manager: DialogManager, item_id: int
):
    manager.dialog_data["executor_id"] = item_id
    await manager.next()


async def on_select_start_task_date(
    call: ChatEvent,
    widget: ManagedCalendar,
    manager: DialogManager,
    selected_date: date,
    /,
):
    manager.dialog_data["selected_start_date"] = str(selected_date)
    await manager.next()


def validate_time_format(time_str: str) -> bool:
    try:
        # Attempt to parse the time string
        datetime.datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


async def is_time_in_work_schedule(
    uow: UnitOfWork, entered_time: str, executor_id: int, selected_date: str
) -> bool:
    # Convert entered_time to datetime object
    entered_time = datetime.datetime.strptime(entered_time, "%H:%M").time()
    selected_date = datetime.datetime.strptime(selected_date, "%Y-%m-%d").date()
    # start_task_date = datetime.datetime.combine(selected_date, entered_time)
    # Get the work schedule for the executor on the selected date
    work_schedule = await uow.work_schedules.get_work_schedule_in_user_by_date(
        executor_id, selected_date, start_time=entered_time
    )
    if not work_schedule:
        return False
    return True


async def on_enter_time_start(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    message_text: str,
):
    i18n: I18nContext = manager.middleware_data["i18n"]
    uow: UnitOfWork = manager.middleware_data["uow"]
    if not validate_time_format(message_text):
        await message.answer(i18n.get("invalid-time-format-error"))
        return
    if not await is_time_in_work_schedule(
        uow,
        message_text,
        manager.dialog_data["executor_id"],
        manager.dialog_data["selected_start_date"],
    ):
        user_work_schedule_on_date = (
            await uow.work_schedules.get_work_schedule_in_user_by_date(
                manager.dialog_data["executor_id"],
                datetime.datetime.strptime(
                    manager.dialog_data["selected_start_date"], "%Y-%m-%d"
                ).date(),
            )
        )
        await message.answer(
            i18n.get(
                "time-not-in-work-schedule-error",
                work_schedule_start_time=user_work_schedule_on_date.start_time,
                work_schedule_end_time=user_work_schedule_on_date.end_time,
            )
        )
        return

    manager.dialog_data["start_time"] = message_text
    await manager.next()


async def on_select_end_task_date(
    call: ChatEvent,
    widget: ManagedCalendar,
    manager: DialogManager,
    selected_date: date,
    /,
):
    manager.dialog_data["selected_end_date"] = str(selected_date)
    await manager.next()


async def on_enter_time_end(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    message_text: str,
):
    i18n: I18nContext = manager.middleware_data["i18n"]
    uow: UnitOfWork = manager.middleware_data["uow"]
    if not validate_time_format(message_text):
        await message.answer(i18n.get("invalid-time-format-error"))
        return
    if not await is_time_in_work_schedule(
        uow,
        message_text,
        manager.dialog_data["executor_id"],
        manager.dialog_data["selected_end_date"],
    ):
        user_work_schedule_on_date = (
            await uow.work_schedules.get_work_schedule_in_user_by_date(
                manager.dialog_data["executor_id"],
                datetime.datetime.strptime(
                    manager.dialog_data["selected_end_date"], "%Y-%m-%d"
                ).date(),
            )
        )
        await message.answer(
            i18n.get(
                "time-not-in-work-schedule-error",
                work_schedule_start_time=user_work_schedule_on_date.start_time,
                work_schedule_end_time=user_work_schedule_on_date.end_time,
            )
        )
        return
    start_date_str = manager.dialog_data["selected_start_date"]
    end_date_str = manager.dialog_data["selected_end_date"]
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
    if start_date == end_date:
        start_time = manager.dialog_data["start_time"]
        t_start_time = datetime.datetime.strptime(start_time, "%H:%M")
        t_end_time = datetime.datetime.strptime(message_text, "%H:%M")
        if t_end_time < t_start_time:
            await message.answer(i18n.get("end-time-before-start-time-error"))
            return
    manager.dialog_data["end_time"] = message_text
    await manager.next()


async def on_select_category(
    call: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: int,
):
    manager.dialog_data["category_id"] = item_id
    await manager.next()


async def on_enter_new_category_name(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    message_text: str,
):
    i18n: I18nContext = manager.middleware_data["i18n"]
    if len(message_text) > 50:
        await message.answer(i18n.get("category-name-too-long-error"))
        return
    uow: UnitOfWork = manager.middleware_data["uow"]
    category_id = await uow.task_categories.add_one(dict(name=message_text))
    manager.dialog_data["category_id"] = category_id
    await manager.next()


async def on_change_photo_required(
    call: CallbackQuery,
    widget: ManagedCheckbox,
    manager: DialogManager,
):
    manager.dialog_data["photo_required"] = not manager.dialog_data.get(
        "photo_required", False
    )
    await manager.next()


async def on_change_video_required(
    call: CallbackQuery,
    widget: ManagedCheckbox,
    manager: DialogManager,
):
    manager.dialog_data["video_required"] = not manager.dialog_data.get(
        "video_required", False
    )
    await manager.next()


async def on_change_file_required(
    call: CallbackQuery,
    widget: ManagedCheckbox,
    manager: DialogManager,
):
    manager.dialog_data["file_required"] = not manager.dialog_data.get(
        "file_required", False
    )
    await manager.next()


async def on_without_control_point(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    manager.dialog_data.pop("control_point_id", None)


async def on_add_control_point(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    task_data = manager.dialog_data
    await manager.start(
        states.AddControlPoint.enter_description,
        data={
            "task_start_datetime": f"{task_data['selected_start_date']} {task_data['start_time']}",
            "task_end_datetime": f"{task_data['selected_end_date']} {task_data['end_time']}",
            "executor_id": task_data["executor_id"],
        },
    )


async def on_enter_control_point_description(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    message_text: str,
):
    i18n: I18nContext = manager.middleware_data["i18n"]
    if len(message_text) > 500:
        await message.answer(i18n.get("task-description-too-long-error"))
        return
    manager.dialog_data["control_point_description"] = message_text
    await manager.next()


async def on_select_control_point_deadline_date(
    call: ChatEvent,
    widget: ManagedCalendar,
    manager: DialogManager,
    selected_date: date,
    /,
):
    manager.dialog_data["selected_control_point_deadline_date"] = str(selected_date)
    await manager.next()


async def on_enter_control_point_deadline_time(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    message_text: str,
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    if not validate_time_format(message_text):
        await message.answer(i18n.get("invalid-time-format-error"))
        return
    if not await is_time_in_work_schedule(
        uow,
        message_text,
        manager.start_data["executor_id"],
        manager.dialog_data["selected_control_point_deadline_date"],
    ):
        user_work_schedule_on_date = (
            await uow.work_schedules.get_work_schedule_in_user_by_date(
                manager.dialog_data["executor_id"],
                datetime.datetime.strptime(
                    manager.dialog_data["selected_end_date"], "%Y-%m-%d"
                ).date(),
            )
        )
        await message.answer(
            i18n.get(
                "time-not-in-work-schedule-error",
                work_schedule_start_time=user_work_schedule_on_date.start_time,
                work_schedule_end_time=user_work_schedule_on_date.end_time,
            )
        )
        return
    manager.dialog_data["control_point_deadline_time"] = message_text
    await manager.next()


async def on_add_another_control_point(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    task_data = manager.dialog_data
    task_control_points = await add_cp_to_list(task_data)
    manager.dialog_data["task_control_points"] = task_control_points
    await manager.switch_to(states.AddControlPoint.enter_description)


async def add_cp_to_list(task_data: dict):
    task_data.setdefault("task_control_points", []).append(
        {
            "description": task_data.get(
                "control_point_description", "Контрольна точка"
            ),
            "deadline": f"{task_data['selected_control_point_deadline_date']} {task_data['control_point_deadline_time']}",
        }
    )
    task_control_points = task_data.get("task_control_points", [])
    return task_control_points


async def on_done_add_control_point(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    task_data = manager.dialog_data
    task_control_points = await add_cp_to_list(task_data)
    await manager.done(result={"task_control_points": task_control_points})


async def on_back_to_cp_description_window(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    task_data = manager.dialog_data
    task_control_points = task_data.get("task_control_points", [])
    del task_control_points[-1]
    manager.dialog_data["task_control_points"] = task_control_points


async def on_select_time_start_now(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    now = datetime.datetime.now()
    manager.dialog_data["start_time"] = now.strftime("%H:%M")
    await manager.next()


async def on_quick_time_15m(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    now = datetime.datetime.now()
    quick_time = now + datetime.timedelta(minutes=15)
    manager.dialog_data["start_time"] = quick_time.strftime("%H:%M")
    await manager.next()


async def on_quick_time_30m(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    now = datetime.datetime.now()
    quick_time = now + datetime.timedelta(minutes=30)
    manager.dialog_data["start_time"] = quick_time.strftime("%H:%M")
    await manager.next()


async def on_quick_time_1h(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    now = datetime.datetime.now()
    quick_time = now + datetime.timedelta(hours=1)
    manager.dialog_data["start_time"] = quick_time.strftime("%H:%M")
    await manager.next()


async def on_quick_time_2h(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    now = datetime.datetime.now()
    quick_time = now + datetime.timedelta(hours=2)
    manager.dialog_data["start_time"] = quick_time.strftime("%H:%M")
    await manager.next()


async def on_time_to_schedule_end(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    executor_id = manager.dialog_data["executor_id"]
    selected_date = manager.dialog_data["selected_start_date"]
    work_schedule = await uow.work_schedules.get_work_schedule_in_user_by_date(
        executor_id, datetime.datetime.strptime(selected_date, "%Y-%m-%d").date()
    )
    if not work_schedule:
        await call.answer("Робочий графік не знайдено.", show_alert=True)
        return
    manager.dialog_data["start_time"] = str(work_schedule.end_time)
    await manager.next()


async def on_delete_control_point(
    call: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: int,
):
    task_data = manager.dialog_data
    task_control_points = task_data.get("task_control_points", [])
    if 0 <= item_id < len(task_control_points):
        del task_control_points[item_id]
        manager.dialog_data["task_control_points"] = task_control_points
        await call.answer("🗑️Контрольна точка видалена")
