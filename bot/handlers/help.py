from aiogram import Router, flags
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager

from bot.middleware.throttling import ThrottlingMiddleware
from bot.utils.unitofwork import UnitOfWork

router = Router()
router.message.middleware(ThrottlingMiddleware(help=2.5))


@router.message(CommandStart())
@flags.throttling_key("help")
async def help_handler(
    message: Message, uow: UnitOfWork, dialog_manager: DialogManager
):
    ...
