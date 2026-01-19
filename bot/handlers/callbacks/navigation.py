"""Navigation callback handlers."""

from typing import Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery
from core.logging import get_logger
from keyboards import HomeKeyboard, ProfileKeyboard
from keyboards.builders import MenuCallback
from locales import TranslationKey
from services import GenerationService, UserService

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


@router.callback_query(F.data == MenuCallback.GENERATION)
async def generation_menu_callback(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle generation menu callback."""
    await call.answer()

    await call.message.answer(_(TranslationKey.GEN_MENU_TEXT, None))


@router.callback_query(F.data == MenuCallback.WATERMARK)
async def watermark_menu_callback(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle watermark menu callback."""
    await call.answer()

    await call.message.answer(_(TranslationKey.WM_MENU_TEXT, None))


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
