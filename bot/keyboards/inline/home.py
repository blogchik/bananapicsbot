"""Home menu keyboard."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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
                        text=_(TranslationKey.BTN_GENERATION, None),
                        callback_data=MenuCallback.GENERATION,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BTN_WATERMARK, None),
                        callback_data=MenuCallback.WATERMARK,
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
