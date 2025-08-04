import datetime
import logging

from langchain_core.tools import tool

from bot.entities.other import ScheduleCreationResult
from bot.entities.users import WorkScheduleCreate, WorkScheduleRead, WorkScheduleUpdate
from .base import BaseTools

logger = logging.getLogger(__name__)


class WorkScheduleTools(BaseTools):
    """Інструменти для роботи з робочими графіками."""

    def get_tools(
        self,
    ) -> list:
        @tool
        async def get_all_work_schedulers_from_db(
            date_from: datetime.datetime | None = None,
            date_to: datetime.datetime | None = None,
        ) -> str | list[WorkScheduleRead]:
            """
            Отримати всі робочі графіки з бази даних.
            Якщо список порожній - графіків немає.

            :param date_from: Дата початку періоду для фільтрації робочих графіків (необов'язково). За замовчування цей місяць
            :param date_to: Дата закінчення періоду для фільтрації робочих графіків (необов'язково). За замовчування цей місяць

            Returns:
                list: List of all work schedules.
            """
            user_level = await self.get_user_hierarchy_level(self.user_id)
            if user_level > 3:
                logger.warning(
                    "User with ID %s has insufficient permissions to access work schedules.",
                    self.user_id,
                )
                return "You do not have permission to access work schedules."
            if not date_from:
                date_from = datetime.datetime.now().replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            if not date_to:
                date_to = datetime.datetime.now().replace(
                    day=1, hour=23, minute=59, second=59, microsecond=999999
                ) + datetime.timedelta(days=31)

            async with self.uow:
                work_schedules = await self.uow.work_schedules.get_all_work_schedules_for_date_to_date(
                    date_from=date_from.date(),
                    date_to=date_to.date(),
                )
                work_schedules_list = [
                    WorkScheduleRead(
                        id=ws.id,
                        user_id=ws.user_id,
                        start_time=ws.start_time,
                        end_time=ws.end_time,
                        date=ws.date,
                    )
                    for ws in work_schedules
                ]
                return work_schedules_list

        @tool
        async def get_work_schedule_in_user(
            user_id: int,
        ) -> list[WorkScheduleRead] | str:
            """
            Отримати робочий графік користувача за його ID.

            :param user_id: ID користувача, для якого потрібно отримати робочий графік.

            Returns:
                WorkScheduleRead: Робочий графік користувача.
            """
            if (
                user_id != self.user_id
                and await self.get_user_hierarchy_level(user_id=user_id) > 3
            ):
                logger.warning(
                    "User with ID %s has insufficient permissions to access their own work schedule.",
                    user_id,
                )
                return "You do not have permission to access your own work schedule."
            async with self.uow:
                work_schedule = await self.uow.work_schedules.find_all(user_id=user_id)
                return [
                    WorkScheduleRead(
                        id=ws.id,
                        user_id=ws.user_id,
                        start_time=ws.start_time,
                        end_time=ws.end_time,
                        date=ws.date,
                    )
                    for ws in work_schedule
                ]

        @tool
        async def update_work_schedule(work_schedule_id: int, data: WorkScheduleUpdate):
            """
            Оновити робочий графік користувача за його ID.

            :param work_schedule_id: ID робочого графіку, який потрібно оновити.
            :param data: WorkScheduleUpdate instance containing the new data for the work schedule.
            """

            async with self.uow:
                if await self.get_user_hierarchy_level(user_id=self.user_id) > 3:
                    logger.warning(
                        "User with ID %s has insufficient permissions to update their own work schedule.",
                        self.user_id,
                    )
                    return (
                        "You do not have permission to update your own work schedule."
                    )
                work_schedule_dict = data.model_dump(
                    exclude_unset=True, exclude_none=True
                )
                try:
                    await self.uow.work_schedules.edit_one(
                        id=work_schedule_id, data=work_schedule_dict
                    )
                except Exception as e:
                    logger.error("Error updating work schedule: %s", e)
                    return f"Error updating work schedule: {e}"
                await self.uow.commit()
                return None

        @tool
        async def delete_work_schedule(work_schedule_id: int):
            """
            Видалити робочий графік користувача за його ID.

            :param work_schedule_id: ID робочого графіку, який потрібно видалити.
            """
            async with self.uow:
                if await self.get_user_hierarchy_level(user_id=self.user_id) > 3:
                    logger.warning(
                        "User with ID %s has insufficient permissions to delete their own work schedule.",
                        self.user_id,
                    )
                    return (
                        "You do not have permission to delete your own work schedule."
                    )
                try:
                    await self.uow.work_schedules.delete_one(id=work_schedule_id)
                except Exception as e:
                    logger.error("Error deleting work schedule: %s", e)
                    return f"Error deleting work schedule: {e}"
                await self.uow.commit()
                return None

        @tool
        async def create_work_schedule(
            work_schedule_data_list: list[WorkScheduleCreate],
        ) -> str | ScheduleCreationResult:
            """
            Створити новий робочий графік користувача.

            :param work_schedule_data_list: WorkScheduleCreate instance containing the data for the new work schedule.

            Returns:
                ScheduleCreationResult: Result of the schedule creation operation, including counts of created and existing schedules.

            """
            schedules_exists = 0
            schedules_created = 0
            if await self.get_user_hierarchy_level(user_id=self.user_id) > 3:
                logger.warning(
                    "User with ID %s has insufficient permissions to create work schedules.",
                    self.user_id,
                )
                return "You do not have permission to create work schedules."
            async with self.uow:
                for work_schedule_data in work_schedule_data_list:
                    work_schedule_exists = await self.uow.work_schedules.find_one(
                        user_id=work_schedule_data.user_id,
                        date=work_schedule_data.date,
                    )
                    if not work_schedule_exists:
                        work_schedule_dict = work_schedule_data.model_dump()
                        try:
                            await self.uow.work_schedules.add_one(work_schedule_dict)
                        except Exception as e:
                            logger.error("Error creating work schedule: %s", e)
                            return f"Error creating work schedule: {e}"
                        await self.uow.commit()
                        schedules_created += 1
                    else:
                        try:
                            await self.uow.work_schedules.edit_one(
                                id=work_schedule_exists.id,
                                data=work_schedule_data.model_dump(
                                    exclude_unset=True, exclude_none=True
                                ),
                            )
                        except Exception as e:
                            logger.error("Error updating existing work schedule: %s", e)
                            return f"Error updating existing work schedule: {e}"
                return ScheduleCreationResult(
                    created_count=schedules_created,
                    existing_count=schedules_exists,
                )

        return [
            get_all_work_schedulers_from_db,
            get_work_schedule_in_user,
            update_work_schedule,
            delete_work_schedule,
            create_work_schedule,
        ]
