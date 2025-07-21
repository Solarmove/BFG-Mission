from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from bot.utils.unitofwork import IUnitOfWork

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, uow: IUnitOfWork):
    ...
