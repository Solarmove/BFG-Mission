import datetime
import logging
from typing import Literal, TypeAlias, Any, Coroutine

import pytz
from arq import ArqRedis
from arq.jobs import Job

from bot.db.redis import redis
from bot.services.log_service import LogService

logger = logging.getLogger(__name__)

NOTIFICATION_SUBJECTS: TypeAlias = Literal[
    "task_ending_soon", "task_overdue", "task_started", "task_updated"
]

NOTIFICATION_FOR: TypeAlias = Literal["creator", "executor"]


async def create_notification_job(
    arq: ArqRedis,
    notification_for: NOTIFICATION_FOR,
    notification_subject: NOTIFICATION_SUBJECTS,
    user_id: int,
    task_id: int,
    _defer_until: datetime.datetime | None = None,
    _defer_by: datetime.timedelta | None = None,
    update_notification: bool = False,
) -> str | None:
    """
    Створює завдання для надсилання сповіщення користувачу по задач

    Args:
        arq (ArqRedis): Підключення до Redis.
        notification_for (Literal['creator', 'executor']): Тип сповіщення - для творця або виконавця завдання.
        notification_subject (Literal['task_ending_soon', 'task_overdue', 'task_started']): Тема сповіщення.
            Визначає, про що саме буде сповіщення.
            - 'task_ending_soon': Завдання, яке скоро закінчується.
            - 'task_overdue': Завдання, яке прострочено.
            - 'task_started': Завдання, яке почалося.
        user_id (int): ID користувача, якому буде надіслано сповіщення.
        task_id (int): ID завдання, про яке буде надіслано сповіщення.
        _defer_until (datetime.datetime | None): Час, до якого слід відкласти виконання завдання.
            Якщо вказано, то завдання буде виконано в цей час.
        _defer_by (datetime.timedelta | None): Час, на який слід від відкласти виконання завдання.
            Якщо вказано, то завдання буде виконано через цей проміжок часу.
        update_notification (bool): Якщо True, то оновлює існуюче сповіщення, якщо воно вже є.
            Якщо False, то створює нове сповіщення. Якщо сповіщення вже існує - нове сповіщення не буде створено.
    """
    log_service = LogService()
    tz_info = pytz.timezone("Europe/Kyiv")
    datetime_now = datetime.datetime.now(tz_info)
    if _defer_until.tim and datetime_now > _defer_until:
        await log_service.warning(
            "Завдання не може бути створено, оскільки час відкладання вже минув.",
            extra_info={
                "DEFER_UNTIL": _defer_until,
                "CURRENT_TIME": datetime_now,
                "USER_ID": user_id,
                "TASK_ID": task_id,
                "NOTIFICATION_FOR": notification_for,
                "NOTIFICATION_SUBJECT": notification_subject,
            },
        )
        return "Завдання не може бути створено, оскільки час відкладання вже минув."
    if _defer_by and _defer_by.total_seconds() < 0:
        await log_service.warning(
            "Завдання не може бути створено, оскільки час відкладання не може бути від'ємним.",
            extra_info={
                "DEFER_BY": _defer_by,
                "USER_ID": user_id,
                "TASK_ID": task_id,
                "NOTIFICATION_FOR": notification_for,
                "NOTIFICATION_SUBJECT": notification_subject,
            },
        )
        return "Завдання не може бути створено, оскільки час відкладання не може бути від'ємним."
    job_id = (
        f"notification_{notification_for}_{notification_subject}_{user_id}_{task_id}"
    )
    if update_notification:
        existing_job = Job(job_id=job_id, redis=redis)
        result = await existing_job.abort()
        if not result:
            logger.warning(
                "Failed to update notification job, it may not exist or is already completed."
            )
            await log_service.warning(
                "Failed to update notification job, it may not exist or is already completed.",
                extra_info={"JOB_ID": job_id},
            )
    try:
        await arq.enqueue_job(
            "send_notification",
            _job_id=job_id,
            _defer_until=_defer_until,
            _defer_by=_defer_by,
            user_id=user_id,
            task_id=task_id,
            notification_for=notification_for,
            notification_subject=notification_subject,
        )
    except Exception as e:
        logger.error(
            f"Failed to create notification job {job_id} for user {user_id} and task {task_id}: {e}"
        )
        await log_service.log_exception(
            e,
            context="Створення нотифікаії",
            extra_info={
                "JOB_ID": job_id,
                "USER_ID": user_id,
                "TASK_ID": task_id,
                "NOTIFICATION_FOR": notification_for,
                "NOTIFICATION_SUBJECT": notification_subject,
            },
        )
        raise e
