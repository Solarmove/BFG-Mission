import logging

from aiogram import Router, Bot
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager
from aiogram_i18n import I18nContext

from bot.db.models.models import Task, User
from bot.dialogs.task_menu_dialogs.states import MyTasks, CompleteTask
from bot.entities.shared import TaskReadExtended
from bot.services.log_service import LogService
from bot.services.mailing_service import send_message
from bot.utils.enum import TaskStatus
from bot.utils.unitofwork import UnitOfWork

router = Router()

logger = logging.getLogger(__name__)


@router.callback_query(lambda c: c.data.startswith("accept_task:"))
async def accept_task_callback(
    call: CallbackQuery,
    uow: UnitOfWork,
    i18n: I18nContext,
    bot: Bot,
    channel_log: LogService,
):
    task_id = int(call.data.split(":")[1])
    task_model_dict: dict = await uow.tasks.get_task_by_id(task_id)
    task_model_extended = TaskReadExtended.model_validate(task_model_dict)

    if task_model_extended.executor_id != call.from_user.id:
        await call.answer(i18n.get("task_not_for_you"), show_alert=True)
        return
    if task_model_extended.status != TaskStatus.NEW:
        await call.answer(i18n.get("task_already_accepted"), show_alert=True)
        return
    try:
        await uow.tasks.edit_one(id=task_id, data=dict(status=TaskStatus.IN_PROGRESS))
        await uow.commit()
    except Exception as e:
        logger.info(f"Error while confirming task: {e}")
        await call.answer(i18n.get("task-confirmed-error"))
        await channel_log.error(
            "Помилка при підтвердженні завдання",
            extra_info={
                "Завдання": task_model_extended.title,
                "Помилка": f"<blockquote>{e}</blockquote>",
                "Виконавець": task_model_extended.executor.full_name
                or task_model_extended.executor.full_name_tg,
            },
        )
        return
    await send_message(
        bot,
        task_model_extended.creator_id,
        text=i18n.get(
            "task-confirmed-notification",
            task_title=task_model_extended.title,
            executor_full_name=task_model_extended.executor.full_name
            or task_model_extended.executor.full_name_tg,
        ),
    )
    await call.answer(
        i18n.get("task-confirmed-alert", task_title=task_model_extended.title),
        show_alert=True,
    )
    await channel_log.info(
        "Завдання підтверджено",
        extra_info={
            "Завдання": task_model_extended.title,
            "Виконавець": task_model_extended.executor.full_name
            or task_model_extended.executor.full_name_tg,
        },
    )
    new_kb = InlineKeyboardBuilder()
    await call.message.edit_reply_markup(
        call.inline_message_id, reply_markup=new_kb.as_markup()
    )


@router.callback_query(lambda c: c.data.startswith("show_task:"))
async def show_task_callback(
    call: CallbackQuery,
    uow: UnitOfWork,
    dialog_manager: DialogManager,
    i18n: I18nContext,
):
    task_id = int(call.data.split(":")[1])
    task_model: Task = await uow.tasks.find_one(id=task_id)
    user_model: User = await uow.users.get_user_by_id(call.from_user.id)
    if (
        task_model.executor_id != call.from_user.id
        and task_model.creator_id != call.from_user.id
        and user_model.position.hierarchy_level != 1
    ):
        await call.answer(i18n.get("task_not_for_you"), show_alert=True)
        return
    await dialog_manager.start(MyTasks.show_task, data={"task_id": task_id})


@router.callback_query(lambda c: c.data.startswith("done_task:"))
async def done_task_callback(
    call: CallbackQuery,
    uow: UnitOfWork,
    dialog_manager: DialogManager,
    i18n: I18nContext,
):
    task_id = int(call.data.split(":")[1])
    task_model_dict: dict = await uow.tasks.get_task_by_id(task_id)
    task_model_extended = TaskReadExtended.model_validate(task_model_dict)

    if task_model_extended.executor_id != call.from_user.id:
        await call.answer(i18n.get("task_not_for_you"), show_alert=True)
        return
    if task_model_extended.status != TaskStatus.IN_PROGRESS:
        await call.answer(i18n.get("task_already_completed"), show_alert=True)
        return
    await dialog_manager.start(
        CompleteTask.enter_report_text,
        data={
            "task_id": task_id,
            "control_point_id": None,
            "photo_required": task_model_extended.photo_required,
            "video_required": task_model_extended.video_required,
            "file_required": task_model_extended.file_required,
            "title": task_model_extended.title,
        },
    )
