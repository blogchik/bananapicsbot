"""WebApp command handler."""

from typing import Callable

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from core.logging import get_logger
from locales import TranslationKey

logger = get_logger(__name__)
router = Router(name="webapp")


@router.message(Command("webapp"))
async def webapp_command(
    message: Message,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle /webapp command."""
    user = message.from_user
    if not user:
        return

    # Get webapp URL from environment or construct it
    # For now, we'll use a placeholder that should be replaced with actual webapp URL
    import os
    
    webapp_url = os.getenv("WEBAPP_URL", "https://your-webapp-url.com")

    # Create inline keyboard with WebApp button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.WEBAPP_BUTTON),
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ]
    )

    # Send message with webapp description and button
    await message.answer(
        _(TranslationKey.WEBAPP_DESCRIPTION),
        reply_markup=keyboard,
    )

    logger.info("WebApp command sent", user_id=user.id)
