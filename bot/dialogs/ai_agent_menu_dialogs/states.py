from aiogram.fsm.state import StatesGroup, State  # noqa: F401


class AIAgentMenu(StatesGroup):
    send_query = State()
    answer = State()
