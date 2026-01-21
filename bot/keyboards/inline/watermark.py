"""Watermark tool keyboards."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from core.constants import BotConstants
from locales import TranslationKey

from keyboards.builders import ImageToolCallback, WatermarkCallback


class WatermarkKeyboard:
    """Watermark tool keyboard builder."""

    @staticmethod
    def main(
        _: Callable[[TranslationKey, dict | None], str],
        message_id: int,
    ) -> InlineKeyboardMarkup:
        """Build image tools menu with all available tools."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.WM_REMOVE_BUTTON, {"price": BotConstants.WATERMARK_REMOVE_COST}),
                        callback_data=WatermarkCallback.remove(message_id),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.TOOL_UPSCALE_BUTTON, {"price": BotConstants.UPSCALE_COST}),
                        callback_data=ImageToolCallback.upscale(message_id),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.TOOL_DENOISE_BUTTON, {"price": BotConstants.DENOISE_COST}),
                        callback_data=ImageToolCallback.denoise(message_id),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.TOOL_RESTORE_BUTTON, {"price": BotConstants.RESTORE_COST}),
                        callback_data=ImageToolCallback.restore(message_id),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.TOOL_ENHANCE_BUTTON, {"price": BotConstants.ENHANCE_COST}),
                        callback_data=ImageToolCallback.enhance(message_id),
                    )
                ],
            ]
        )
