"""Media (photo/document) message handler."""

import asyncio
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from typing import Callable

from locales import TranslationKey
from services import GenerationService
from core.constants import BotConstants
from core.logging import get_logger

logger = get_logger(__name__)
router = Router(name="media")

# User locks for reference processing
USER_REFERENCE_LOCKS: dict[int, asyncio.Lock] = {}

# Media group buffers
MEDIA_GROUP_BUFFERS: dict[tuple[int, str], dict] = {}


def is_image_document(message: Message) -> bool:
    """Check if document is an image."""
    document = message.document
    if not document:
        return False
    
    if document.mime_type and document.mime_type.startswith("image/"):
        return True
    
    filename = (document.file_name or "").lower()
    return filename.endswith(BotConstants.ALLOWED_IMAGE_EXTENSIONS)


async def process_reference_batch(
    message: Message,
    state: FSMContext,
    files: list[tuple[str, str | None]],
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Process batch of reference images."""
    user = message.from_user
    if not user:
        return
    
    lock = USER_REFERENCE_LOCKS.setdefault(user.id, asyncio.Lock())
    
    async with lock:
        # Check reference limit
        data = await state.get_data()
        references = list(data.get("reference_urls", []))
        reference_file_ids = list(data.get("reference_file_ids", []))
        
        if len(references) + len(files) > BotConstants.MAX_REFERENCE_IMAGES:
            await message.answer(
                _(TranslationKey.GEN_MAX_REFERENCES, {"max": BotConstants.MAX_REFERENCE_IMAGES})
            )
            return
        
        # Upload files
        new_urls: list[str] = []
        new_file_ids: list[str] = []
        
        for file_id, filename in files:
            file = await message.bot.get_file(file_id)
            file_bytes = await message.bot.download_file(file.file_path)
            content = file_bytes.read()
            safe_name = filename or file.file_path.split("/")[-1]
            
            try:
                download_url = await GenerationService.upload_media(content, safe_name)
            except Exception as e:
                logger.warning("Failed to upload media", error=str(e))
                download_url = ""
            
            if not download_url:
                await message.answer(_(TranslationKey.GEN_UPLOAD_ERROR, None))
                return
            
            new_urls.append(download_url)
            new_file_ids.append(file_id)
        
        references.extend(new_urls)
        reference_file_ids.extend(new_file_ids)
        
        await state.update_data(
            reference_urls=references,
            reference_file_ids=reference_file_ids,
        )
    
    # Process as prompt with references
    from .prompt import handle_prompt_message
    await handle_prompt_message(message, state, _)


async def queue_media_group_item(
    message: Message,
    state: FSMContext,
    file_id: str,
    filename: str | None,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Queue media group item for batch processing."""
    media_group_id = message.media_group_id
    if not media_group_id:
        return
    
    key = (message.chat.id, str(media_group_id))
    entry = MEDIA_GROUP_BUFFERS.get(key)
    
    if not entry:
        entry = {
            "files": [],
            "prompt_message": None,
            "state": state,
            "last_message": message,
            "translator": _,
            "task": None,
        }
        MEDIA_GROUP_BUFFERS[key] = entry
    
    files = entry["files"]
    if isinstance(files, list):
        files.append((file_id, filename))
    
    if message.caption:
        entry["prompt_message"] = message
    
    entry["last_message"] = message
    
    # Cancel previous task and create new one
    task = entry.get("task")
    if isinstance(task, asyncio.Task) and not task.done():
        task.cancel()
    
    entry["task"] = asyncio.create_task(process_media_group(key))


async def process_media_group(key: tuple[int, str]) -> None:
    """Process media group after delay."""
    await asyncio.sleep(BotConstants.MEDIA_GROUP_DELAY_SECONDS)
    
    entry = MEDIA_GROUP_BUFFERS.pop(key, None)
    if not entry:
        return
    
    prompt_message = entry.get("prompt_message")
    last_message = entry.get("last_message")
    state = entry.get("state")
    files = entry.get("files")
    translator = entry.get("translator")
    
    if not isinstance(prompt_message, Message) or not isinstance(state, FSMContext):
        if isinstance(last_message, Message) and translator:
            await last_message.answer(
                translator(TranslationKey.GEN_PROMPT_WITH_IMAGE, None),
                reply_to_message_id=last_message.message_id,
            )
        return
    
    if not isinstance(files, list) or not files:
        if translator:
            await prompt_message.answer(
                translator(TranslationKey.GEN_UPLOAD_ERROR, None),
                reply_to_message_id=prompt_message.message_id,
            )
        return
    
    await process_reference_batch(prompt_message, state, files, translator)


@router.message(F.photo)
async def handle_reference_photo(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle photo as reference image."""
    photo = message.photo[-1]
    
    if message.media_group_id:
        await queue_media_group_item(message, state, photo.file_id, None, _)
        return
    
    if not message.caption:
        await message.answer(
            _(TranslationKey.GEN_PROMPT_WITH_IMAGE, None),
            reply_to_message_id=message.message_id,
        )
        return
    
    await process_reference_batch(message, state, [(photo.file_id, None)], _)


@router.message(F.document)
async def handle_reference_document(
    message: Message,
    state: FSMContext,
    _: Callable[[TranslationKey, dict | None], str],
) -> None:
    """Handle document as reference image."""
    document = message.document
    if not document:
        return
    
    if not is_image_document(message):
        await message.answer(
            "Faqat rasm fayl yuboring.",
            reply_to_message_id=message.message_id,
        )
        return
    
    if message.media_group_id:
        await queue_media_group_item(message, state, document.file_id, document.file_name, _)
        return
    
    if not message.caption:
        await message.answer(
            _(TranslationKey.GEN_PROMPT_WITH_IMAGE, None),
            reply_to_message_id=message.message_id,
        )
        return
    
    await process_reference_batch(
        message,
        state,
        [(document.file_id, document.file_name)],
        _,
    )
