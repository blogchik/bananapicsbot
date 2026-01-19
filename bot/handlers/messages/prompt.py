"""Prompt message handler."""

from typing import Callable

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from core.constants import BotConstants
from core.logging import get_logger
from keyboards import GenerationKeyboard
from locales import TranslationKey
from services import GenerationService

logger = get_logger(__name__)
router = Router(name="prompt")


def get_support_flags(data: dict) -> tuple[bool, bool, bool, bool, bool]:
    """Get display flags from state data."""
    show_size = data.get("supports_size") and bool(data.get("size_options"))
    show_aspect = data.get("supports_aspect_ratio") and bool(data.get("aspect_ratio_options"))
    show_resolution = data.get("supports_resolution") and bool(data.get("resolution_options"))
    show_quality = data.get("supports_quality") and bool(data.get("quality_options"))
    show_input_fidelity = data.get("supports_input_fidelity") and bool(
        data.get("input_fidelity_options")
    )
    return show_size, show_aspect, show_resolution, show_quality, show_input_fidelity


def build_generation_text(
    prompt: str,
    model_name: str,
    size: str | None,
    aspect_ratio: str | None,
    resolution: str | None,
    show_size: bool,
    show_aspect: bool,
    show_resolution: bool,
    has_reference: bool,
    _: Callable[[TranslationKey, dict | None], str],
) -> str:
    """Build generation settings text."""
    import html

    escaped_prompt = html.escape(prompt)
    prompt_text = _(TranslationKey.GEN_PROMPT, {"prompt": f"<blockquote>{escaped_prompt}</blockquote>"})
    title_key = TranslationKey.GEN_SETTINGS_TITLE_I2I if has_reference else TranslationKey.GEN_SETTINGS_TITLE_T2I
    lines = [
        _(title_key, None),
        prompt_text,
    ]
    return "\n".join(lines)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_prompt_message(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle text message as generation prompt."""
    user = message.from_user
    if not user:
        return

    prompt = (message.caption or message.text or "").strip()
    if not prompt:
        await message.answer(_(TranslationKey.GEN_PROMPT_REQUIRED, None))
        return

    # Limit prompt length
    if len(prompt) > BotConstants.MAX_PROMPT_LENGTH:
        prompt = prompt[:BotConstants.MAX_PROMPT_LENGTH]

    # Get models
    try:
        models = await GenerationService.get_models()
    except Exception as e:
        logger.warning("Failed to get models", error=str(e))
        await message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return

    if not models:
        await message.answer(_(TranslationKey.MODEL_NOT_FOUND, None))
        return

    defaults = await GenerationService.get_generation_defaults(user.id)
    selected_model = models[0]
    default_model_id = defaults.get("model_id")
    if isinstance(default_model_id, int):
        saved_model = GenerationService.find_model(models, default_model_id)
        if saved_model:
            selected_model = saved_model

    # Delete previous menu if exists
    data = await state.get_data()
    has_reference_media = bool(message.photo or message.document)
    if not has_reference_media and (data.get("reference_urls") or data.get("reference_file_ids")):
        await state.update_data(reference_urls=[], reference_file_ids=[])
        data = {**data, "reference_urls": [], "reference_file_ids": []}

    references = data.get("reference_urls") or []
    has_reference = bool(references or data.get("reference_file_ids"))
    previous_menu_id = data.get("menu_message_id")
    if previous_menu_id:
        try:
            await message.bot.delete_message(message.chat.id, previous_menu_id)
        except TelegramBadRequest:
            pass

    # Get model options
    show_size = selected_model.supports_size and bool(selected_model.size_options)
    show_aspect = selected_model.supports_aspect_ratio and bool(selected_model.aspect_ratio_options)
    show_resolution = selected_model.supports_resolution and bool(selected_model.resolution_options)
    show_quality = selected_model.supports_quality and bool(selected_model.quality_options)
    show_input_fidelity = selected_model.supports_input_fidelity and bool(
        selected_model.input_fidelity_options
    )

    size = defaults.get("size") if show_size else None
    aspect_ratio = defaults.get("aspect_ratio") if show_aspect else None
    resolution = defaults.get("resolution") if show_resolution else None
    quality = defaults.get("quality") if show_quality else None
    input_fidelity = defaults.get("input_fidelity") if show_input_fidelity else None

    if size and selected_model.size_options and size not in selected_model.size_options:
        size = None
    if aspect_ratio and selected_model.aspect_ratio_options and aspect_ratio not in selected_model.aspect_ratio_options:
        aspect_ratio = None
    if resolution and selected_model.resolution_options and resolution not in selected_model.resolution_options:
        resolution = None
    if quality and selected_model.quality_options and quality not in selected_model.quality_options:
        quality = None
    if input_fidelity and selected_model.input_fidelity_options and input_fidelity not in selected_model.input_fidelity_options:
        input_fidelity = None

    # Save state
    await state.update_data(
        prompt=prompt,
        model_id=selected_model.id,
        model_name=selected_model.name,
        model_key=selected_model.key,
        prompt_message_id=message.message_id,
        price=GenerationService.calculate_generation_price(
            selected_model.key,
            selected_model.price,
            size,
            resolution,
            quality,
            is_image_to_image=has_reference,
        ),
        size=size,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        quality=quality,
        input_fidelity=input_fidelity,
        supports_size=selected_model.supports_size,
        supports_aspect_ratio=selected_model.supports_aspect_ratio,
        supports_resolution=selected_model.supports_resolution,
        supports_quality=selected_model.supports_quality,
        supports_input_fidelity=selected_model.supports_input_fidelity,
        size_options=selected_model.size_options,
        aspect_ratio_options=selected_model.aspect_ratio_options,
        resolution_options=selected_model.resolution_options,
        quality_options=selected_model.quality_options,
        input_fidelity_options=selected_model.input_fidelity_options,
    )

    # Build menu text
    menu_text = build_generation_text(
        prompt, selected_model.name, size, aspect_ratio, resolution,
        show_size, show_aspect, show_resolution, has_reference, _,
    )

    # Send menu
    menu = GenerationKeyboard.main(
        _, selected_model.name, size, aspect_ratio, resolution,
        quality,
        input_fidelity,
        GenerationService.calculate_generation_price(
            selected_model.key,
            selected_model.price,
            size,
            resolution,
            quality,
            is_image_to_image=has_reference,
        ),
        show_size,
        show_aspect,
        show_resolution,
        show_quality,
        show_input_fidelity,
    )

    msg = await message.answer(
        menu_text,
        reply_markup=menu,
        reply_to_message_id=message.message_id,
    )

    await state.update_data(menu_message_id=msg.message_id)
    await GenerationService.save_generation_defaults(
        user.id,
        selected_model.id,
        size,
        aspect_ratio,
        resolution,
        quality,
        input_fidelity,
        store_resolution=selected_model.supports_resolution,
    )
