"""Referral menu keyboard."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keyboards.builders import MenuCallback
from locales import TranslationKey


class ReferralKeyboard:
    """Referral menu keyboard builder."""

    @staticmethod
    def main(_: Callable[[TranslationKey, dict | None], str]) -> InlineKeyboardMarkup:
        """Build referral menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.BACK, None),
                        callback_data=MenuCallback.PROFILE,
                    )
                ],
            ]
        )
