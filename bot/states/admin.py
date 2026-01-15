"""Admin FSM states."""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """Admin workflow states."""
    
    # User search flow
    waiting_user_search = State()
    
    # Add credits flow
    waiting_credits_user_id = State()
    waiting_credits_amount = State()
    waiting_credits_reason = State()
    waiting_credits_description = State()
    
    # Broadcast flow
    waiting_broadcast_message = State()
    waiting_broadcast_confirm = State()
    confirming_broadcast = State()
    
    # Refund flow
    waiting_refund_user_id = State()
    waiting_refund_amount = State()
