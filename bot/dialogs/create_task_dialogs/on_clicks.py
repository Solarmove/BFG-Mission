import datetime
import os.path
from _pydatetime import date

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram_i18n import I18nContext
from arq import ArqRedis
from arq.jobs import Job

from scheduler.jobs import abort_jobs
from . import states, getters, on_clicks  # noqa: F401
from aiogram_dialog.widgets.kbd import Button, Select, ManagedCalendar, ManagedCheckbox  # noqa: F401
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput  # noqa: F401
from aiogram_dialog import DialogManager, ShowMode, ChatEvent  # noqa: F401

from ...db.models.models import WorkSchedule
from ...exceptions.user_exceptions import InvalidCSVFile
from ...keyboards.ai import exit_ai_agent_kb
from ...services.create_task_with_csv import parse_regular_tasks_csv
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


async def time_not_in_work_time_message(
    uow: UnitOfWork,
    message: Message | CallbackQuery,
    manager: DialogManager,
    i18n: I18nContext,
    date: str,
):
    user_work_schedule_on_date = (
        await uow.work_schedules.get_work_schedule_in_user_by_date(
            manager.dialog_data["executor_id"],
            datetime.datetime.strptime(date, "%Y-%m-%d").date(),
        )
    )
    text = i18n.get(
        "time-not-in-work-schedule-error",
        work_schedule_start_time=str(
            user_work_schedule_on_date.start_time.strftime("%H:%M")
        ),
        work_schedule_end_time=str(
            user_work_schedule_on_date.end_time.strftime("%H:%M")
        ),
    )
    if isinstance(message, Message):
        await message.answer(text)
    elif isinstance(message, CallbackQuery):
        await message.answer(text, show_alert=True)


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
        await time_not_in_work_time_message(
            uow,
            message,
            manager,
            i18n,
            manager.dialog_data["selected_start_date"],
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
        await time_not_in_work_time_message(
            uow,
            message,
            manager,
            i18n,
            manager.dialog_data["selected_end_date"],
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


async def on_select_time_start_now(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    quick_time = datetime.datetime.now()
    manager.dialog_data["start_time"] = quick_time.strftime("%H:%M")
    uow: UnitOfWork = manager.middleware_data["uow"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    if not await is_time_in_work_schedule(
        uow,
        quick_time.strftime("%H:%M"),
        manager.dialog_data["executor_id"],
        manager.dialog_data["selected_start_date"],
    ):
        await time_not_in_work_time_message(
            uow,
            call,
            manager,
            i18n,
            manager.dialog_data["selected_start_date"],
        )
        return
    await manager.next()


async def on_quick_time_15m(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    now = datetime.datetime.now()
    quick_time = now + datetime.timedelta(minutes=15)
    manager.dialog_data["start_time"] = quick_time.strftime("%H:%M")
    uow: UnitOfWork = manager.middleware_data["uow"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    if not await is_time_in_work_schedule(
        uow,
        quick_time.strftime("%H:%M"),
        manager.dialog_data["executor_id"],
        manager.dialog_data["selected_start_date"],
    ):
        await time_not_in_work_time_message(
            uow,
            call,
            manager,
            i18n,
            manager.dialog_data["selected_start_date"],
        )
        return
    await manager.next()


async def on_quick_time_30m(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    now = datetime.datetime.now()
    quick_time = now + datetime.timedelta(minutes=30)
    manager.dialog_data["start_time"] = quick_time.strftime("%H:%M")
    if not await is_time_in_work_schedule(
        uow,
        quick_time.strftime("%H:%M"),
        manager.dialog_data["executor_id"],
        manager.dialog_data["selected_start_date"],
    ):
        await time_not_in_work_time_message(
            uow,
            call,
            manager,
            i18n,
            manager.dialog_data["selected_start_date"],
        )
        return
    await manager.next()


async def on_quick_time_1h(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    now = datetime.datetime.now()
    quick_time = now + datetime.timedelta(hours=1)
    manager.dialog_data["start_time"] = quick_time.strftime("%H:%M")
    uow: UnitOfWork = manager.middleware_data["uow"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    if not await is_time_in_work_schedule(
        uow,
        quick_time.strftime("%H:%M"),
        manager.dialog_data["executor_id"],
        manager.dialog_data["selected_start_date"],
    ):
        await time_not_in_work_time_message(
            uow,
            call,
            manager,
            i18n,
            manager.dialog_data["selected_start_date"],
        )
        return
    await manager.next()


async def on_quick_time_2h(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    now = datetime.datetime.now()
    quick_time = now + datetime.timedelta(hours=2)
    manager.dialog_data["start_time"] = quick_time.strftime("%H:%M")
    uow: UnitOfWork = manager.middleware_data["uow"]
    i18n: I18nContext = manager.middleware_data["i18n"]
    if not await is_time_in_work_schedule(
        uow,
        quick_time.strftime("%H:%M"),
        manager.dialog_data["executor_id"],
        manager.dialog_data["selected_start_date"],
    ):
        await time_not_in_work_time_message(
            uow,
            call,
            manager,
            i18n,
            manager.dialog_data["selected_start_date"],
        )
        return
    await manager.next()


async def on_time_to_schedule_end(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    i18n: I18nContext = manager.middleware_data["i18n"]
    uow: UnitOfWork = manager.middleware_data["uow"]
    selected_end_date_str = manager.dialog_data.get("selected_end_date")
    selected_end_date = datetime.datetime.strptime(selected_end_date_str, "%Y-%m-%d")
    work_schedule_model: WorkSchedule = (
        await uow.work_schedules.get_work_schedule_in_user_by_date(
            manager.dialog_data["executor_id"],
            selected_end_date.date(),
        )
    )
    manager.dialog_data["end_time"] = work_schedule_model.end_time.strftime("%H:%M")
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
    await uow.commit()
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
    # await manager.next()


async def on_change_video_required(
    call: CallbackQuery,
    widget: ManagedCheckbox,
    manager: DialogManager,
):
    manager.dialog_data["video_required"] = not manager.dialog_data.get(
        "video_required", False
    )
    # await manager.next()


async def on_change_file_required(
    call: CallbackQuery,
    widget: ManagedCheckbox,
    manager: DialogManager,
):
    manager.dialog_data["file_required"] = not manager.dialog_data.get(
        "file_required", False
    )
    # await manager.next()


async def on_without_control_point(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    manager.dialog_data.pop("task_control_points", None)


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
    selected_cp_deadline_date = manager.dialog_data[
        "selected_control_point_deadline_date"
    ]
    task_end_datetime = datetime.datetime.strptime(
        manager.start_data["task_end_datetime"],
        "%Y-%m-%d %H:%M",
    )
    task_start_datetime = datetime.datetime.strptime(
        manager.start_data["task_start_datetime"], "%Y-%m-%d %H:%M"
    )
    if not await is_time_in_work_schedule(
        uow,
        message_text,
        manager.start_data["executor_id"],
        selected_cp_deadline_date,
    ):
        user_work_schedule_on_date = (
            await uow.work_schedules.get_work_schedule_in_user_by_date(
                manager.start_data["executor_id"],
                task_end_datetime.date(),
            )
        )
        await message.answer(
            i18n.get(
                "time-not-in-work-schedule-error",
                work_schedule_start_time=str(
                    user_work_schedule_on_date.start_time.strftime("%H:%M")
                ),
                work_schedule_end_time=str(
                    user_work_schedule_on_date.end_time.strftime("%H:%M")
                ),
            )
        )
        return
    if task_start_datetime.date() == task_end_datetime.date():
        entered_time = datetime.datetime.strptime(message_text, "%H:%M")
        if (
            entered_time.time() > task_end_datetime.time()
            or entered_time.time() < task_start_datetime.time()
        ):
            await message.answer(
                i18n.get(
                    "control-point-time-out-of-task-range-error",
                    task_start_datetime=task_start_datetime.strftime("%H:%M"),
                    task_end_datetime=task_end_datetime.strftime("%H:%M"),
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


async def on_send_csv_file_click(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
):
    if not message.document:
        await message.answer("Будь ласка, надішліть CSV файл.")
        return

    bot: Bot = manager.middleware_data["bot"]
    uow: UnitOfWork = manager.middleware_data["uow"]
    path_to_file = os.path.join(
        "csv_files", f"regular_tasks_{message.from_user.id}.csv"
    )
    await bot.download(
        message.document.file_id,
        os.path.join("csv_files", f"regular_tasks_{message.from_user.id}.csv"),
    )
    try:
        result = await parse_regular_tasks_csv(path_to_file, uow)
        create_notification_task_started
        create_notification_task_is_overdue
        create_notification_task_ending_soon
        manager.dialog_data["parsing_csv_result"] = result
    except InvalidCSVFile as e:
        await message.answer(f"Помилка в CSV файлі: \n\n<blockquote>{e}</blockquote>")
        return
    await manager.next()


async def on_recheck_csv_file_click(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    path_to_file = os.path.join(
        "csv_files", f"regular_tasks_{message.from_user.id}.csv"
    )
    try:
        result = await parse_regular_tasks_csv(path_to_file, uow)
        manager.dialog_data["parsing_csv_result"] = result
    except InvalidCSVFile as e:
        await message.answer(f"Помилка в CSV файлі: \n\n<blockquote>{e}</blockquote>")


async def on_delete_create_task(
    call: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    uow: UnitOfWork = manager.middleware_data["uow"]
    arq: ArqRedis = manager.middleware_data["arq"]
    parsing_csv_result = manager.dialog_data.get("parsing_csv_result", {})
    created_tasks_ids = parsing_csv_result.get('created_tasks_ids', [])
    try:
        for created_task_id in created_tasks_ids:
            await uow.tasks.delete_one(int(created_task_id))
            # await abort_jobs(created_task_id)
    except Exception as e:
        await call.answer(f"Помилка при видаленні завдань: {e}", show_alert=True)
        await uow.rollback()
        return
    await uow.commit()
    await call.answer("Завдання видалено", show_alert=True)