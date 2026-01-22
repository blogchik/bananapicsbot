"""Settings keyboards."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from locales import LocaleManager, TranslationKey

from keyboards.builders import MenuCallback, SettingsCallback


class SettingsKeyboard:
    """Settings keyboard builder."""

    @staticmethod
    def main(
        current_language: str,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build main settings menu."""
        manager = LocaleManager.get_instance()
        language_name = manager.language_names.get(current_language, current_language)

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🌐 {language_name}",
                        callback_data=SettingsCallback.LANGUAGE_MENU,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.HOME, None),
                        callback_data=MenuCallback.HOME,
                    )
                ],
            ]
        )

    @staticmethod
    def language_list(
        current_language: str,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build language selection menu."""
        manager = LocaleManager.get_instance()
        rows: list[list[InlineKeyboardButton]] = []

        for code, name in manager.language_names.items():
            label = f"✅ {name}" if code == current_language else name
            rows.append(
                [
                    InlineKeyboardButton(
                        text=label,
                        callback_data=SettingsCallback.language_set(code),
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=MenuCallback.PROFILE,
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=rows)
