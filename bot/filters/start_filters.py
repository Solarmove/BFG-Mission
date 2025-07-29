from aiogram.filters import Filter
from aiogram.types import Message

from bot.utils.unitofwork import UnitOfWork
from configreader import config


class IsAdmin(Filter):
    async def __call__(self, message) -> bool:
        user = message.from_user
        # Assuming you have a method to check if the user is an admin
        return user.id in config.admins


class UserExists(Filter):
    async def __call__(self, message: Message, uow: UnitOfWork) -> bool:
        user = message.from_user
        return await uow.users.user_exist(user.id)
