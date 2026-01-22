"""Generation menu keyboards."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keyboards.builders import GenerationCallback
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
        quality: str | None,
        input_fidelity: str | None,
        price: int,
        show_size: bool = False,
        show_aspect_ratio: bool = False,
        show_resolution: bool = False,
        show_quality: bool = False,
        show_input_fidelity: bool = False,
    ) -> InlineKeyboardMarkup:
        """Build main generation menu."""
        default_label = _(TranslationKey.GEN_DEFAULT, None)
        size_label = size if size else default_label
        aspect_label = aspect_ratio if aspect_ratio else default_label
        resolution_label = resolution if resolution else default_label
        quality_label = quality if quality else default_label
        fidelity_label = input_fidelity if input_fidelity else default_label
        model_text = _(TranslationKey.GEN_MODEL, {"model": model_name})

        rows: list[list[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(
                    text=model_text,
                    callback_data=GenerationCallback.MODEL_MENU,
                )
            ]
        ]

        param_buttons: list[InlineKeyboardButton] = []
        if show_size:
            size_text = _(TranslationKey.GEN_SIZE, {"size": size_label})
            param_buttons.append(
                InlineKeyboardButton(
                    text=size_text,
                    callback_data=GenerationCallback.SIZE_MENU,
                )
            )

        if show_aspect_ratio:
            aspect_text = _(TranslationKey.GEN_ASPECT_RATIO, {"ratio": aspect_label})
            param_buttons.append(
                InlineKeyboardButton(
                    text=aspect_text,
                    callback_data=GenerationCallback.RATIO_MENU,
                )
            )

        if show_resolution:
            resolution_text = _(TranslationKey.GEN_RESOLUTION, {"resolution": resolution_label})
            param_buttons.append(
                InlineKeyboardButton(
                    text=resolution_text,
                    callback_data=GenerationCallback.RESOLUTION_MENU,
                )
            )

        if show_quality:
            quality_text = _(TranslationKey.GEN_QUALITY, {"quality": quality_label})
            param_buttons.append(
                InlineKeyboardButton(
                    text=quality_text,
                    callback_data=GenerationCallback.QUALITY_MENU,
                )
            )

        if show_input_fidelity:
            fidelity_text = _(TranslationKey.GEN_INPUT_FIDELITY, {"value": fidelity_label})
            param_buttons.append(
                InlineKeyboardButton(
                    text=fidelity_text,
                    callback_data=GenerationCallback.INPUT_FIDELITY_MENU,
                )
            )

        for i in range(0, len(param_buttons), 2):
            rows.append(param_buttons[i : i + 2])

        start_text = _(TranslationKey.GEN_START_BUTTON, {"price": price})
        rows.append(
            [
                InlineKeyboardButton(
                    text=start_text,
                    callback_data=GenerationCallback.SUBMIT,
                )
            ]
        )

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
            rows.append(
                [
                    InlineKeyboardButton(
                        text=label,
                        callback_data=GenerationCallback.model_set(model_id),
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=GenerationCallback.BACK,
                )
            ]
        )

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
        rows.append(
            [
                InlineKeyboardButton(
                    text=default_label,
                    callback_data=GenerationCallback.size_set("default"),
                )
            ]
        )

        # Size options in pairs
        for i in range(0, len(sizes), 2):
            row = []
            for size in sizes[i : i + 2]:
                label = f"✅ {size}" if size == selected_size else size
                row.append(
                    InlineKeyboardButton(
                        text=label,
                        callback_data=GenerationCallback.size_set(size),
                    )
                )
            rows.append(row)

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=GenerationCallback.BACK,
                )
            ]
        )

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
        rows.append(
            [
                InlineKeyboardButton(
                    text=default_label,
                    callback_data=GenerationCallback.ratio_set("default"),
                )
            ]
        )

        # Ratio options in pairs
        for i in range(0, len(ratios), 2):
            row = []
            for ratio in ratios[i : i + 2]:
                label = f"✅ {ratio}" if ratio == selected_ratio else ratio
                row.append(
                    InlineKeyboardButton(
                        text=label,
                        callback_data=GenerationCallback.ratio_set(ratio),
                    )
                )
            rows.append(row)

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=GenerationCallback.BACK,
                )
            ]
        )

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
        rows.append(
            [
                InlineKeyboardButton(
                    text=default_label,
                    callback_data=GenerationCallback.resolution_set("default"),
                )
            ]
        )

        # Resolution options
        for resolution in resolutions:
            label = f"✅ {resolution}" if resolution == selected_resolution else resolution
            rows.append(
                [
                    InlineKeyboardButton(
                        text=label,
                        callback_data=GenerationCallback.resolution_set(resolution),
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=GenerationCallback.BACK,
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def quality_list(
        qualities: list[str],
        selected_quality: str | None,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build quality selection menu."""
        rows: list[list[InlineKeyboardButton]] = []

        default_text = _(TranslationKey.GEN_DEFAULT, None)
        default_label = f"✅ {default_text}" if not selected_quality else default_text
        rows.append(
            [
                InlineKeyboardButton(
                    text=default_label,
                    callback_data=GenerationCallback.quality_set("default"),
                )
            ]
        )

        for quality in qualities:
            label = f"✅ {quality}" if quality == selected_quality else quality
            rows.append(
                [
                    InlineKeyboardButton(
                        text=label,
                        callback_data=GenerationCallback.quality_set(quality),
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=GenerationCallback.BACK,
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def input_fidelity_list(
        values: list[str],
        selected_value: str | None,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> InlineKeyboardMarkup:
        """Build input fidelity selection menu."""
        rows: list[list[InlineKeyboardButton]] = []

        default_text = _(TranslationKey.GEN_DEFAULT, None)
        default_label = f"✅ {default_text}" if not selected_value else default_text
        rows.append(
            [
                InlineKeyboardButton(
                    text=default_label,
                    callback_data=GenerationCallback.input_fidelity_set("default"),
                )
            ]
        )

        for value in values:
            label = f"✅ {value}" if value == selected_value else value
            rows.append(
                [
                    InlineKeyboardButton(
                        text=label,
                        callback_data=GenerationCallback.input_fidelity_set(value),
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=_(TranslationKey.BACK, None),
                    callback_data=GenerationCallback.BACK,
                )
            ]
        )

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
