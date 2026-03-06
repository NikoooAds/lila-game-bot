from aiogram.fsm.state import StatesGroup, State


class Prompt(StatesGroup):
    text = State()
