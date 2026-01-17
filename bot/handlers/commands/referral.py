"""Referral command handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from typing import Callable

from keyboards import ReferralKeyboard
from locales import TranslationKey
from services import UserService
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="referral")


@router.message(Command("referral"))
async def referral_handler(
    message: Message,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle /referral command."""
    user = message.from_user
    if not user:
        return

    try:
        await UserService.sync_user(user.id)
        info = await UserService.get_referral_info(user.id)
    except Exception as e:
        logger.warning("Failed to get referral info", user_id=user.id, error=str(e))
        await message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return

    try:
        me = await message.bot.get_me()
        bot_username = me.username or ""
    except Exception:
        bot_username = ""

    code = str(info.get("referral_code", ""))
    link = f"https://t.me/{bot_username}?start=r_{code}" if bot_username and code else "-"

    bonus_percent = int(info.get("bonus_percent", 10))
    referrals_count = int(info.get("referrals_count", 0))
    bonus_total = int(info.get("referral_credits_total", 0))

    text = (
        f"{_(TranslationKey.REFERRAL_TITLE, None)}\n"
        f"{_(TranslationKey.REFERRAL_DESCRIPTION, {'percent': bonus_percent})}\n\n"
        f"{_(TranslationKey.REFERRAL_LINK, {'link': link})}\n\n"
        f"{_(TranslationKey.REFERRAL_COUNT, {'count': referrals_count})}\n"
        f"{_(TranslationKey.REFERRAL_BONUS_TOTAL, {'total': bonus_total})}"
    )

    await message.answer(text, reply_markup=ReferralKeyboard.main(_))
