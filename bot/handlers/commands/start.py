"""Start command handler."""

from typing import Callable

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from core.logging import get_logger
from keyboards import HomeKeyboard
from locales import TranslationKey
from services import UserService

logger = get_logger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def start_handler(
    message: Message,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle /start command."""
    user = message.from_user
    if not user:
        return

    # Extract referral code from deep link
    referral_code = None
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].startswith("r_"):
            referral_code = parts[1][2:].strip() or None

    # Sync user with API (including profile data)
    try:
        result = await UserService.sync_user(
            user.id,
            referral_code=referral_code,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
        )

        # Notify referrer if new referral applied
        if result.get("referral_applied") and result.get("referrer_telegram_id"):
            bonus_percent = int(result.get("bonus_percent", 10))
            await message.bot.send_message(
                chat_id=int(result["referrer_telegram_id"]),
                text=_(TranslationKey.REFERRAL_NEW_APPLIED, {"percent": bonus_percent}),
            )
    except Exception as e:
        logger.warning("Failed to sync user on start", user_id=user.id, error=str(e))

    # Clear any reply keyboard
    clearing = await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await clearing.delete()

    # Send welcome message
    await message.answer(
        _(TranslationKey.WELCOME, {"name": user.first_name or ""}),
        reply_markup=HomeKeyboard.main(_),
    )
