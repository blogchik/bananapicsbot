"""Validation utilities."""

import re
from typing import Optional

from core.constants import BotConstants


def validate_prompt(prompt: str) -> tuple[bool, Optional[str]]:
    """
    Validate generation prompt.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"

    prompt = prompt.strip()

    if len(prompt) < BotConstants.MIN_PROMPT_LENGTH:
        return False, f"Prompt must be at least {BotConstants.MIN_PROMPT_LENGTH} characters"

    if len(prompt) > BotConstants.MAX_PROMPT_LENGTH:
        return False, f"Prompt must be at most {BotConstants.MAX_PROMPT_LENGTH} characters"

    return True, None


def validate_amount(text: str, min_value: int = 1, max_value: int = 1_000_000) -> tuple[bool, Optional[int], Optional[str]]:
    """
    Validate numeric amount input.
    
    Returns:
        Tuple of (is_valid, parsed_value, error_message)
    """
    text = text.strip()

    # Remove common number formatting
    text = re.sub(r"[\s,]", "", text)

    try:
        value = int(text)
    except ValueError:
        return False, None, "Invalid number format"

    if value < min_value:
        return False, None, f"Value must be at least {min_value}"

    if value > max_value:
        return False, None, f"Value must be at most {max_value}"

    return True, value, None


def validate_telegram_id(text: str) -> tuple[bool, Optional[int], Optional[str]]:
    """
    Validate Telegram user ID.
    
    Returns:
        Tuple of (is_valid, parsed_id, error_message)
    """
    text = text.strip()

    try:
        user_id = int(text)
    except ValueError:
        return False, None, "Invalid user ID format"

    if user_id <= 0:
        return False, None, "User ID must be positive"

    return True, user_id, None


def validate_username(text: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Validate Telegram username.
    
    Returns:
        Tuple of (is_valid, normalized_username, error_message)
    """
    text = text.strip()

    # Remove @ prefix if present
    if text.startswith("@"):
        text = text[1:]

    if not text:
        return False, None, "Username cannot be empty"

    # Username rules: 5-32 characters, alphanumeric and underscore
    if len(text) < 5 or len(text) > 32:
        return False, None, "Username must be 5-32 characters"

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", text):
        return False, None, "Username must start with letter and contain only letters, numbers, underscores"

    return True, text.lower(), None
