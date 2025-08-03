import datetime

from langchain_core.tools import tool

from bot.entities.shared import TaskReadExtended
from bot.entities.task import TaskUpdate
from bot.services.ai_agent.tools import TaskTools
from bot.utils.enum import TaskStatus


class ManageTaskTools(TaskTools):
    def get_tools(self):
        @tool
        async def update_tasks(updates_list: list[TaskUpdate]) -> bool:
            """
            Оновити завдання за його ID.

            :param updates_list: TaskUpdate instances containing the task ID and new data.

            Returns:
                bool: True, якщо завдання були успішно оновлені, False в іншому випадку.
            """
            return await self.update_tasks_func(updates_list)

        @tool(description="Видалити завдання за його ID")
        async def delete_task(task_id: int) -> str | bool:
            """
            Видалити завдання за його ID.

            :param task_id: ID завдання, яке потрібно видалити.

            Returns:
                bool: True, якщо завдання було успішно видалено, False в іншому випадку.
            """

            return await self.delete_task_func(task_id)

        @tool(description="Видалити кілька завдань за їх ID")
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

        @tool(description="Отримати список завдань за різними критеріями")
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

        @tool(description="Отримати завдання за його ID")
        async def get_task(
            task_id: int,
        ) -> TaskReadExtended | None:
            """
            Отримати завдання за його ID.

            :param task_id: ID завдання, яке потрібно отримати.

            Returns:
                TaskReadExtended | None: Завдання з розширеною інформацією або None, якщо не знайдено.
            """
            task = await self.get_task_by_id_func(task_id)
            if task:
                return TaskReadExtended.model_validate(task)
            return None

        return [update_tasks, delete_task, delete_many_tasks, get_tasks, get_task]