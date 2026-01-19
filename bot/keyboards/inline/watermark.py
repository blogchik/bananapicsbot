"""Watermark tool keyboards."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from core.constants import BotConstants
from locales import TranslationKey

from keyboards.builders import WatermarkCallback


class WatermarkKeyboard:
    """Watermark tool keyboard builder."""

    @staticmethod
    def main(
        _: Callable[[TranslationKey, dict | None], str],
        message_id: int,
    ) -> InlineKeyboardMarkup:
        """Build watermark tool menu."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.WM_REMOVE_BUTTON, {"price": BotConstants.WATERMARK_REMOVE_COST}),
                        callback_data=WatermarkCallback.remove(message_id),
                    )
                ]
            ]
        )
