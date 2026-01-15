"""Payment keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Callable

from keyboards.builders import TopupCallback, MenuCallback
from locales import TranslationKey


class PaymentKeyboard:
    """Payment keyboard builder."""
    
    @staticmethod
    def topup_menu(
        presets: list[tuple[int, int]],
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build top-up menu with preset amounts."""
        rows: list[list[InlineKeyboardButton]] = []
        
        # Preset amounts in pairs
        for i in range(0, len(presets), 2):
            row = []
            for amount, credits in presets[i:i + 2]:
                row.append(
                    InlineKeyboardButton(
                        text=f"{amount} ⭐ → {credits} cr",
                        callback_data=TopupCallback.stars(amount),
                    )
                )
            rows.append(row)
        
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
