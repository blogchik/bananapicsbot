"""Profile menu keyboard."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Callable

from keyboards.builders import MenuCallback
from locales import TranslationKey


class ProfileKeyboard:
    """Profile menu keyboard builder."""
    
    @staticmethod
    def main(_: Callable[[TranslationKey, dict | None], str]) -> InlineKeyboardMarkup:
        """Build profile menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BTN_TOPUP, None),
                        callback_data=MenuCallback.TOPUP,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BTN_REFERRAL, None),
                        callback_data=MenuCallback.REFERRAL,
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
