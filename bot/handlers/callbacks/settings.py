"""Settings callback handlers."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from typing import Callable

from keyboards import SettingsKeyboard
from keyboards.builders import SettingsCallback, MenuCallback
from locales import TranslationKey, set_user_language, LocaleManager
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="settings_callbacks")


@router.callback_query(F.data == SettingsCallback.LANGUAGE_MENU)
async def language_menu(
    call: CallbackQuery,
    language: str,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Show language selection menu."""
    await call.answer()
    
    if call.message:
        await call.message.delete()
    
    await call.message.answer(
        _(TranslationKey.SETTINGS_LANGUAGE, {"language": language}),
        reply_markup=SettingsKeyboard.language_list(language, _),
    )


@router.callback_query(F.data.startswith("settings:lang:"))
async def set_language(
    call: CallbackQuery,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle language selection."""
    await call.answer()
    
    lang_code = call.data.split(":", 2)[2]
    manager = LocaleManager.get_instance()
    
    if lang_code not in manager.available_languages:
        return
    
    # Save user language preference
    await set_user_language(call.from_user.id, lang_code)
    
    # Get new translator
    from locales import get_translator
    new_translator = get_translator(lang_code)
    
    language_name = manager.language_names.get(lang_code, lang_code)
    
    if call.message:
        await call.message.delete()
    
    from keyboards import ProfileKeyboard
    
    await call.message.answer(
        new_translator(TranslationKey.SETTINGS_LANGUAGE_CHANGED, {"language": language_name}),
        reply_markup=ProfileKeyboard.main(new_translator),
    )
