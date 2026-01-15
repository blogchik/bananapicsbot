"""Payment FSM states."""

from aiogram.fsm.state import State, StatesGroup


class PaymentStates(StatesGroup):
    """Payment workflow states."""
    
    # Waiting for custom stars amount
    waiting_stars_amount = State()
    
    # Processing payment
    processing_payment = State()
