"""Payment keyboards."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from locales import TranslationKey

from keyboards.builders import MenuCallback, TopupCallback


class PaymentKeyboard:
    """Payment keyboard builder."""

    @staticmethod
    def topup_menu(
        presets: list[tuple[int, int]],
        min_price: int | None,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build top-up menu with preset amounts."""
        rows: list[list[InlineKeyboardButton]] = []

        # Preset amounts in a single column
        for amount, credits in presets:
            gens = (credits // min_price) if min_price else 0
            label = _(TranslationKey.TOPUP_PRESET_LABEL, {
                "stars": amount,
                "credits": credits,
                "gens": gens,
            })
            rows.append([
                InlineKeyboardButton(
                    text=label,
                    callback_data=TopupCallback.stars(amount),
                )
            ])

        # Custom amount button
        rows.append([
            InlineKeyboardButton(
                text=_(TranslationKey.TOPUP_CUSTOM, None),
                callback_data=TopupCallback.CUSTOM,
            )
        ])

        # Back button
        rows.append([
            InlineKeyboardButton(
                text=_(TranslationKey.BACK, None),
                callback_data=MenuCallback.PROFILE,
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=rows)
