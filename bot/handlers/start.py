from aiogram import Router, flags
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_i18n import I18nContext

from bot.dialogs.main_menu_dialogs.states import Registration, MainMenu
from bot.filters.start_filters import IsAdmin, UserExists
from bot.middleware.throttling import ThrottlingMiddleware
from bot.utils.unitofwork import UnitOfWork

router = Router()
router.message.middleware(ThrottlingMiddleware(start=2.5))


@router.message(CommandStart(ignore_case=True), IsAdmin())
@flags.throttling_key("start")
async def admin_start_handler(
    message: Message, uow: UnitOfWork, dialog_manager: DialogManager, state: FSMContext
):
    """
    Handler for the /start command.
    Initializes the user in the database and starts the dialog.
    """
    await state.clear()
    owner_position = await uow.positions.find_one(title="Власник")
    if not owner_position:
        await message.answer("Позиції не налаштовані. Зверніться до адміністратора.")
        return
    user = await uow.users.get_or_create(
        id=message.from_user.id,
        username=message.from_user.username,
        full_name_tg=message.from_user.full_name,
        position_id=owner_position.id if owner_position else None,
    )
    if user:
        await dialog_manager.start(MainMenu.select_action, mode=StartMode.RESET_STACK)
        return
    await uow.commit()
    await dialog_manager.start(
        Registration.enter_full_name,
        data={"position_id": owner_position.id},
        mode=StartMode.RESET_STACK,
    )


@router.message(CommandStart(deep_link=True, deep_link_encoded=True, ignore_case=True))
@flags.throttling_key("start")
async def other_start_handler(
    message: Message,
    command: CommandObject,
    uow: UnitOfWork,
    dialog_manager: DialogManager,
    i18n: I18nContext,
    state: FSMContext,
):
    """
    Handler for the /start command.
    Initializes the user in the database and starts the dialog.
    """
    await state.clear()
    user_exist = await uow.users.user_exist(message.from_user.id, update_cache=True)
    if user_exist:
        return await message.answer(i18n.get("already-registered-text"))
    args = command.args
    if not args.startswith("position="):
        return await message.answer(i18n.get("registration-error-text"))
    position_id = int(args.split("=")[1])
    return await dialog_manager.start(
        Registration.enter_full_name,
        data={"position_id": position_id},
        mode=StartMode.RESET_STACK,
    )


@router.message(CommandStart(ignore_case=True), UserExists())
@flags.throttling_key("start")
async def user_start_handler(
    message: Message, uow: UnitOfWork, dialog_manager: DialogManager, state: FSMContext
):
    """
    Handler for the /start command.
    Initializes the user in the database and starts the dialog.
    """

    await state.clear()
    await dialog_manager.start(MainMenu.select_action, mode=StartMode.RESET_STACK)
