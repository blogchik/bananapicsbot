"""Helper utilities."""

import html
import secrets
import string
from typing import Optional


def truncate_text(
    text: str,
    max_length: int = 100,
    suffix: str = "...",
) -> str:
    """Truncate text to max length with suffix."""
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text)


def generate_id(length: int = 16) -> str:
    """Generate random alphanumeric ID."""
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_short_id(length: int = 8) -> str:
    """Generate short random ID."""
    return generate_id(length)


def safe_int(value: Optional[str], default: int = 0) -> int:
    """Safely convert string to int with default."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Optional[str], default: float = 0.0) -> float:
    """Safely convert string to float with default."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def chunk_list(lst: list, chunk_size: int) -> list:
    """Split list into chunks of given size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def first_or_none(lst: list) -> Optional[any]:
    """Get first element of list or None if empty."""
    return lst[0] if lst else None


def get_username_link(username: Optional[str]) -> str:
    """Get Telegram username link."""
    if not username:
        return "-"
    return f"@{username}"


def get_user_link(user_id: int, name: str) -> str:
    """Get HTML link to user profile."""
    safe_name = escape_html(name)
    return f'<a href="tg://user?id={user_id}">{safe_name}</a>'


def pluralize(count: int, one: str, few: str, many: str) -> str:
    """
    Russian/Uzbek pluralization.

    Example: pluralize(5, "кредит", "кредита", "кредитов")
    """
    if count % 10 == 1 and count % 100 != 11:
        return one
    if 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return few
    return many
