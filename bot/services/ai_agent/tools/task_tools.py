import datetime
from langchain_core.tools import tool
from bot.entities.shared import TaskReadExtended
from bot.entities.task import (
    TaskCategoryRead,
    TaskControlPointRead,
    TaskCreate,
    TaskUpdate,
)
from bot.entities.users import UserRead
from bot.utils.enum import TaskStatus
from .base import BaseTools


class TaskTools(BaseTools):
    """Інструменти для роботи з завданнями."""

    def get_tools(self) -> list:
        @tool
        async def create_one_task(
            new_task_data: TaskCreate,
        ):
            """
            Создает новою задачу для пользователя.

            :param new_task_data: TaskCreate instance containing task details.

            :return: The created task object.
            """
            async with self.uow:
                task_data_dict = new_task_data.model_dump(
                    exclude={"task_control_points"}
                )
                task_id = await self.uow.tasks.add_one(task_data_dict)
                if new_task_data.task_control_points:
                    for control_point in new_task_data.task_control_points:
                        control_point_data = control_point.model_dump()
                        control_point_data["task_id"] = task_id
                        await self.uow.task_control_points.add_one(control_point_data)
                await self.uow.commit()

        @tool
        async def create_many_task(
            new_task_data: list[TaskCreate],
        ):
            """
            Создает новою задачу для пользователя.
            :param new_task_data: TaskCreate instance containing task details.


            :return: The created task object.
            """
            # uow: UnitOfWork = UnitOfWork()
            async with self.uow:
                for new_task in new_task_data:
                    task_data_dict = new_task.model_dump(
                        exclude={"task_control_points"}
                    )
                    task_id = await self.uow.tasks.add_one(task_data_dict)
                    if new_task.task_control_points:
                        for control_point in new_task.task_control_points:
                            control_point_data = control_point.model_dump()
                            control_point_data["task_id"] = task_id
                            await self.uow.task_control_points.add_one(
                                control_point_data
                            )
                await self.uow.commit()

        @tool
        async def update_tasks(updates_list: list[TaskUpdate]) -> bool:
            """
            Оновити завдання за його ID.

            :param updates_list: TaskUpdate instances containing the task ID and new data.

            Returns:
                bool: True, якщо завдання були успішно оновлені, False в іншому випадку.
            """
            async with self.uow:
                for task_data in updates_list:
                    task_dict = task_data.model_dump(
                        exclude_unset=True, exclude_none=True, exclude={"id"}
                    )
                    await self.uow.tasks.edit_one(id=task_data.id, data=task_dict)
                await self.uow.commit()
                return True

        @tool
        async def delete_task(task_id: int) -> bool:
            """
            Видалити завдання за його ID.

            :param task_id: ID завдання, яке потрібно видалити.

            Returns:
                bool: True, якщо завдання було успішно видалено, False в іншому випадку.
            """
            async with self.uow:
                await self.uow.tasks.delete_one(id=task_id)
                await self.uow.commit()
                return True

        @tool
        async def delete_many_tasks(task_ids: list[int]) -> bool:
            """
            Видалити кілька завдань за їх ID.

            :param task_ids: Список ID завдань, які потрібно видалити.

            Returns:
                bool: True, якщо завдання були успішно видалені, False в іншому випадку.
            """
            async with self.uow:
                for task_id in task_ids:
                    await self.uow.tasks.delete_one(id=task_id)
                await self.uow.commit()
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
            async with self.uow:
                tasks = await self.uow.tasks.get_all_tasks(
                    creator_id=creator_id,
                    executor_id=executor_id,
                    category_id=category_id,
                    status=status,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                )
                return [
                    TaskReadExtended(
                        id=task.id,
                        creator_id=task.creator_id,
                        executor_id=task.executor_id,
                        title=task.title,
                        description=task.description,
                        start_datetime=task.start_datetime,
                        end_datetime=task.end_datetime,
                        completed_datetime=task.completed_datetime,
                        category_id=task.category_id,
                        photo_required=task.photo_required,
                        video_required=task.video_required,
                        file_required=task.file_required,
                        status=task.status,
                        category=(
                            TaskCategoryRead(
                                id=task.category.id, name=task.category.title
                            )
                            if task.category
                            else None
                        ),
                        creator=(
                            UserRead(
                                id=task.creator.id,
                                username=task.creator.username,
                                full_name_tg=task.creator.full_name_tg,
                                full_name=task.creator.full_name,
                                hierarchy_level=task.creator.hierarchy_level,
                                position_title=task.creator.position_title,
                                created_at=task.creator.created_at,
                                updated_at=task.creator.updated_at,
                            )
                            if task.creator
                            else None
                        ),
                        executor=(
                            UserRead(
                                id=task.executor.id,
                                username=task.executor.username,
                                full_name_tg=task.executor.full_name_tg,
                                full_name=task.executor.full_name,
                                hierarchy_level=task.executor.hierarchy_level,
                                position_title=task.executor.position_title,
                                created_at=task.executor.created_at,
                                updated_at=task.executor.updated_at,
                            )
                            if task.executor
                            else None
                        ),
                        task_control_points=[
                            TaskControlPointRead(
                                id=cp.id,
                                task_id=cp.task_id,
                                description=cp.description,
                                datetime_complete=cp.datetime_complete,
                                deadline=cp.deadline,
                            )
                            for cp in task.control_points
                        ]
                        if task.control_points
                        else None,
                    )
                    for task in tasks
                ]

        return [
            create_one_task,
            create_many_task,
            update_tasks,
            delete_task,
            delete_many_tasks,
            get_tasks,
        ]
