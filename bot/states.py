from aiogram.fsm.state import State, StatesGroup


class GenerationState(StatesGroup):
    prompt = State()
    menu_message_id = State()
    size = State()
    reference_urls = State()
    model_id = State()
    price = State()
