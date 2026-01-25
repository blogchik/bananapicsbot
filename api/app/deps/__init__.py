"""FastAPI dependencies."""

from app.deps.telegram_auth import (
    OptionalTelegramUserDep,
    TelegramInitData,
    TelegramUser,
    TelegramUserDep,
    get_optional_telegram_user,
    get_telegram_user,
    validate_init_data,
)

__all__ = [
    "TelegramUser",
    "TelegramInitData",
    "TelegramUserDep",
    "OptionalTelegramUserDep",
    "get_telegram_user",
    "get_optional_telegram_user",
    "validate_init_data",
]
