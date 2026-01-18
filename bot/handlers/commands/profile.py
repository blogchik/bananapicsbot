"""Profile command handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, User
from typing import Callable

from keyboards import ProfileKeyboard
from locales import TranslationKey
from services import UserService, GenerationService
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="profile")


async def send_profile_message(
    message: Message,
    user: User,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Send profile information message."""
    try:
        profile = await UserService.get_profile(user.id)
    except Exception as e:
        logger.warning("Failed to get profile", user_id=user.id, error=str(e))
        await message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    approx_text = ""
    try:
        models = await GenerationService.get_models()
        prices = [model.price for model in models if model.price > 0]
        if prices:
            min_price = min(prices)
            approx_count = int(profile.balance // min_price)
            approx_text = _(TranslationKey.PROFILE_GENERATIONS_ESTIMATE, {"count": approx_count})
    except Exception:
        approx_text = ""

    telegram_id_text = _(TranslationKey.PROFILE_ID_LABEL, None) + f": <code>{user.id}</code>"
    balance_text = _(TranslationKey.PROFILE_BALANCE, {"balance": profile.balance})
    
    # Build message
    lines = [
        telegram_id_text,
        balance_text,
    ]
    if approx_text:
        lines.append(approx_text)
    text = "\n".join(lines)
    
    await message.answer(text, reply_markup=ProfileKeyboard.main(_))


@router.message(Command("profile"))
async def profile_handler(
    message: Message,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle /profile command."""
    user = message.from_user
    if not user:
        await message.answer(_(TranslationKey.USER_NOT_FOUND, None))
        return
    
    await send_profile_message(message, user, _)
