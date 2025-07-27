from langchain_core.tools import tool

from bot.db.redis import redis_cache
from bot.entities.task import TaskCategoryRead
from .base import BaseTools


class CategoryTools(BaseTools):
    """Інструменти для роботи з категоріями завдань."""

    @redis_cache(60)
    async def get_categories_dict(self):
        """
        Отримати словник всіх категорій завдань з бази даних.

        Returns:
            list[dict]: Список словників, де кожен словник містить інформацію про категорію завдання.

        """
        async with self.uow:
            categories = await self.uow.task_categories.find_all()
            return [
                TaskCategoryRead.model_validate(
                    category, from_attributes=True
                ).model_dump()
                for category in categories
            ]

    def get_tools(self) -> list:
        @tool
        async def get_categories_from_db() -> list[TaskCategoryRead]:
            """
            Отримати всі категорії завдань з бази даних.

            Returns:
                list[TaskCategoryRead]: List of all task categories.
            """

            categories = await self.get_categories_dict()
            return [
                TaskCategoryRead.model_validate(category) for category in categories
            ]

        @tool
        async def get_category_by_id(category_id: int) -> TaskCategoryRead | None:
            """
            Отримати категорію завдання за її ID.

            :param category_id: ID категорії завдання.

            Returns:
                TaskCategoryRead | None: Категорія завдання або None, якщо не знайдено.
            """
            async with self.uow:
                category = await self.uow.task_categories.find_one(id=category_id)
                if category:
                    return TaskCategoryRead(id=category.id, name=category.title)
                return None

        @tool
        async def create_category(category_name: str) -> TaskCategoryRead:
            """
            Створити нову категорію завдання.

            :param category_name: Назва категорії завдання.

            Returns:
                TaskCategoryRead: Створена категорія завдання.
            """
            async with self.uow:
                category_data = {"name": category_name}
                category_id = await self.uow.task_categories.add_one(category_data)
                await self.uow.commit()
                return TaskCategoryRead(id=category_id, name=category_name)

        @tool
        async def delete_category(category_id: int):
            """
            Видалити категорію завдання за її ID.

            :param category_id: ID категорії завдання, яку потрібно видалити.
            """
            async with self.uow:
                await self.uow.task_categories.delete_one(id=category_id)
                await self.uow.commit()

        return [
            get_categories_from_db,
            get_category_by_id,
            create_category,
            delete_category,
        ]
