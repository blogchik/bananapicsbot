"""Image tools callback handlers."""

import os
from typing import Callable

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, URLInputFile
from core.container import get_container
from core.exceptions import APIError
from core.logging import get_logger
from locales import TranslationKey
from services import GenerationService

logger = get_logger(__name__)
router = Router(name="image_tools_callbacks")


async def _process_tool(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
    tool_name: str,
    processing_key: TranslationKey,
    success_key: TranslationKey,
    api_method: str,
) -> None:
    """Generic tool processing handler."""
    await call.answer()
    if not call.message or not call.from_user:
        return

    try:
        message_id = int(call.data.split(":", 2)[2])
    except (IndexError, ValueError):
        return

    stored = await state.get_data()
    targets = stored.get("watermark_targets") or {}
    target = targets.get(str(message_id))
    if not isinstance(target, dict):
        await call.message.answer(_(TranslationKey.TOOL_FAILED, None))
        return

    file_id = target.get("file_id")
    filename = target.get("filename") or ""
    if not file_id:
        await call.message.answer(_(TranslationKey.TOOL_FAILED, None))
        return

    try:
        await call.message.edit_text(_(processing_key, None))
    except TelegramBadRequest:
        pass

    try:
        file = await call.bot.get_file(file_id)
        file_bytes = await call.bot.download_file(file.file_path)
        content = file_bytes.read()
        if not filename:
            filename = os.path.basename(file.file_path or "")
        if not filename:
            filename = "image.jpg"
        name_root, ext = os.path.splitext(filename)
        if not ext:
            filename = f"{filename}.jpg"
        image_url = await GenerationService.upload_media(content, filename)
        container = get_container()
        api = container.api_client
        # Call the appropriate API method
        method = getattr(api, api_method)
        result = await method(call.from_user.id, image_url)
        output_url = result.get("output_url")
        cost = int(result.get("cost") or 0)
        if not output_url:
            raise RuntimeError("Missing output url")
    except APIError as exc:
        if exc.status == 402:
            await call.message.answer(_(TranslationKey.INSUFFICIENT_BALANCE, None))
            return
        logger.warning(f"{tool_name} failed", error=str(exc))
        await call.message.answer(_(TranslationKey.TOOL_FAILED, None))
        return
    except Exception as exc:
        logger.warning(f"{tool_name} failed", error=str(exc))
        await call.message.answer(_(TranslationKey.TOOL_FAILED, None))
        return

    try:
        await call.message.delete()
    except TelegramBadRequest:
        pass

    targets.pop(str(message_id), None)
    await state.update_data(watermark_targets=targets)

    await call.message.bot.send_document(
        chat_id=call.message.chat.id,
        document=URLInputFile(output_url, filename=f"{name_root}_{tool_name}.png"),
        caption=_(success_key, {"cost": cost}),
        reply_to_message_id=message_id,
    )


@router.callback_query(F.data.startswith("tool:upscale:"))
async def upscale_image(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Upscale image to 4K resolution."""
    await _process_tool(
        call=call,
        state=state,
        _=_,
        tool_name="upscale",
        processing_key=TranslationKey.TOOL_UPSCALE_PROCESSING,
        success_key=TranslationKey.TOOL_UPSCALE_SUCCESS,
        api_method="upscale_image",
    )


@router.callback_query(F.data.startswith("tool:denoise:"))
async def denoise_image(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Remove noise from image."""
    await _process_tool(
        call=call,
        state=state,
        _=_,
        tool_name="denoise",
        processing_key=TranslationKey.TOOL_DENOISE_PROCESSING,
        success_key=TranslationKey.TOOL_DENOISE_SUCCESS,
        api_method="denoise_image",
    )


@router.callback_query(F.data.startswith("tool:restore:"))
async def restore_image(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Restore old photo by removing dust and scratches."""
    await _process_tool(
        call=call,
        state=state,
        _=_,
        tool_name="restore",
        processing_key=TranslationKey.TOOL_RESTORE_PROCESSING,
        success_key=TranslationKey.TOOL_RESTORE_SUCCESS,
        api_method="restore_image",
    )


@router.callback_query(F.data.startswith("tool:enhance:"))
async def enhance_image(
    call: CallbackQuery,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Enhance image with AI upscaling and sharpening."""
    await _process_tool(
        call=call,
        state=state,
        _=_,
        tool_name="enhance",
        processing_key=TranslationKey.TOOL_ENHANCE_PROCESSING,
        success_key=TranslationKey.TOOL_ENHANCE_SUCCESS,
        api_method="enhance_image",
    )
