"""Settings command handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from typing import Callable

from keyboards import SettingsKeyboard
from locales import TranslationKey
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="settings")


@router.message(Command("settings"))
async def settings_handler(
    message: Message,
    language: str,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle /settings command."""
    await message.answer(
        _(TranslationKey.SETTINGS_TITLE, None),
        reply_markup=SettingsKeyboard.main(language, _),
    )
