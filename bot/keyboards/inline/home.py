"""Home menu keyboard."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Callable

from keyboards.builders import MenuCallback
from locales import TranslationKey


class HomeKeyboard:
    """Home menu keyboard builder."""
    
    @staticmethod
    def main(_: Callable[[TranslationKey, dict | None], str]) -> InlineKeyboardMarkup:
        """Build main home menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BTN_START, None),
                        callback_data=MenuCallback.INFO,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BTN_PROFILE, None),
                        callback_data=MenuCallback.PROFILE,
                    )
                ],
            ]
        )
