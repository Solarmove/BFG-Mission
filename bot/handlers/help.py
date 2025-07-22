from aiogram import Router, flags
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_i18n import I18nContext

from bot.filters.start_filters import UserExists
from bot.middleware.throttling import ThrottlingMiddleware
from bot.utils.unitofwork import UnitOfWork

router = Router()
router.message.middleware(ThrottlingMiddleware(help=2.5))


@router.message(CommandStart(), UserExists())
@flags.throttling_key("help")
async def help_handler(
    message: Message, uow: UnitOfWork, dialog_manager: DialogManager, i18n: I18nContext
):
    hierarchy_level = await uow.users.get_user_hierarchy_level(message.from_user.id)
    if hierarchy_level is None:
        return await message.answer("You are not registered in the system.")
    text_map = {
        1: "help-text-1",
        2: "help-text-2",
        3: "help-text-3",
        4: "help-text-4",
        5: "help-text-5",
    }
    return await message.answer(
        i18n.get(text_map.get(hierarchy_level)),
        disable_web_page_preview=True,
    )