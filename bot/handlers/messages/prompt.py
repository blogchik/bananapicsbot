"""Prompt message handler."""

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from typing import Callable

from keyboards import GenerationKeyboard
from locales import TranslationKey
from services import GenerationService
from core.constants import BotConstants
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="prompt")


def get_support_flags(data: dict) -> tuple[bool, bool, bool]:
    """Get display flags from state data."""
    show_size = data.get("supports_size") and bool(data.get("size_options"))
    show_aspect = data.get("supports_aspect_ratio") and bool(data.get("aspect_ratio_options"))
    show_resolution = data.get("supports_resolution") and bool(data.get("resolution_options"))
    return show_size, show_aspect, show_resolution


def build_generation_text(
    prompt: str,
    model_name: str,
    size: str | None,
    aspect_ratio: str | None,
    resolution: str | None,
    show_size: bool,
    show_aspect: bool,
    show_resolution: bool,
    _: Callable[[TranslationKey, dict | None], str],
) -> str:
    """Build generation settings text."""
    default_label = _(TranslationKey.GEN_DEFAULT, None)
    size_label = size if size else default_label
    aspect_label = aspect_ratio if aspect_ratio else default_label
    resolution_label = resolution if resolution else default_label
    
    lines = [
        _(TranslationKey.GEN_SETTINGS_TITLE, None),
        _(TranslationKey.GEN_PROMPT, {"prompt": prompt}),
        _(TranslationKey.GEN_MODEL, {"model": model_name}),
    ]
    
    if show_size:
        lines.append(_(TranslationKey.GEN_SIZE, {"size": size_label}))
    if show_aspect:
        lines.append(_(TranslationKey.GEN_ASPECT_RATIO, {"ratio": aspect_label}))
    if show_resolution:
        lines.append(_(TranslationKey.GEN_RESOLUTION, {"resolution": resolution_label}))
    
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
    
    # Check for active generation
    if await GenerationService.has_active_generation(user.id):
        await message.answer(_(TranslationKey.GEN_ACTIVE_EXISTS, None))
        return
    
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
    
    selected_model = models[0]
    
    # Delete previous menu if exists
    data = await state.get_data()
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
    
    # Save state
    await state.update_data(
        prompt=prompt,
        model_id=selected_model.id,
        model_name=selected_model.name,
        model_key=selected_model.key,
        prompt_message_id=message.message_id,
        price=selected_model.price,
        size=None,
        aspect_ratio=None,
        resolution=None,
        supports_size=selected_model.supports_size,
        supports_aspect_ratio=selected_model.supports_aspect_ratio,
        supports_resolution=selected_model.supports_resolution,
        size_options=selected_model.size_options,
        aspect_ratio_options=selected_model.aspect_ratio_options,
        resolution_options=selected_model.resolution_options,
    )
    
    # Build menu text
    menu_text = build_generation_text(
        prompt, selected_model.name, None, None, None,
        show_size, show_aspect, show_resolution, _,
    )
    
    # Send menu
    menu = GenerationKeyboard.main(
        _, selected_model.name, None, None, None,
        selected_model.price, show_size, show_aspect, show_resolution,
    )
    
    msg = await message.answer(
        menu_text,
        reply_markup=menu,
        reply_to_message_id=message.message_id,
    )
    
    await state.update_data(menu_message_id=msg.message_id)
