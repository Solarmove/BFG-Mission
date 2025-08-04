from aiogram.fsm.state import StatesGroup, State


class AIAgentMenu(StatesGroup):
    send_query = State()
