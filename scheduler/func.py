import logging

from aiogram import Bot

from bot.db.redis import get_user_locale
from bot.entities.shared import TaskReadExtended
from bot.utils.enum import TaskStatus
from bot.utils.unitofwork import UnitOfWork
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
    user_id: int,
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
    locale = await get_user_locale(user_id)
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
                user_id=user_id,
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

