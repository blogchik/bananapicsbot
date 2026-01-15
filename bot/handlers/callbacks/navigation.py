"""Navigation callback handlers."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from typing import Callable

from keyboards import HomeKeyboard, ProfileKeyboard
from keyboards.builders import MenuCallback
from locales import TranslationKey
from services import UserService
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="navigation")


@router.callback_query(F.data == MenuCallback.HOME)
async def home_callback(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle home menu callback."""
    await call.answer()
    
    if call.message:
        await call.message.delete()
    
    user = call.from_user
    name = user.first_name if user else ""
    await call.message.answer(
        _(TranslationKey.WELCOME, {"name": name}),
        reply_markup=HomeKeyboard.main(_),
    )


@router.callback_query(F.data == MenuCallback.INFO)
async def info_callback(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle info menu callback."""
    await call.answer()

    await call.message.answer(_(TranslationKey.START_INFO, None))


@router.callback_query(F.data == MenuCallback.PROFILE)
async def profile_callback(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle profile menu callback."""
    await call.answer()
    
    if call.message:
        await call.message.delete()
    
    user = call.from_user
    
    try:
        profile = await UserService.get_profile(user.id)
    except Exception as e:
        logger.warning("Failed to get profile", user_id=user.id, error=str(e))
        await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
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
    if profile.trial_used_count:
        trial_text += _(TranslationKey.PROFILE_TRIAL_USED, {"count": profile.trial_used_count})
    
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
    
    await call.message.answer(text, reply_markup=ProfileKeyboard.main(_))


@router.callback_query(F.data == MenuCallback.SETTINGS)
async def settings_callback(
    call: CallbackQuery,
    language: str,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle settings menu callback."""
    await call.answer()
    
    if call.message:
        await call.message.delete()
    
    from keyboards import SettingsKeyboard
    
    await call.message.answer(
        _(TranslationKey.SETTINGS_LANGUAGE, {"language": language}),
        reply_markup=SettingsKeyboard.language_list(language, _),
    )


@router.callback_query(F.data == MenuCallback.HELP)
async def help_callback(
    call: CallbackQuery,
    language: str,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle help menu callback."""
    await call.answer()
    
    if call.message:
        await call.message.delete()
    
    from handlers.commands.help import HELP_TEXTS
    
    help_text = HELP_TEXTS.get(language, HELP_TEXTS["uz"])
    await call.message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=HomeKeyboard.main(_),
    )
