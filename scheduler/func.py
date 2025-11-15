import datetime
import logging

from aiogram import Bot

from bot.entities.shared import TaskReadExtended
from bot.services.ai_agent.tools import TaskTools
from bot.utils.enum import TaskStatus
from bot.utils.unitofwork import UnitOfWork
from configreader import KYIV
from scheduler.jobs import NOTIFICATION_FOR, NOTIFICATION_SUBJECTS
from scheduler.services import (
    send_task_ending_soon_notification,
    send_task_overdue_notification,
    send_task_started_notification,
    send_task_updated_notification,
    send_task_created_notification,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def send_notification(
    ctx: dict,
    task_id: int,
    notification_for: NOTIFICATION_FOR,
    notification_subject: NOTIFICATION_SUBJECTS,
):
    """
    Sends a notification to the user.

    Args:
        ctx (dict): Context dictionary containing the necessary parts.
        user_id (int): ID of the user to notify.
        task_id (int): ID of the task related to the notification.
        notification_for (Literal["creator", "executor"]): Specifies whether the notification is for the task creator or executor.
        notification_subject (Literal["task_ending_soon", "task_overdue", "task_started"]):
            Specifies the subject of the notification.
            - 'task_ending_soon': Notification for tasks that are ending soon.
            - 'task_overdue': Notification for overdue tasks.
            - 'task_started': Notification for tasks that have started.
    """
    bot: Bot = ctx["bot"]
    uow = UnitOfWork()
    core = ctx["core"]
    locale = "uk"
    async with uow:
        task_model_dict = await uow.tasks.get_task_by_id(task_id, update_cache=True)
        if not task_model_dict:
            logger.warning(f"Task with ID {task_id} not found in the database.")
            return
        task_model_extended = TaskReadExtended.model_validate(task_model_dict)
        if task_model_extended.status in [
            TaskStatus.COMPLETED,
            TaskStatus.CANCELED,
        ]:
            logger.info(
                f"Task {task_model_extended.id} is already completed or canceled, skipping notification."
            )
            return
        if notification_subject == "task_ending_soon":
            await send_task_ending_soon_notification(
                task_model_extended=task_model_extended,
                core=core,
                bot=bot,
            )
        elif notification_subject == "task_overdue":
            await send_task_overdue_notification(
                task_model_extended=task_model_extended,
                notification_for=notification_for,
                locale=locale,
                core=core,
                bot=bot,
            )
        elif notification_subject == "task_started":
            await send_task_started_notification(
                task_model_extended=task_model_extended,
                core=core,
                bot=bot,
            )
        elif notification_subject == "task_updated":
            await send_task_updated_notification(
                task_model_extended=task_model_extended,
                core=core,
                bot=bot,
            )
        elif notification_subject == "task_created":
            await send_task_created_notification(
                task_model_extended=task_model_extended,
                core=core,
                bot=bot,
            )


async def create_task_from_regular(ctx):
    uow = UnitOfWork()

    async with uow:
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year
        all_regulars_tasks = await uow.regular_tasks.get_all_regular_tasks(
            month=month, year=year
        )
        now = datetime.datetime.now(KYIV)
        for task in all_regulars_tasks:
            task_start_date = datetime.datetime.combine(now.date(), task.start_time)
            task_end_date = datetime.datetime.combine(now.date(), task.end_time)
            is_user_work = await uow.work_schedules.is_user_work_in_this_time(
                user_id=task.executor_id,
                date=task_start_date.date(),
                time_from=task_start_date.time(),
                time_to=task_end_date.time(),
            )
            if not is_user_work:
                continue
            task_start_date = datetime.datetime.combine(
                task_start_date.date(), task_start_date.time()
            )
            task_end_date = datetime.datetime.combine(
                task_end_date.date(), task_end_date.time()
            )
            task_create = dict(
                creator_id=task.creator_id,  # User creates their own regular task
                executor_id=task.executor_id,
                title=task.title,
                description=task.description,
                start_datetime=task_start_date,
                end_datetime=task_end_date,
                category_id=task.category_id,
                photo_required=task.photo_required,
                video_required=task.video_required,
                file_required=task.file_required,
            )
            task_id = await uow.tasks.add_one(task_create)

            # Add task to database
            task_tools = TaskTools(
                uow=uow,
                arq=ctx["redis"],
                user_id=task.executor_id,
            )

            await uow.session.flush()
            await uow.session.commit()
            await task_tools.create_notification_task_started(
                task_id,
                _defer_until=task_start_date,
            )
            await task_tools.create_notification_task_is_overdue(
                task_id,
                _defer_until=task_end_date,
            )
            await task_tools.create_notification_task_ending_soon(
                task_id,
                _defer_until=task_end_date - datetime.timedelta(minutes=30),
            )
