"""Generation FSM states."""

from aiogram.fsm.state import State, StatesGroup


class GenerationStates(StatesGroup):
    """Generation workflow states."""

    # Prompt input
    waiting_prompt = State()

    # Configuration menu
    configuring = State()

    # Model selection
    selecting_model = State()

    # Size selection
    selecting_size = State()

    # Aspect ratio selection
    selecting_ratio = State()

    # Resolution selection
    selecting_resolution = State()

    # Processing
    processing = State()
