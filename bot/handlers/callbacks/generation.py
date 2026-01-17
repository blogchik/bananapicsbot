"""Generation callback handlers."""

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LinkPreviewOptions
from typing import Callable

from keyboards import GenerationKeyboard, ProfileKeyboard
from keyboards.builders import GenerationCallback
from locales import TranslationKey
from services import GenerationService
from services.generation import GenerationConfig, NormalizedModel
from states import GenerationStates
from core.exceptions import (
    ActiveGenerationError,
    InsufficientBalanceError,
    ProviderUnavailableError,
)
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


def build_model_menu_text(
    models: list[NormalizedModel],
    _: Callable[[TranslationKey, dict | None], str],
) -> str:
    """Build model selection info text."""
    import html

    lines: list[str] = []
    quality_label = _(TranslationKey.GEN_MODEL_MENU_QUALITY, None)
    duration_label = _(TranslationKey.GEN_MODEL_MENU_DURATION, None)
    seconds_label = _(TranslationKey.GEN_MODEL_MENU_SECONDS, None)
    minutes_label = _(TranslationKey.GEN_MODEL_MENU_MINUTES, None)
    price_label = _(TranslationKey.GEN_MODEL_MENU_PRICE, None)

    for model in models:
        emoji = model_emoji(model)
        safe_name = html.escape(model.name)
        name_line = f"{emoji} <b>{safe_name}</b>".strip()
        stars = model.quality_stars if model.quality_stars is not None else 0
        stars = max(0, min(5, stars))
        star_text = "★" * stars + "☆" * (5 - stars) if stars else "-"
        duration_text = "-"
        if model.avg_duration_seconds_min is not None and model.avg_duration_seconds_max is not None:
            min_sec = max(0, model.avg_duration_seconds_min)
            max_sec = max(0, model.avg_duration_seconds_max)
            if max_sec >= 60:
                min_min = max(1, min_sec // 60) if min_sec else 1
                max_min = max(1, (max_sec + 59) // 60)
                duration_text = f"{min_min}-{max_min} {minutes_label}"
            else:
                duration_text = f"{min_sec}-{max_sec} {seconds_label}"
        elif model.avg_duration_text:
            duration_text = model.avg_duration_text
        lines.extend([
            name_line,
            f"{quality_label}: {star_text}",
            f"{duration_label}: {duration_text}",
            f"{price_label}: {model.price} cr",
            "",
        ])

    hint = _(TranslationKey.GEN_MODEL_MENU_HINT, None).strip()
    if hint:
        lines.append(hint)
    return "\n".join(lines).strip()


def model_emoji(model: NormalizedModel) -> str:
    """Get emoji for model."""
    key = (model.key or "").lower()
    if key == "nano-banana":
        return "🍌"
    if key == "nano-banana-pro":
        return "🔥"
    if key == "seedream-v4":
        return "☁️"
    return "✨"


def get_ratio_preview_url(ratio: str) -> str | None:
    """Get preview image URL for aspect ratio."""
    return {
        "1:1": "https://img1.teletype.in/files/45/36/4536730e-d817-4526-9a54-0712000ab797.jpeg",
        "2:3": "https://img2.teletype.in/files/58/33/5833e4d5-ffcd-4406-90cd-57a5b35762ab.jpeg",
        "3:2": "https://img3.teletype.in/files/6d/ae/6daef1e0-151a-4b67-866a-7ce9639f47f3.jpeg",
        "3:4": "https://img2.teletype.in/files/dc/e4/dce43e0a-8199-4f5e-82f8-557306ba5ffa.jpeg",
        "4:3": "https://img2.teletype.in/files/5f/78/5f782960-5e93-4b8e-87d2-f5eb51bd96f2.jpeg",
        "4:5": "https://img4.teletype.in/files/f4/b0/f4b0cfff-1332-421f-afd0-bb9daf453572.jpeg",
        "5:4": "https://img3.teletype.in/files/aa/29/aa29c0a7-97a6-4db7-b968-ac715eaaf19d.jpeg",
        "9:16": "https://img1.teletype.in/files/cc/d8/ccd871ca-e2b1-4457-ab23-437573998b0c.jpeg",
        "16:9": "https://img4.teletype.in/files/35/d1/35d16a47-cb5d-487e-847a-1a463ac49985.jpeg",
        "21:9": "https://img1.teletype.in/files/0d/e8/0de8a652-680f-44e9-8e78-fabc90f76ee8.jpeg",
    }.get(ratio)


def get_resolution_preview_url() -> str:
    """Get preview image URL for resolution selection."""
    return "https://img3.teletype.in/files/e7/1d/e71d4ab1-fcb5-4d33-90fa-a1c6b9640fd9.png"


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
        await call.message.edit_text(
            build_model_menu_text(models, _),
            reply_markup=GenerationKeyboard.model_list(
                [
                    {"id": m.id, "name": f"{model_emoji(m)} {m.name}".strip()}
                    for m in models
                ],
                model_id,
                _,
            ),
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
        price=GenerationService.calculate_generation_price(
            selected.key,
            selected.price,
            size,
            resolution,
        ),
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

    await GenerationService.save_generation_defaults(
        call.from_user.id,
        selected.id,
        size,
        aspect_ratio,
        resolution,
        store_resolution=selected.supports_resolution,
    )

    try:
        await call.message.edit_reply_markup(
            reply_markup=GenerationKeyboard.model_list(
                [
                    {"id": m.id, "name": f"{model_emoji(m)} {m.name}".strip()}
                    for m in models
                ],
                selected.id,
                _,
            )
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
    model_id = data.get("model_id")
    if model_id:
        await GenerationService.save_generation_defaults(
            call.from_user.id,
            int(model_id),
            size,
            data.get("aspect_ratio"),
            data.get("resolution"),
            store_resolution=bool(data.get("supports_resolution")),
        )
    try:
        await call.message.edit_reply_markup(
            reply_markup=GenerationKeyboard.size_list(
                data.get("size_options") or [],
                size,
                _,
            )
        )
    except TelegramBadRequest:
        pass


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

    selected_ratio = data.get("aspect_ratio") or (ratio_options[0] if ratio_options else None)
    preview_url = get_ratio_preview_url(selected_ratio) if selected_ratio else None
    caption = _(TranslationKey.GEN_ASPECT_MENU_TITLE, None)

    try:
        if preview_url and call.message:
            await call.message.delete()
            msg = await call.message.bot.send_message(
                chat_id=call.message.chat.id,
                text=caption,
                reply_markup=GenerationKeyboard.aspect_ratio_list(
                    ratio_options, selected_ratio, _
                ),
                link_preview_options=LinkPreviewOptions(
                    url=preview_url,
                    is_disabled=False,
                    show_above_text=True,
                ),
            )
            await state.update_data(menu_message_id=msg.message_id)
        else:
            await call.message.edit_reply_markup(
                reply_markup=GenerationKeyboard.aspect_ratio_list(
                    ratio_options, selected_ratio, _
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
    model_id = data.get("model_id")
    if model_id:
        await GenerationService.save_generation_defaults(
            call.from_user.id,
            int(model_id),
            data.get("size"),
            aspect_ratio,
            data.get("resolution"),
            store_resolution=bool(data.get("supports_resolution")),
        )
    try:
        ratio_options = data.get("aspect_ratio_options") or []
        preview_url = get_ratio_preview_url(aspect_ratio) if aspect_ratio else None
        if preview_url and call.message:
            caption = _(TranslationKey.GEN_ASPECT_MENU_TITLE, None)
            await call.message.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=caption,
                reply_markup=GenerationKeyboard.aspect_ratio_list(
                    ratio_options,
                    aspect_ratio,
                    _,
                ),
                link_preview_options=LinkPreviewOptions(
                    url=preview_url,
                    is_disabled=False,
                    show_above_text=True,
                ),
            )
        else:
            await call.message.edit_reply_markup(
                reply_markup=GenerationKeyboard.aspect_ratio_list(
                    ratio_options,
                    aspect_ratio,
                    _,
                )
            )
    except TelegramBadRequest:
        pass


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
        preview_url = get_resolution_preview_url()
        caption = _(TranslationKey.GEN_RESOLUTION_MENU_TITLE, None)
        if call.message:
            await call.message.delete()
            msg = await call.message.bot.send_message(
                chat_id=call.message.chat.id,
                text=caption,
                reply_markup=GenerationKeyboard.resolution_list(
                    resolution_options, data.get("resolution"), _
                ),
                link_preview_options=LinkPreviewOptions(
                    url=preview_url,
                    is_disabled=False,
                    show_above_text=True,
                ),
            )
            await state.update_data(menu_message_id=msg.message_id)
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
    price = GenerationService.calculate_generation_price(
        data.get("model_key"),
        int(data.get("price") or 0),
        data.get("size"),
        resolution,
    )
    await state.update_data(price=price)
    
    model_id = data.get("model_id")
    if model_id:
        await GenerationService.save_generation_defaults(
            call.from_user.id,
            int(model_id),
            data.get("size"),
            data.get("aspect_ratio"),
            resolution,
        )
    try:
        resolution_options = data.get("resolution_options") or []
        if call.message:
            await call.message.bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=GenerationKeyboard.resolution_list(
                    resolution_options,
                    resolution,
                    _,
                ),
            )
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        pass


@router.callback_query(F.data == GenerationCallback.BACK)
async def back_to_generation(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Go back to generation menu."""
    await call.answer()
    
    data = await state.get_data()
    if call.message and call.message.text:
        model_name = data.get("model_name", "-")
        size = data.get("size")
        aspect_ratio = data.get("aspect_ratio")
        resolution = data.get("resolution")
        price = GenerationService.calculate_generation_price(
            data.get("model_key"),
            int(data.get("price") or 0),
            size,
            resolution,
        )
        show_size = data.get("supports_size") and bool(data.get("size_options"))
        show_aspect = data.get("supports_aspect_ratio") and bool(data.get("aspect_ratio_options"))
        show_resolution = data.get("supports_resolution") and bool(data.get("resolution_options"))
        has_reference = bool(data.get("reference_urls"))
        text = build_generation_text(
            data.get("prompt", ""),
            model_name,
            size,
            aspect_ratio,
            resolution,
            show_size,
            show_aspect,
            show_resolution,
            has_reference,
            _,
        )
        try:
            await call.message.delete()
        except TelegramBadRequest:
            pass
        msg = await call.message.bot.send_message(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=GenerationKeyboard.main(
                _,
                model_name,
                size,
                aspect_ratio,
                resolution,
                int(price),
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
        await state.update_data(menu_message_id=msg.message_id)
        return
    await _update_generation_menu(call, data, _)


@router.callback_query(F.data == GenerationCallback.SUBMIT)
async def submit_generation(
    call: CallbackQuery,
    state: FSMContext,
    language: str,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Submit generation request."""
    await call.answer()
    
    data = await state.get_data()
    prompt = data.get("prompt")
    model_id = data.get("model_id")
    model_name = data.get("model_name", "-")
    price = data.get("price", 0)
    resolution = data.get("resolution")
    price = GenerationService.calculate_generation_price(
        data.get("model_key"),
        int(price or 0),
        data.get("size"),
        resolution,
    )
    
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
        language=language,
        reference_urls=data.get("reference_urls"),
        reference_file_ids=data.get("reference_file_ids"),
        chat_id=call.message.chat.id if call.message else None,
        message_id=call.message.message_id if call.message else None,
        prompt_message_id=data.get("prompt_message_id"),
    )

    await GenerationService.save_last_request(
        call.from_user.id,
        {
            "prompt": config.prompt,
            "model_id": config.model_id,
            "model_name": config.model_name,
            "model_key": config.model_key,
            "price": config.price,
            "size": config.size,
            "aspect_ratio": config.aspect_ratio,
            "resolution": config.resolution,
            "language": language,
            "reference_urls": config.reference_urls or [],
            "reference_file_ids": config.reference_file_ids or [],
            "prompt_message_id": data.get("prompt_message_id"),
        },
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
    except ProviderUnavailableError:
        await call.message.edit_text(_(TranslationKey.GEN_PROVIDER_UNAVAILABLE, None))
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
    await state.clear()


@router.callback_query(F.data == GenerationCallback.RETRY)
async def retry_generation(
    call: CallbackQuery,
    language: str,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Retry last generation request."""
    await call.answer()
    last = await GenerationService.get_last_request(call.from_user.id)
    prompt = last.get("prompt")
    model_id = last.get("model_id")
    if not prompt or not model_id:
        await call.message.answer(_(TranslationKey.GEN_PROMPT_NOT_FOUND, None))
        return

    model_name = last.get("model_name") or "-"
    model_key = last.get("model_key") or ""
    price = int(last.get("price") or 0)

    config = GenerationConfig(
        prompt=str(prompt),
        model_id=int(model_id),
        model_name=str(model_name),
        model_key=str(model_key),
        price=price,
        size=last.get("size"),
        aspect_ratio=last.get("aspect_ratio"),
        resolution=last.get("resolution"),
        language=str(last.get("language") or language),
        reference_urls=list(last.get("reference_urls") or []),
        reference_file_ids=list(last.get("reference_file_ids") or []),
        chat_id=call.message.chat.id if call.message else None,
        message_id=call.message.message_id if call.message else None,
        prompt_message_id=last.get("prompt_message_id"),
    )

    try:
        await call.message.edit_text(_(TranslationKey.GEN_IN_QUEUE, None))
    except TelegramBadRequest:
        pass

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
    except ProviderUnavailableError:
        await call.message.edit_text(_(TranslationKey.GEN_PROVIDER_UNAVAILABLE, None))
        return
    except Exception as e:
        logger.error("Generation retry failed", error=str(e))
        await call.message.edit_text(_(TranslationKey.ERROR_GENERIC, None))
        return

    request = result.get("request", {})
    request_id = request.get("id")
    request_status = request.get("status")

    if not request_id:
        await call.message.answer(_(TranslationKey.ERROR_GENERIC, None))
        return

    return


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
    price = GenerationService.calculate_generation_price(
        data.get("model_key"),
        int(price or 0),
        size,
        resolution,
    )
    
    show_size = data.get("supports_size") and bool(data.get("size_options"))
    show_aspect = data.get("supports_aspect_ratio") and bool(data.get("aspect_ratio_options"))
    show_resolution = data.get("supports_resolution") and bool(data.get("resolution_options"))
    
    has_reference = bool(data.get("reference_urls"))
    text = build_generation_text(
        prompt, model_name, size, aspect_ratio, resolution,
        show_size, show_aspect, show_resolution, has_reference, _,
    )
    
    try:
        await call.message.edit_text(
            text,
            reply_markup=GenerationKeyboard.main(
                _,
                model_name,
                size,
                aspect_ratio,
                resolution,
                int(price),
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest:
        pass
