"""Profile command handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, User
from typing import Callable

from keyboards import ProfileKeyboard
from locales import TranslationKey
from services import UserService
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
    
    # Format user info
    name = UserService.format_user_name(
        user.first_name or "",
        user.last_name,
        user.username,
        user.id,
    )
    username = f"@{user.username}" if user.username else "-"
    
    # Format trial status
    if profile.trial_available:
        trial_status = _(TranslationKey.PROFILE_TRIAL_AVAILABLE, None)
    else:
        trial_status = _(TranslationKey.PROFILE_TRIAL_UNAVAILABLE, None)
    
    trial_text = _(TranslationKey.PROFILE_TRIAL, {"status": trial_status})
    
    # Build message
    text = (
        f"{_(TranslationKey.PROFILE_TITLE, None)}\n"
        f"{_(TranslationKey.PROFILE_INFO, None)}\n"
        f"{_(TranslationKey.PROFILE_NAME, {'name': name})}\n"
        f"{_(TranslationKey.PROFILE_USERNAME, {'username': username})}\n"
        f"{_(TranslationKey.PROFILE_TELEGRAM_ID, {'telegram_id': user.id})}\n\n"
        f"{_(TranslationKey.PROFILE_BALANCE, {'balance': profile.balance})}\n"
        f"{trial_text}"
    )
    
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
