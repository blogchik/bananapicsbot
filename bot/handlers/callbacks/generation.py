"""Generation callback handlers."""

import asyncio
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from typing import Callable

from keyboards import GenerationKeyboard, ProfileKeyboard
from keyboards.builders import GenerationCallback
from locales import TranslationKey
from services import GenerationService
from services.generation import GenerationConfig, NormalizedModel
from states import GenerationStates
from core.exceptions import ActiveGenerationError, InsufficientBalanceError
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="generation_callbacks")


def get_support_flags(model: NormalizedModel) -> tuple[bool, bool, bool]:
    """Get display flags for model options."""
    show_size = model.supports_size and bool(model.size_options)
    show_aspect = model.supports_aspect_ratio and bool(model.aspect_ratio_options)
    show_resolution = model.supports_resolution and bool(model.resolution_options)
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


@router.callback_query(F.data == GenerationCallback.MODEL_MENU)
async def open_model_menu(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Open model selection menu."""
    await call.answer()
    
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer(_(TranslationKey.GEN_PROMPT_REQUIRED, None))
        return
    
    try:
        models = await GenerationService.get_models()
    except Exception as e:
        logger.warning("Failed to get models", error=str(e))
        await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    model_id = data.get("model_id")
    
    try:
        await call.message.edit_reply_markup(
            reply_markup=GenerationKeyboard.model_list(
                [{"id": m.id, "name": m.name} for m in models],
                model_id,
                _,
            )
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("gen:model:set:"))
async def select_model(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle model selection."""
    await call.answer()
    
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer(_(TranslationKey.GEN_PROMPT_REQUIRED, None))
        return
    
    try:
        model_id = int(call.data.split(":", 3)[3])
    except (IndexError, ValueError):
        return
    
    try:
        models = await GenerationService.get_models()
    except Exception:
        await call.message.answer(_(TranslationKey.ERROR_CONNECTION, None))
        return
    
    selected = GenerationService.find_model(models, model_id)
    if not selected:
        await call.message.answer(_(TranslationKey.MODEL_NOT_FOUND, None))
        return
    
    show_size, show_aspect, show_resolution = get_support_flags(selected)
    
    # Reset options when model changes
    size = data.get("size") if show_size else None
    aspect_ratio = data.get("aspect_ratio") if show_aspect else None
    resolution = data.get("resolution") if show_resolution else None
    
    await state.update_data(
        model_id=selected.id,
        model_name=selected.name,
        model_key=selected.key,
        price=selected.price,
        size=size,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        supports_size=selected.supports_size,
        supports_aspect_ratio=selected.supports_aspect_ratio,
        supports_resolution=selected.supports_resolution,
        size_options=selected.size_options,
        aspect_ratio_options=selected.aspect_ratio_options,
        resolution_options=selected.resolution_options,
    )
    
    text = build_generation_text(
        prompt, selected.name, size, aspect_ratio, resolution,
        show_size, show_aspect, show_resolution, _,
    )
    
    try:
        await call.message.edit_text(
            text,
            reply_markup=GenerationKeyboard.main(
                _, selected.name, size, aspect_ratio, resolution,
                selected.price, show_size, show_aspect, show_resolution,
            ),
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data == GenerationCallback.SIZE_MENU)
async def open_size_menu(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Open size selection menu."""
    data = await state.get_data()
    size_options = data.get("size_options") or []
    
    if not size_options:
        await call.answer("Bu modelda size mavjud emas.", show_alert=True)
        return
    
    await call.answer()
    
    try:
        await call.message.edit_reply_markup(
            reply_markup=GenerationKeyboard.size_list(size_options, data.get("size"), _)
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("gen:size:set:"))
async def select_size(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle size selection."""
    await call.answer()
    
    size_value = call.data.split(":", 3)[3]
    size = None if size_value == "default" else size_value
    
    await state.update_data(size=size)
    
    data = await state.get_data()
    await _update_generation_menu(call, data, _)


@router.callback_query(F.data == GenerationCallback.RATIO_MENU)
async def open_ratio_menu(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Open aspect ratio selection menu."""
    data = await state.get_data()
    ratio_options = data.get("aspect_ratio_options") or []
    
    if not ratio_options:
        await call.answer("Bu modelda aspect ratio mavjud emas.", show_alert=True)
        return
    
    await call.answer()
    
    try:
        await call.message.edit_reply_markup(
            reply_markup=GenerationKeyboard.aspect_ratio_list(
                ratio_options, data.get("aspect_ratio"), _
            )
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("gen:ratio:set:"))
async def select_ratio(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle aspect ratio selection."""
    await call.answer()
    
    ratio_value = call.data.split(":", 3)[3]
    aspect_ratio = None if ratio_value == "default" else ratio_value
    
    await state.update_data(aspect_ratio=aspect_ratio)
    
    data = await state.get_data()
    await _update_generation_menu(call, data, _)


@router.callback_query(F.data == GenerationCallback.RESOLUTION_MENU)
async def open_resolution_menu(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Open resolution selection menu."""
    data = await state.get_data()
    resolution_options = data.get("resolution_options") or []
    
    if not resolution_options:
        await call.answer("Bu modelda resolution mavjud emas.", show_alert=True)
        return
    
    await call.answer()
    
    try:
        await call.message.edit_reply_markup(
            reply_markup=GenerationKeyboard.resolution_list(
                resolution_options, data.get("resolution"), _
            )
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("gen:resolution:set:"))
async def select_resolution(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle resolution selection."""
    await call.answer()
    
    resolution_value = call.data.split(":", 3)[3]
    resolution = None if resolution_value == "default" else resolution_value
    
    await state.update_data(resolution=resolution)
    
    data = await state.get_data()
    await _update_generation_menu(call, data, _)


@router.callback_query(F.data == GenerationCallback.BACK)
async def back_to_generation(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Go back to generation menu."""
    await call.answer()
    
    data = await state.get_data()
    await _update_generation_menu(call, data, _)


@router.callback_query(F.data == GenerationCallback.SUBMIT)
async def submit_generation(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Submit generation request."""
    await call.answer()
    
    data = await state.get_data()
    prompt = data.get("prompt")
    model_id = data.get("model_id")
    model_name = data.get("model_name", "-")
    price = data.get("price", 0)
    
    if not prompt or not model_id:
        await call.message.answer(_(TranslationKey.GEN_PROMPT_REQUIRED, None))
        return
    
    # Show processing status
    try:
        await call.message.edit_text(_(TranslationKey.GEN_IN_QUEUE, None))
    except TelegramBadRequest:
        pass
    
    # Build config
    config = GenerationConfig(
        prompt=prompt,
        model_id=model_id,
        model_name=model_name,
        model_key=data.get("model_key", ""),
        price=price,
        size=data.get("size") if data.get("supports_size") else None,
        aspect_ratio=data.get("aspect_ratio") if data.get("supports_aspect_ratio") else None,
        resolution=data.get("resolution") if data.get("supports_resolution") else None,
        reference_urls=data.get("reference_urls"),
        reference_file_ids=data.get("reference_file_ids"),
    )
    
    try:
        result = await GenerationService.submit_generation(call.from_user.id, config)
    except ActiveGenerationError:
        await call.message.edit_text(_(TranslationKey.GEN_ACTIVE_EXISTS, None))
        return
    except InsufficientBalanceError:
        await call.message.edit_text(
            _(TranslationKey.INSUFFICIENT_BALANCE, None),
            reply_markup=ProfileKeyboard.main(_),
        )
        return
    except Exception as e:
        logger.error("Generation submit failed", error=str(e))
        await call.message.edit_text(_(TranslationKey.ERROR_GENERIC, None))
        return
    
    request = result.get("request", {})
    request_id = request.get("id")
    request_status = request.get("status")
    
    if not request_id:
        await call.message.answer(_(TranslationKey.ERROR_GENERIC, None))
        await state.clear()
        return
    
    # Handle already completed
    if request_status == "completed":
        try:
            outputs = await GenerationService.get_results(request_id, call.from_user.id)
        except Exception:
            outputs = []
        
        try:
            await call.message.edit_text(_(TranslationKey.GEN_COMPLETED, None))
        except TelegramBadRequest:
            pass

        if outputs:
            caption = GenerationService.build_result_caption(
                prompt, model_name, request.get("cost"), None, _
            )
            await GenerationService.send_results(
                call.message.bot,
                call.message.chat.id,
                outputs,
                data.get("prompt_message_id"),
                caption,
                _,
            )
        await state.clear()
        return
    
    # Start polling
    prompt_message_id = data.get("prompt_message_id") or call.message.message_id
    
    asyncio.create_task(
        GenerationService.poll_generation_status(
            call.message.bot,
            call.message.chat.id,
            call.message.message_id,
            request_id,
            call.from_user.id,
            prompt,
            model_name,
            prompt_message_id,
            _,
        )
    )
    
    await state.clear()


async def _update_generation_menu(
    call: CallbackQuery,
    data: dict,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Update generation menu with current settings."""
    prompt = data.get("prompt", "")
    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")
    price = data.get("price", 0)
    
    show_size = data.get("supports_size") and bool(data.get("size_options"))
    show_aspect = data.get("supports_aspect_ratio") and bool(data.get("aspect_ratio_options"))
    show_resolution = data.get("supports_resolution") and bool(data.get("resolution_options"))
    
    text = build_generation_text(
        prompt, model_name, size, aspect_ratio, resolution,
        show_size, show_aspect, show_resolution, _,
    )
    
    try:
        await call.message.edit_text(
            text,
            reply_markup=GenerationKeyboard.main(
                _, model_name, size, aspect_ratio, resolution,
                price, show_size, show_aspect, show_resolution,
            ),
        )
    except TelegramBadRequest:
        pass
