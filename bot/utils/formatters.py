"""Formatting utilities."""

from datetime import datetime
from typing import Union


def format_number(value: Union[int, float], decimals: int = 0) -> str:
    """Format number with thousand separators."""
    if decimals > 0:
        formatted = f"{value:,.{decimals}f}"
    else:
        formatted = f"{int(value):,}"
    return formatted.replace(",", " ")


def format_date(
    value: Union[str, datetime, None],
    include_time: bool = False,
) -> str:
    """Format date/datetime to string."""
    if value is None:
        return "-"
    
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    
    if include_time:
        return value.strftime("%d.%m.%Y %H:%M")
    return value.strftime("%d.%m.%Y")


def format_credits(amount: Union[int, float]) -> str:
    """Format credits amount."""
    return format_number(amount)


def format_balance(balance: int, trial: int = 0) -> str:
    """Format balance with trial if available."""
    if trial > 0:
        return f"{format_number(balance)} (+{format_number(trial)} trial)"
    return format_number(balance)


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage."""
    return f"{value:.{decimals}f}%"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
