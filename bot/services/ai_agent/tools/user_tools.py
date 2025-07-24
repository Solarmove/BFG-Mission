from langchain_core.tools import tool
from bot.entities.shared import UserReadExtended
from bot.entities.task import TaskRead
from bot.entities.users import UserRead, WorkScheduleRead
from .base import BaseTools


class UserTools(BaseTools):
    """Інструменти для роботи з користувачами."""
    
    def get_tools(self) -> list:
        @tool
        async def get_all_users_from_db() -> list[UserRead]:
            """
            Отримати всіх користувачів з бази даних.

            Returns:
                list: List of all users.
            """

            async with self.uow:
                users = await self.uow.users.find_all()
                users_list = [
                    UserRead(
                        id=user.id,
                        username=user.username,
                        full_name_tg=user.full_name_tg,
                        full_name=user.full_name,
                        hierarchy_level=user.hierarchy_level,
                        position_title=user.position_title,
                        created_at=user.created_at,
                        updated_at=user.updated_at,
                    )
                    for user in users
                ]
                return users_list

        @tool
        async def get_user_by_id(
            user_id: int, extended: bool = False
        ) -> UserRead | UserReadExtended | None:
            """
            Отримати користувача за його ID.

            :param user_id: ID користувача, якого потрібно отримати.
            :param extended: Якщо True, повертає розширену інформацію про користувача, включаючи робочі графіки та завдання.

            Returns:
                UserRead | UserReadExtended | None: Користувач або None, якщо користувач не знайдений.

            """
            async with self.uow:
                if extended:
                    user = await self.uow.users.get_user_with_all_data(user_id=user_id)
                    if not user:
                        return None
                    return UserReadExtended(
                        id=user.id,
                        username=user.username,
                        full_name_tg=user.full_name_tg,
                        full_name=user.full_name,
                        hierarchy_level=user.hierarchy_level,
                        position_title=user.position_title,
                        created_at=user.created_at,
                        updated_at=user.updated_at,
                        work_schedules=[
                            WorkScheduleRead(
                                id=ws.id,
                                user_id=ws.user_id,
                                start_time=ws.start_time,
                                end_time=ws.end_time,
                                date=ws.date,
                            )
                            for ws in user.work_schedules
                        ],
                        created_tasks=[
                            TaskRead(
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
                            )
                            for task in user.created_tasks
                        ],
                        executed_tasks=[
                            TaskRead(
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
                            )
                            for task in user.executed_tasks
                        ],
                    )
                else:
                    user = await self.uow.users.find_one(id=user_id)
                    if not user:
                        return None
                    return UserRead(
                        id=user.id,
                        username=user.username,
                        full_name_tg=user.full_name_tg,
                        full_name=user.full_name,
                        hierarchy_level=user.hierarchy_level,
                        position_title=user.position_title,
                        created_at=user.created_at,
                        updated_at=user.updated_at,
                    )

        return [
            get_all_users_from_db,
            get_user_by_id,
        ]