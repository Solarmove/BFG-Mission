import datetime
import logging

from langchain_core.tools import tool

from bot.db.models.models import Task
from bot.db.redis import redis_cache
from bot.entities.shared import TaskReadExtended
from bot.entities.task import (
    TaskCreate,
    TaskUpdate,
)
from bot.utils.enum import TaskStatus
from configreader import KYIV
from scheduler.jobs import create_notification_job
from .base import BaseTools

logger = logging.getLogger(__name__)


class TaskTools(BaseTools):
    """Інструменти для роботи з завданнями."""

    async def create_notification_new_task(
        self,
        task_id: int,
        user_id: int,
    ):
        """
        Creates a notification for a newly created task.

        This method triggers an asynchronous job to create a notification
        related to a newly created task. The notification is specifically
        for the task creator and is categorized under the subject "new_task".

        Parameters:
        task_id: int
            The unique identifier of the task for which the notification
            is created.
        user_id: int
            The unique identifier of the user who created the task.
        """
        await create_notification_job(
            self.arq,
            notification_for="executor",
            notification_subject="task_created",
            user_id=user_id,
            task_id=task_id,
        )

    async def create_notification_task_started(
        self,
        task_id: int,
        user_id: int,
        _defer_until: datetime.datetime | None = None,
        _defer_by: datetime.timedelta | None = None,
        update_notification: bool = False,
    ):
        """
        Створює завдання для надсилання сповіщення користувачу про те, що завдання почалося.
        Args:
            task_id (int): ID завдання, про яке буде надіслано сповіщення.
            user_id (int): ID користувача, якому буде надіслано сповіщення.
            _defer_until (datetime.datetime | None): Час, до якого слід відкласти виконання завдання.
                Якщо вказано, то завдання буде виконано в цей час.
            _defer_by (datetime.timedelta | None): Час, на який слід відкласти виконання завдання.
                Якщо вказано, то завдання буде виконано через цей проміжок часу.
            update_notification: bool: True - для того щоб оновити існуюче сповіщення, якщо ми оновили завдання.
                False - для того щоб створити нове сповіщення.

            Якщо не вказати _defer_until та _defer_by - повідомлення буде надіслано відразу.

        """
        await create_notification_job(
            self.arq,
            notification_for="executor",
            notification_subject="task_started",
            user_id=user_id,
            task_id=task_id,
            _defer_until=_defer_until,
            _defer_by=_defer_by,
            update_notification=update_notification,
        )

    async def create_notification_task_updated(
        self,
        task_id: int,
        user_id: int,
    ):
        """
        Створює завдання для надсилання сповіщення користувачу про те, що завдання оновлено.
        Args:
            task_id (int): ID завдання, про яке буде надіслано сповіщення.
            user_id (int): ID користувача, якому буде надіслано сповіщення.

            Якщо не вказати _defer_until та _defer_by - повідомлення буде надіслано відразу.

        """
        await create_notification_job(
            self.arq,
            notification_for="executor",
            notification_subject="task_updated",
            user_id=user_id,
            task_id=task_id,
        )

    async def create_notification_task_is_overdue(
        self,
        task_id: int,
        executor_id: int,
        creator_id: int,
        _defer_until: datetime.datetime | None = None,
        _defer_by: datetime.timedelta | None = None,
        update_notification: bool = False,
    ):
        """
        Створює завдання для надсилання сповіщення користувачу про те, що завдання прострочено.
        Args:
            task_id (int): ID завдання, про яке буде надіслано сповіщення.
            executor_id (int): ID виконавця завдання, якому буде надіслано сповіщення.
            creator_id (int): ID творця завдання, якому буде надіслано сповіщення.
            _defer_until (datetime.datetime | None): Час, до якого слід відкласти виконання завдання.
                Якщо вказано, то завдання буде виконано в цей час.
            _defer_by (datetime.timedelta | None): Час, на який слід відкласти виконання завдання.
                Якщо вказано, то завдання буде виконано через цей проміжок часу.
            update_notification: bool: True - для того щоб оновити існуюче сповіщення, якщо ми оновили завдання.
                False - для того щоб створити нове сповіщення.

            Якщо не вказати _defer_until та _defer_by - повідомлення буде надіслано відразу.

        """
        await create_notification_job(
            self.arq,
            notification_for="executor",
            notification_subject="task_overdue",
            user_id=executor_id,
            task_id=task_id,
            _defer_until=_defer_until,
            _defer_by=_defer_by,
            update_notification=update_notification,
        )
        await create_notification_job(
            self.arq,
            notification_for="creator",
            notification_subject="task_overdue",
            user_id=creator_id,
            task_id=task_id,
            _defer_until=_defer_until,
            _defer_by=_defer_by,
            update_notification=update_notification,
        )

    async def create_notification_task_ending_soon(
        self,
        task_id: int,
        user_id: int,
        _defer_until: datetime.datetime | None = None,
        _defer_by: datetime.timedelta | None = None,
        update_notification: bool = False,
    ):
        """
        Створює завдання для надсилання сповіщення користувачу про те, що завдання закінчується незабаром.
        Args:
            task_id (int): ID завдання, про яке буде надіслано сповіщення.
            user_id (int): ID користувача, якому буде надіслано сповіщення.
            _defer_until (datetime.datetime | None): Час, до якого слід відкласти виконання завдання.
                Якщо вказано, то завдання буде виконано в цей час.
            _defer_by (datetime.timedelta | None): Час, на який слід відкласти виконання завдання.
                Якщо вказано, то завдання буде виконано через цей проміжок часу.
            update_notification: bool: True - для того щоб оновити існуюче сповіщення, якщо ми оновили завдання.
                False - для того щоб створити нове сповіщення.


            Якщо не вказати _defer_until та _defer_by - повідомлення буде надіслано відразу.

        """
        await create_notification_job(
            self.arq,
            notification_for="executor",
            notification_subject="task_ending_soon",
            user_id=user_id,
            task_id=task_id,
            _defer_until=_defer_until,
            _defer_by=_defer_by,
            update_notification=update_notification,
        )

    async def create_one_task_func(self, new_task_data: TaskCreate):
        new_task_data.start_datetime = new_task_data.start_datetime.replace(tzinfo=KYIV)
        new_task_data.end_datetime = new_task_data.end_datetime.replace(tzinfo=KYIV)
        task_id = None
        creator_level = await self.get_user_hierarchy_level()

        async with self.uow:
            if new_task_data.creator_id != self.user_id:
                return "Creator ID does not match the current user."
            executor_level = await self.get_user_hierarchy_level(
                new_task_data.executor_id
            )
            if executor_level < creator_level:
                return "You do not have permission to create a task for this user."
            task_data_dict = new_task_data.model_dump(exclude={"task_control_points"})
            try:
                task_id = await self.uow.tasks.add_one(task_data_dict)
            except Exception as e:
                logger.error(f"Error creating task: {e}")
                await self.uow.rollback()
                return f"Error creating task: {e}"
            if new_task_data.task_control_points:
                for control_point in new_task_data.task_control_points:
                    # TODO: додати нотифікації по контрольним точкам
                    control_point_data = control_point.model_dump()
                    control_point_data["task_id"] = task_id
                    try:
                        await self.uow.task_control_points.add_one(control_point_data)
                    except Exception as e:
                        logger.error(f"Error creating control point: {e}")
                        await self.uow.rollback()
                        return f"Error creating control point: {e}"
            await self.uow.commit()
        await self.create_notification_task_ending_soon(
            task_id=task_id,
            user_id=new_task_data.executor_id,
            _defer_until=new_task_data.end_datetime - datetime.timedelta(minutes=30),
        )
        await self.create_notification_task_is_overdue(
            task_id=task_id,
            executor_id=new_task_data.executor_id,
            creator_id=new_task_data.creator_id,
            _defer_until=new_task_data.end_datetime,
        )
        await self.create_notification_task_started(
            task_id=task_id,
            user_id=new_task_data.executor_id,
            _defer_until=new_task_data.start_datetime,
        )
        await self.create_notification_new_task(
            task_id=task_id,
            user_id=new_task_data.creator_id,
        )
        return task_id

    async def create_many_task_func(
        self,
        new_task_data: list[TaskCreate],
    ):
        created_task_ids = []
        for new_task in new_task_data:
            task_id = await self.create_one_task_func(new_task)
            if isinstance(task_id, str):
                return task_id
            created_task_ids.append(task_id)
        return created_task_ids

    async def update_tasks_func(
        self,
        updates_list: list[TaskUpdate],
    ):
        async with self.uow:
            for task_data in updates_list:
                task_model = await self.uow.tasks.find_one(
                    id=task_data.id,
                )
                if not task_model:
                    await self.uow.rollback()
                    return f"Task with ID {task_data.id} not found."
                if (
                    task_model.creator_id != self.user_id
                    and await self.get_user_hierarchy_level() > 3
                ):
                    await self.uow.rollback()
                    return "You do not have permission to update this task."
                if task_data.start_datetime:
                    task_data.start_datetime = task_data.start_datetime.replace(
                        tzinfo=KYIV
                    )
                if task_data.end_datetime:
                    task_data.end_datetime = task_data.end_datetime.replace(tzinfo=KYIV)
                task_dict = task_data.model_dump(
                    exclude_unset=True, exclude_none=True, exclude={"id"}
                )
                try:
                    await self.uow.tasks.edit_one(id=task_data.id, data=task_dict)
                except Exception as e:
                    logger.error(f"Error updating task: {e}")
                    await self.uow.rollback()
                    return f"Error updating task: {e}"

            await self.uow.commit()
            for task_data in updates_list:
                await self.create_notification_task_updated(
                    task_id=task_data.id,
                    user_id=task_data.executor_id,
                )
                await self.create_notification_task_ending_soon(
                    task_id=task_data.id,
                    user_id=task_data.executor_id,
                    _defer_until=task_data.end_datetime
                    - datetime.timedelta(minutes=30),
                    update_notification=True,
                )
                await self.create_notification_task_is_overdue(
                    task_id=task_data.id,
                    executor_id=task_data.executor_id,
                    creator_id=task_data.creator_id,
                    _defer_until=task_data.end_datetime,
                    update_notification=True,
                )
                await self.create_notification_task_started(
                    task_id=task_data.id,
                    user_id=task_data.executor_id,
                    _defer_until=task_data.start_datetime,
                    update_notification=True,
                )
            return True

    async def delete_task_func(self, task_id: int) -> str | bool:
        async with self.uow:
            try:
                task_model: Task | None = await self.uow.tasks.find_one(id=task_id)
                if not task_model:
                    return f"Task with ID {task_id} not found."
                if (
                    task_model.creator_id != self.user_id
                    and await self.get_user_hierarchy_level() > 3
                ):
                    return "You do not have permission to delete this task."
                await self.uow.tasks.delete_one(id=task_id)
            except Exception as e:
                logger.error(f"Error deleting task: {e}")
                await self.uow.rollback()
                return f"Error deleting task: {e}"
            await self.uow.commit()
            return True

    @redis_cache(15)
    async def get_tasks_func(
        self,
        creator_id: int | None = None,
        executor_id: int | None = None,
        category_id: int | None = None,
        status: TaskStatus | None = None,
        start_datetime: datetime.datetime | None = None,
        end_datetime: datetime.datetime | None = None,
    ):
        async with self.uow:
            hierarchy_level = await self.get_user_hierarchy_level()
            if hierarchy_level > 3 and self.user_id not in [
                creator_id,
                executor_id,
            ]:
                return []
            tasks = await self.uow.tasks.get_all_tasks(
                creator_id=creator_id,
                executor_id=executor_id,
                category_id=category_id,
                status=status,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )
            return [
                TaskReadExtended.model_validate(task, from_attributes=True).model_dump(
                    exclude={
                        "creator": {
                            "position": {
                                "hierarchy_level": {
                                    "create_task_prompt",
                                    "manage_task_prompt",
                                    "work_schedule_prompt",
                                    "category_prompt",
                                    "analytics_prompt",
                                }
                            }
                        },
                        "executor": {
                            "position": {
                                "hierarchy_level": {
                                    "create_task_prompt",
                                    "manage_task_prompt",
                                    "work_schedule_prompt",
                                    "category_prompt",
                                    "analytics_prompt",
                                }
                            }
                        },
                    },
                )
                for task in tasks
            ]

    async def get_task_by_id_func(self, task_id: int):
        async with self.uow:
            task = await self.uow.tasks.get_task_by_id(
                task_id=task_id,
            )
            if (
                self.user_id not in [task["creator_id"], task["executor_id"]]
                and await self.get_user_hierarchy_level() > 3
            ):
                return None
            return TaskReadExtended.model_validate(
                task, from_attributes=True
            ).model_dump(
                exclude={
                    "creator": {
                        "position": {
                            "hierarchy_level": {
                                "create_task_prompt",
                                "manage_task_prompt",
                                "work_schedule_prompt",
                                "category_prompt",
                                "analytics_prompt",
                            }
                        }
                    },
                    "executor": {
                        "position": {
                            "hierarchy_level": {
                                "create_task_prompt",
                                "manage_task_prompt",
                                "work_schedule_prompt",
                                "category_prompt",
                                "analytics_prompt",
                            }
                        }
                    },
                },
            )

    def get_tools(
        self,
    ) -> list:
        @tool
        async def create_one_task(new_task_data: TaskCreate):
            """
            Создает новою задачу для пользователя.

            :param new_task_data: TaskCreate instance containing task details.

            :return: The ID of the created task.
            """
            return await self.create_one_task_func(new_task_data)

        @tool
        async def create_many_task(
            new_task_data: list[TaskCreate],
        ):
            """
            Создает новою задачу для пользователя.
            :param new_task_data: TaskCreate instance containing task details.


            :return: list of created task IDs.
            """
            return await self.create_many_task_func(new_task_data)

        @tool
        async def update_tasks(updates_list: list[TaskUpdate]) -> bool:
            """
            Оновити завдання за його ID.

            :param updates_list: TaskUpdate instances containing the task ID and new data.

            Returns:
                bool: True, якщо завдання були успішно оновлені, False в іншому випадку.
            """
            return await self.update_tasks_func(updates_list)

        @tool
        async def delete_task(task_id: int) -> str | bool:
            """
            Видалити завдання за його ID.

            :param task_id: ID завдання, яке потрібно видалити.

            Returns:
                bool: True, якщо завдання було успішно видалено, False в іншому випадку.
            """
            return await self.delete_task_func(task_id)

        @tool
        async def delete_many_tasks(task_ids: list[int]) -> str | bool:
            """
            Видалити кілька завдань за їх ID.

            :param task_ids: Список ID завдань, які потрібно видалити.

            Returns:
                bool: True, якщо завдання були успішно видалені, False в іншому випадку.
            """
            async with self.uow:
                for task_id in task_ids:
                    result = await self.delete_task_func(task_id)
                    if isinstance(result, str):
                        return result
                return True

        @tool
        async def get_tasks(
            creator_id: int | None = None,
            executor_id: int | None = None,
            category_id: int | None = None,
            status: TaskStatus | None = None,
            start_datetime: datetime.datetime | None = None,
            end_datetime: datetime.datetime | None = None,
        ):
            """
            Отримати завдання з бази даних за різними критеріями.

            :param creator_id: ID користувача, який створив завдання (необов'язково).
            :param executor_id: ID користувача, який виконує завдання (необов'язково).
            :param category_id: ID категорії завдання (необов'язково).
            :param status: Статус завдання (необов'язково).
            :param start_datetime: Дата та час початку завдання (необов'язково).
            :param end_datetime: Дата та час завершення завдання (необов'язково).

            Returns:
                list[TaskReadExtended]: Список завдань, що відповідають критеріям.
            """
            list_dict_tasks = await self.get_tasks_func(
                creator_id=creator_id,
                executor_id=executor_id,
                category_id=category_id,
                status=status,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )
            return [TaskReadExtended.model_validate(task) for task in list_dict_tasks]

        @tool
        async def get_task_by_id(task_id: int):
            """
            Отримати завдання за його ID.

            :param task_id: ID завдання, яке потрібно отримати.

            Returns:
                TaskReadExtended: Завдання з бази даних.
            """
            task_dict = await self.get_task_by_id_func(task_id)
            if not task_dict:
                return None
            return TaskReadExtended.model_validate(task_dict)

        all_tools = [
            create_one_task,
            create_many_task,
            update_tasks,
            delete_task,
            delete_many_tasks,
            get_tasks,
            get_task_by_id,
        ]

        return all_tools
