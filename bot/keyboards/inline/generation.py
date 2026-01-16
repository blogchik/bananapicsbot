"""Generation menu keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Callable

from keyboards.builders import GenerationCallback, MenuCallback
from locales import TranslationKey


class GenerationKeyboard:
    """Generation menu keyboard builder."""
    
    @staticmethod
    def main(
        _: Callable[[TranslationKey, dict | None], str],
        model_name: str,
        size: str | None,
        aspect_ratio: str | None,
        resolution: str | None,
        price: int,
        show_size: bool = False,
        show_aspect_ratio: bool = False,
        show_resolution: bool = False,
    ) -> InlineKeyboardMarkup:
        """Build main generation menu."""
        default_label = _(TranslationKey.GEN_DEFAULT, None)
        size_label = size if size else default_label
        aspect_label = aspect_ratio if aspect_ratio else default_label
        resolution_label = resolution if resolution else default_label
        model_text = _(TranslationKey.GEN_MODEL, {"model": model_name})
        
        rows: list[list[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(
                    text=f"🧠 {model_text}",
                    callback_data=GenerationCallback.MODEL_MENU,
                )
            ]
        ]
        
        if show_size:
            size_text = _(TranslationKey.GEN_SIZE, {"size": size_label})
            rows.append([
                InlineKeyboardButton(
                    text=f"📐 {size_text}",
                    callback_data=GenerationCallback.SIZE_MENU,
                )
            ])
        
        if show_aspect_ratio:
            aspect_text = _(TranslationKey.GEN_ASPECT_RATIO, {"ratio": aspect_label})
            rows.append([
                InlineKeyboardButton(
                    text=f"📏 {aspect_text}",
                    callback_data=GenerationCallback.RATIO_MENU,
                )
            ])
        
        if show_resolution:
            resolution_text = _(TranslationKey.GEN_RESOLUTION, {"resolution": resolution_label})
            rows.append([
                InlineKeyboardButton(
                    text=f"🖼️ {resolution_text}",
                    callback_data=GenerationCallback.RESOLUTION_MENU,
                )
            ])
        
        start_text = _(TranslationKey.GEN_START_BUTTON, {"price": price})
        rows.append([
            InlineKeyboardButton(
                text=start_text,
                callback_data=GenerationCallback.SUBMIT,
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=rows)
    
    @staticmethod
    def model_list(
        models: list[dict],
        selected_id: int | None,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build model selection menu."""
        rows: list[list[InlineKeyboardButton]] = []
        
        for model in models:
            model_id = int(model["id"])
            name = str(model["name"])
            label = f"✅ {name}" if selected_id == model_id else name
            rows.append([
                InlineKeyboardButton(
                    text=label,
                    callback_data=GenerationCallback.model_set(model_id),
                )
            ])
        
        rows.append([
            InlineKeyboardButton(
                text=_(TranslationKey.BACK, None),
                callback_data=GenerationCallback.BACK,
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=rows)
    
    @staticmethod
    def size_list(
        sizes: list[str],
        selected_size: str | None,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build size selection menu."""
        rows: list[list[InlineKeyboardButton]] = []
        
        # Default option
        default_text = _(TranslationKey.GEN_DEFAULT, None)
        default_label = f"✅ {default_text}" if not selected_size else default_text
        rows.append([
            InlineKeyboardButton(
                text=default_label,
                callback_data=GenerationCallback.size_set("default"),
            )
        ])
        
        # Size options in pairs
        for i in range(0, len(sizes), 2):
            row = []
            for size in sizes[i:i + 2]:
                label = f"✅ {size}" if size == selected_size else size
                row.append(
                    InlineKeyboardButton(
                        text=label,
                        callback_data=GenerationCallback.size_set(size),
                    )
                )
            rows.append(row)
        
        rows.append([
            InlineKeyboardButton(
                text=_(TranslationKey.BACK, None),
                callback_data=GenerationCallback.BACK,
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=rows)
    
    @staticmethod
    def aspect_ratio_list(
        ratios: list[str],
        selected_ratio: str | None,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build aspect ratio selection menu."""
        rows: list[list[InlineKeyboardButton]] = []
        
        # Default option
        default_text = _(TranslationKey.GEN_DEFAULT, None)
        default_label = f"✅ {default_text}" if not selected_ratio else default_text
        rows.append([
            InlineKeyboardButton(
                text=default_label,
                callback_data=GenerationCallback.ratio_set("default"),
            )
        ])
        
        # Ratio options in pairs
        for i in range(0, len(ratios), 2):
            row = []
            for ratio in ratios[i:i + 2]:
                label = f"✅ {ratio}" if ratio == selected_ratio else ratio
                row.append(
                    InlineKeyboardButton(
                        text=label,
                        callback_data=GenerationCallback.ratio_set(ratio),
                    )
                )
            rows.append(row)
        
        rows.append([
            InlineKeyboardButton(
                text=_(TranslationKey.BACK, None),
                callback_data=GenerationCallback.BACK,
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=rows)
    
    @staticmethod
    def resolution_list(
        resolutions: list[str],
        selected_resolution: str | None,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build resolution selection menu."""
        rows: list[list[InlineKeyboardButton]] = []
        
        # Default option
        default_text = _(TranslationKey.GEN_DEFAULT, None)
        default_label = f"✅ {default_text}" if not selected_resolution else default_text
        rows.append([
            InlineKeyboardButton(
                text=default_label,
                callback_data=GenerationCallback.resolution_set("default"),
            )
        ])
        
        # Resolution options
        for resolution in resolutions:
            label = f"✅ {resolution}" if resolution == selected_resolution else resolution
            rows.append([
                InlineKeyboardButton(
                    text=label,
                    callback_data=GenerationCallback.resolution_set(resolution),
                )
            ])
        
        rows.append([
            InlineKeyboardButton(
                text=_(TranslationKey.BACK, None),
                callback_data=GenerationCallback.BACK,
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def retry(_: Callable[[TranslationKey, dict | None], str]) -> InlineKeyboardMarkup:
        """Build retry keyboard for failed generation."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_(TranslationKey.GEN_RETRY, None),
                        callback_data=GenerationCallback.RETRY,
                    )
                ]
            ]
        )
