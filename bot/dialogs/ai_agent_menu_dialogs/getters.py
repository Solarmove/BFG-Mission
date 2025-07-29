from aiogram_dialog import DialogManager  # noqa: F401
from aiogram.types import User  # noqa: F401

from bot.utils.unitofwork import UnitOfWork


async def ai_agent_getter(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    event_from_user: User,
    **kwargs: dict,
):
    """
    Getter function for AI Agent dialog.
    Retrieves the hierarchy level and current task from the user's state.
    """
    hierarchy_level = await uow.users.get_user_hierarchy_level(event_from_user.id)
    my_full_name = await uow.users.get_user_full_name(event_from_user.id)
    dialog_manager.dialog_data["hierarchy_level"] = hierarchy_level
    return {
        "hierarchy_level": hierarchy_level,
        "full_name": my_full_name or event_from_user.full_name,
        'prompt': dialog_manager.start_data.get('prompt')
    }


async def ai_agent_answer_getter(
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    event_from_user: User,
    **kwargs: dict,
):
    """
    Getter function for AI Agent answer dialog.
    Retrieves the answer from the user's state.
    """
    answer = dialog_manager.dialog_data["answer"]
    return {"answer": answer, "answer_len": len(answer)}
