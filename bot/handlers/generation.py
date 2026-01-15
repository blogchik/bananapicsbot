import asyncio
from datetime import datetime
import html
import re
from urllib.parse import unquote, urlparse
from typing import Awaitable, Callable

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, URLInputFile

from api_client import ApiClient, ApiError
from config import load_settings
from keyboards import (
    aspect_ratio_menu,
    generation_menu,
    model_menu,
    profile_menu,
    resolution_menu,
    size_menu,
)
from locales.base import TranslationKey
from locales.manager import LocalizationFunction

router = Router()

ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
USER_REFERENCE_LOCKS: dict[int, asyncio.Lock] = {}
MEDIA_GROUP_DELAY_SECONDS = 1.0
MEDIA_GROUP_BUFFERS: dict[tuple[int, str], dict[str, object]] = {}

POLL_INTERVAL_SECONDS = 2
MAX_POLL_DURATION_SECONDS = 300  # 5 minutes max polling
SEND_RETRY_ATTEMPTS = 3
SEND_RETRY_DELAY_SECONDS = 1.5
MAX_DOCUMENT_CAPTION_LEN = 1024

QUEUE_STATUSES = {"pending", "configuring", "queued", "created"}


def format_status_label(status: str | None, _: LocalizationFunction) -> str:
    if not status:
        return _(TranslationKey.GEN_STATUS_LABEL_PROCESSING)
    normalized = status.lower()
    if normalized in QUEUE_STATUSES:
        return _(TranslationKey.GEN_STATUS_LABEL_QUEUE)
    return _(TranslationKey.GEN_STATUS_LABEL_PROCESSING)


async def retry_send(
    action: Callable[[], Awaitable[None]],
    attempts: int = SEND_RETRY_ATTEMPTS,
    delay_seconds: float = SEND_RETRY_DELAY_SECONDS,
) -> bool:
    for attempt in range(attempts):
        try:
            await action()
            return True
        except Exception:
            if attempt == attempts - 1:
                return False
            await asyncio.sleep(delay_seconds * (attempt + 1))
    return False


def format_model_hashtag(model_name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", model_name.title())
    if not cleaned:
        return "#Model"
    return f"#{cleaned}"


def build_escaped_prompt(prompt: str, max_len: int) -> str:
    if max_len <= 0:
        return ""
    ellipsis = "..."
    truncated = False
    target_len = max_len
    if max_len > len(ellipsis):
        target_len = max_len - len(ellipsis)
    chunks: list[str] = []
    current_len = 0
    for ch in prompt:
        escaped = html.escape(ch)
        if current_len + len(escaped) > target_len:
            truncated = True
            break
        chunks.append(escaped)
        current_len += len(escaped)
    result = "".join(chunks)
    if truncated and max_len > len(ellipsis):
        return result + ellipsis
    return result


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_duration_seconds(started_at: str | None, completed_at: str | None, created_at: str | None) -> int | None:
    start_time = parse_datetime(started_at) or parse_datetime(created_at)
    end_time = parse_datetime(completed_at)
    if not start_time or not end_time:
        return None
    delta = end_time - start_time
    seconds = int(delta.total_seconds())
    return seconds if seconds >= 0 else None


def build_result_caption(
    prompt: str,
    model_name: str,
    cost: int | None,
    duration_seconds: int | None,
    _: LocalizationFunction,
) -> str:
    hashtag = format_model_hashtag(model_name)
    credits = cost if cost is not None else 0
    duration_text = f"{duration_seconds}s" if duration_seconds is not None else "-"
    result_text = _(TranslationKey.GEN_RESULT_CAPTION).format(
        model=hashtag,
        credits=credits,
        duration=duration_text,
        prompt="{PROMPT_PLACEHOLDER}"
    )
    prefix = result_text.split("{PROMPT_PLACEHOLDER}")[0]
    suffix = result_text.split("{PROMPT_PLACEHOLDER}")[1] if "{PROMPT_PLACEHOLDER}" in result_text else ""
    max_prompt_len = MAX_DOCUMENT_CAPTION_LEN - len(prefix) - len(suffix)
    escaped_prompt = build_escaped_prompt(prompt, max_prompt_len)
    return result_text.replace("{PROMPT_PLACEHOLDER}", escaped_prompt)


def extract_filename_from_url(url: str) -> str:
    path = urlparse(url).path
    name = unquote(path.rsplit("/", 1)[-1]) if path else ""
    return name or "result"


def get_support_flags(
    supports_size: bool | None,
    supports_aspect_ratio: bool | None,
    supports_resolution: bool | None,
    size_options: list[str] | None,
    aspect_ratio_options: list[str] | None,
    resolution_options: list[str] | None,
) -> tuple[bool, bool, bool]:
    show_size = bool(supports_size and size_options)
    show_aspect = bool(supports_aspect_ratio and aspect_ratio_options)
    show_resolution = bool(supports_resolution and resolution_options)
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
) -> str:
    size_label = size if size else "Default"
    aspect_label = aspect_ratio if aspect_ratio else "Default"
    resolution_label = resolution if resolution else "Default"

    lines = [
        "⚙️ Generatsiya sozlamalari",
        f"Prompt: {prompt}",
        f"Model: {model_name}",
    ]
    if show_size:
        lines.append(f"Size: {size_label}")
    if show_aspect:
        lines.append(f"Aspect ratio: {aspect_label}")
    if show_resolution:
        lines.append(f"Resolution: {resolution_label}")
    return "\n".join(lines)


def normalize_models(models: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for item in models:
        model = item.get("model") or {}
        model_id = model.get("id")
        if not model_id:
            continue
        prices = item.get("prices") or []
        price = int(prices[0].get("unit_price", 0)) if prices else 0
        options = model.get("options") or {}
        size_options = list(options.get("size_options") or [])
        aspect_ratio_options = list(options.get("aspect_ratio_options") or [])
        resolution_options = list(options.get("resolution_options") or [])
        supports_size = bool(options.get("supports_size")) or bool(size_options)
        supports_aspect_ratio = bool(options.get("supports_aspect_ratio")) or bool(
            aspect_ratio_options
        )
        supports_resolution = bool(options.get("supports_resolution")) or bool(
            resolution_options
        )
        normalized.append(
            {
                "id": int(model_id),
                "key": model.get("key"),
                "name": model.get("name") or model.get("key") or str(model_id),
                "price": price,
                "supports_size": supports_size,
                "supports_aspect_ratio": supports_aspect_ratio,
                "supports_resolution": supports_resolution,
                "size_options": size_options,
                "aspect_ratio_options": aspect_ratio_options,
                "resolution_options": resolution_options,
            }
        )
    return normalized


def find_model(models: list[dict], model_id: int) -> dict | None:
    for model in models:
        if int(model["id"]) == model_id:
            return model
    return None


async def fetch_models(client: ApiClient) -> list[dict]:
    return normalize_models(await client.get_models())


async def has_active_generation(client: ApiClient, telegram_id: int) -> bool:
    try:
        data = await client.get_active_generation(telegram_id)
    except Exception:
        return False
    return bool(data.get("has_active"))


async def get_models_from_state(state: FSMContext, client: ApiClient) -> list[dict]:
    data = await state.get_data()
    models = data.get("models")
    if models:
        return models
    models = normalize_models(await client.get_models())
    await state.update_data(models=models)
    return models


def is_image_document(message: Message) -> bool:
    document = message.document
    if not document:
        return False
    if document.mime_type and document.mime_type.startswith("image/"):
        return True
    filename = (document.file_name or "").lower()
    return filename.endswith(ALLOWED_IMAGE_EXTENSIONS)


async def process_reference_batch(
    message: Message,
    state: FSMContext,
    files: list[tuple[str, str | None]],
) -> None:
    user = message.from_user
    if not user:
        return

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)

    lock = USER_REFERENCE_LOCKS.setdefault(user.id, asyncio.Lock())
    async with lock:
        if await has_active_generation(client, user.id):
            await message.answer(
                "Sizda hozir aktiv generatsiya bor. Iltimos, tugashini kuting va keyinroq urinib ko'ring."
            )
            return

        data = await state.get_data()
        references = list(data.get("reference_urls", []))
        reference_file_ids = list(data.get("reference_file_ids", []))
        if len(references) + len(files) > 10:
            await message.answer(_(TranslationKey.GEN_MAX_REFERENCES))
            return

        new_urls: list[str] = []
        new_file_ids: list[str] = []
        for file_id, filename in files:
            file = await message.bot.get_file(file_id)
            file_bytes = await message.bot.download_file(file.file_path)
            content = file_bytes.read()
            safe_name = filename or file.file_path.split("/")[-1]

            try:
                download_url = await client.upload_media(content, safe_name)
            except Exception:
                download_url = ""
            if not download_url:
                await message.answer(_(TranslationKey.GEN_UPLOAD_ERROR))
                return

            new_urls.append(download_url)
            new_file_ids.append(file_id)

        references.extend(new_urls)
        reference_file_ids.extend(new_file_ids)
        await state.update_data(
            reference_urls=references,
            reference_file_ids=reference_file_ids,
        )

    await handle_prompt_message(message, state)


async def queue_media_group_item(
    message: Message,
    state: FSMContext,
    file_id: str,
    filename: str | None,
) -> None:
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
            "task": None,
        }
        MEDIA_GROUP_BUFFERS[key] = entry

    files = entry["files"]
    if isinstance(files, list):
        files.append((file_id, filename))
    if message.caption:
        entry["prompt_message"] = message
    entry["last_message"] = message

    task = entry.get("task")
    if isinstance(task, asyncio.Task) and not task.done():
        task.cancel()
    entry["task"] = asyncio.create_task(process_media_group(key))


async def process_media_group(key: tuple[int, str]) -> None:
    await asyncio.sleep(MEDIA_GROUP_DELAY_SECONDS)
    entry = MEDIA_GROUP_BUFFERS.pop(key, None)
    if not entry:
        return

    prompt_message = entry.get("prompt_message")
    last_message = entry.get("last_message")
    state = entry.get("state")
    files = entry.get("files")

    if not isinstance(prompt_message, Message) or not isinstance(state, FSMContext):
        if isinstance(last_message, Message):
            await last_message.answer(
                "Rasmni prompt bilan yuboring.",
                reply_to_message_id=last_message.message_id,
            )
        return

    if not isinstance(files, list) or not files:
        await prompt_message.answer(
            "Rasm topilmadi. Qaytadan yuboring.",
            reply_to_message_id=prompt_message.message_id,
        )
        return

    await process_reference_batch(prompt_message, state, files)


@router.message(F.photo)
async def handle_reference_photo(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1]
    if message.media_group_id:
        await queue_media_group_item(message, state, photo.file_id, None)
        return
    if not message.caption:
        await message.answer(
            "Rasmni prompt bilan yuboring.",
            reply_to_message_id=message.message_id,
        )
        return
    await process_reference_batch(message, state, [(photo.file_id, None)])


@router.message(F.document)
async def handle_reference_document(message: Message, state: FSMContext) -> None:
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
        await queue_media_group_item(message, state, document.file_id, document.file_name)
        return
    if not message.caption:
        await message.answer(
            "Rasmni prompt bilan yuboring.",
            reply_to_message_id=message.message_id,
        )
        return
    await process_reference_batch(
        message,
        state,
        [(document.file_id, document.file_name)],
    )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_prompt_message(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return

    prompt = message.caption or message.text or ""
    prompt = prompt.strip()
    if not prompt:
        await message.answer(_(TranslationKey.GEN_PROMPT_REQUIRED))
        return

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)

    if await has_active_generation(client, user.id):
        await message.answer(
            "Sizda hozir aktiv generatsiya bor. Iltimos, tugashini kuting va keyinroq urinib ko'ring."
        )
        return

    try:
        models = await fetch_models(client)
    except Exception:
        await message.answer(_(TranslationKey.GEN_MODEL_FETCH_ERROR))
        return

    if not models:
        await message.answer(_(TranslationKey.GEN_MODEL_NOT_FOUND_ERROR))
        return

    selected_model = models[0]

    data = await state.get_data()
    previous_menu_id = data.get("menu_message_id")
    if previous_menu_id:
        try:
            await message.bot.delete_message(message.chat.id, previous_menu_id)
        except TelegramBadRequest as exc:
            if "message to delete not found" not in str(exc):
                raise

    supports_size = selected_model.get("supports_size")
    supports_aspect_ratio = selected_model.get("supports_aspect_ratio")
    supports_resolution = selected_model.get("supports_resolution")
    size_options = selected_model.get("size_options") or []
    aspect_ratio_options = selected_model.get("aspect_ratio_options") or []
    resolution_options = selected_model.get("resolution_options") or []

    await state.update_data(
        prompt=prompt,
        model_id=selected_model["id"],
        model_name=selected_model["name"],
        model_key=selected_model.get("key"),
        prompt_message_id=message.message_id,
        price=selected_model["price"],
        size=None,
        aspect_ratio=None,
        resolution=None,
        supports_size=supports_size,
        supports_aspect_ratio=supports_aspect_ratio,
        supports_resolution=supports_resolution,
        size_options=size_options,
        aspect_ratio_options=aspect_ratio_options,
        resolution_options=resolution_options,
        models=models,
    )

    show_size, show_aspect, show_resolution = get_support_flags(
        supports_size,
        supports_aspect_ratio,
        supports_resolution,
        size_options,
        aspect_ratio_options,
        resolution_options,
    )
    menu_text = build_generation_text(
        prompt,
        selected_model["name"],
        None,
        None,
        None,
        show_size,
        show_aspect,
        show_resolution,
    )
    menu = generation_menu(
        selected_model["name"],
        None,
        None,
        None,
        selected_model["price"],
        show_size,
        show_aspect,
        show_resolution,
    )
    msg = await message.answer(
        menu_text,
        reply_markup=menu,
        reply_to_message_id=message.message_id,
    )
    await state.update_data(menu_message_id=msg.message_id)


@router.callback_query(F.data == "gen:model:menu")
async def open_model_menu(call: CallbackQuery, state: FSMContext, _) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer(_(TranslationKey.GEN_PROMPT_NOT_FOUND))
        return

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    try:
        models = await get_models_from_state(state, client)
    except Exception:
        await call.message.answer("Model ma'lumotini olishda xatolik.")
        return

    model_id = int(data.get("model_id", 0)) if data.get("model_id") else None
    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )

    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(text, reply_markup=model_menu(models, model_id))
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data.startswith("gen:model:set:"))
async def select_model(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer(_(TranslationKey.GEN_PROMPT_NOT_FOUND))
        return

    try:
        model_id = int(call.data.split(":", 3)[3])
    except (IndexError, ValueError):
        return

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    try:
        models = await get_models_from_state(state, client)
    except Exception:
        await call.message.answer(_(TranslationKey.GEN_MODEL_FETCH_ERROR))
        return

    selected = find_model(models, model_id)
    if not selected:
        await call.message.answer(_(TranslationKey.GEN_MODEL_NOT_FOUND_ERROR))
        return

    supports_size = selected.get("supports_size")
    supports_aspect_ratio = selected.get("supports_aspect_ratio")
    supports_resolution = selected.get("supports_resolution")
    size_options = selected.get("size_options") or []
    aspect_ratio_options = selected.get("aspect_ratio_options") or []
    resolution_options = selected.get("resolution_options") or []

    show_size, show_aspect, show_resolution = get_support_flags(
        supports_size,
        supports_aspect_ratio,
        supports_resolution,
        size_options,
        aspect_ratio_options,
        resolution_options,
    )

    size = data.get("size") if show_size else None
    aspect_ratio = data.get("aspect_ratio") if show_aspect else None
    resolution = data.get("resolution") if show_resolution else None

    await state.update_data(
        model_id=selected["id"],
        model_name=selected["name"],
        model_key=selected.get("key"),
        price=selected["price"],
        size=size,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        supports_size=supports_size,
        supports_aspect_ratio=supports_aspect_ratio,
        supports_resolution=supports_resolution,
        size_options=size_options,
        aspect_ratio_options=aspect_ratio_options,
        resolution_options=resolution_options,
    )

    text = build_generation_text(
        prompt,
        selected["name"],
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=generation_menu(
                selected["name"],
                size,
                aspect_ratio,
                resolution,
                selected["price"],
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data == "gen:size:menu")
async def open_size_menu(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    supports_size = data.get("supports_size")
    size_options = data.get("size_options") or []
    show_size, show_aspect, show_resolution = get_support_flags(
        supports_size,
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        size_options,
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )
    if not show_size:
        await call.answer(_(TranslationKey.GEN_SIZE_NOT_AVAILABLE), show_alert=True)
        return

    await call.answer()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer(_(TranslationKey.GEN_PROMPT_NOT_FOUND))
        return

    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")

    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(text, reply_markup=size_menu(size_options, size))
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data.startswith("gen:size:set:"))
async def select_size(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    size_value = call.data.split(":", 3)[3]
    size = None if size_value == "default" else size_value

    model_name = data.get("model_name", "-")
    price = int(data.get("price", 0))
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )

    await state.update_data(size=size)
    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=generation_menu(
                model_name,
                size,
                aspect_ratio,
                resolution,
                price,
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data == "gen:ratio:menu")
async def open_ratio_menu(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    aspect_ratio_options = data.get("aspect_ratio_options") or []
    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        aspect_ratio_options,
        data.get("resolution_options"),
    )
    if not show_aspect:
        await call.answer(_(TranslationKey.GEN_ASPECT_NOT_AVAILABLE), show_alert=True)
        return

    await call.answer()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer(_(TranslationKey.GEN_PROMPT_NOT_FOUND))
        return

    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")

    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=aspect_ratio_menu(aspect_ratio_options, aspect_ratio),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data.startswith("gen:ratio:set:"))
async def select_ratio(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    ratio_value = call.data.split(":", 3)[3]
    aspect_ratio = None if ratio_value == "default" else ratio_value

    model_name = data.get("model_name", "-")
    price = int(data.get("price", 0))
    size = data.get("size")
    resolution = data.get("resolution")

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )

    await state.update_data(aspect_ratio=aspect_ratio)
    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=generation_menu(
                model_name,
                size,
                aspect_ratio,
                resolution,
                price,
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data == "gen:resolution:menu")
async def open_resolution_menu(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    resolution_options = data.get("resolution_options") or []
    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        resolution_options,
    )
    if not show_resolution:
        await call.answer("Bu modelda resolution mavjud emas.", show_alert=True)
        return

    await call.answer()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")

    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=resolution_menu(resolution_options, resolution),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data.startswith("gen:resolution:set:"))
async def select_resolution(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    resolution_value = call.data.split(":", 3)[3]
    resolution = None if resolution_value == "default" else resolution_value

    model_name = data.get("model_name", "-")
    price = int(data.get("price", 0))
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )

    await state.update_data(resolution=resolution)
    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=generation_menu(
                model_name,
                size,
                aspect_ratio,
                resolution,
                price,
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


@router.callback_query(F.data == "gen:back")
async def back_to_generation(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    if not prompt:
        await call.message.answer("Prompt topilmadi. Iltimos, qaytadan yuboring.")
        return

    model_name = data.get("model_name", "-")
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")
    price = int(data.get("price", 0))

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )

    text = build_generation_text(
        prompt,
        model_name,
        size,
        aspect_ratio,
        resolution,
        show_size,
        show_aspect,
        show_resolution,
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=generation_menu(
                model_name,
                size,
                aspect_ratio,
                resolution,
                price,
                show_size,
                show_aspect,
                show_resolution,
            ),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


async def send_outputs(
    bot,
    chat_id: int,
    outputs: list[str],
    reply_to_message_id: int | None,
    caption_text: str,
    _: LocalizationFunction,
) -> None:
    caption_pending = True
    document_failed = False
    for url in outputs:
        sent_photo = await retry_send(
            lambda: bot.send_photo(
                chat_id, url, reply_to_message_id=reply_to_message_id
            )
        )
        caption_value = caption_text if caption_pending else None
        filename = extract_filename_from_url(url)
        sent_document = await retry_send(
            lambda: bot.send_document(
                chat_id,
                URLInputFile(url, filename=filename),
                reply_to_message_id=reply_to_message_id,
                caption=caption_value,
                parse_mode="HTML",
            )
        )
        if not sent_document:
            document_failed = True
        if sent_document and caption_pending:
            caption_pending = False
        if not sent_photo and not sent_document:
            await retry_send(
                lambda: bot.send_message(
                    chat_id, url, reply_to_message_id=reply_to_message_id
                )
            )
    if document_failed:
        await retry_send(
            lambda: bot.send_message(
                chat_id,
                _(TranslationKey.GEN_SEND_ERROR),
                reply_to_message_id=reply_to_message_id,
            )
        )


async def poll_generation_status(
    bot,
    client: ApiClient,
    chat_id: int,
    message_id: int,
    request_id: int,
    telegram_id: int,
    prompt: str,
    model_name: str,
    prompt_message_id: int | None,
    _: LocalizationFunction,
) -> None:
    last_label = None
    consecutive_errors = 0
    import time
    start_time = time.time()
    
    while True:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > MAX_POLL_DURATION_SECONDS:
            try:
                await bot.edit_message_text(
                    _(TranslationKey.GEN_TIMEOUT),
                    chat_id=chat_id,
                    message_id=message_id,
                )
            except TelegramBadRequest:
                pass
            return
        
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        try:
            result = await client.refresh_generation(request_id, telegram_id)
        except ApiError as exc:
            consecutive_errors += 1
            if consecutive_errors in {3, 6, 10}:
                detail = exc.data.get("detail") if isinstance(exc.data, dict) else None
                if isinstance(detail, dict):
                    detail_value = detail.get("message") or str(detail)
                else:
                    detail_value = str(detail) if detail else ""
                detail_text = f" ({detail_value})" if detail_value else ""
                try:
                    await bot.edit_message_text(
                        f"{_(TranslationKey.GEN_STATUS_CHECK_ERROR)}"
                        f"{detail_text}",
                        chat_id=chat_id,
                        message_id=message_id,
                    )
                except TelegramBadRequest as error:
                    if "message is not modified" not in str(error):
                        raise
            continue
        except Exception:
            consecutive_errors += 1
            if consecutive_errors in {3, 6, 10}:
                try:
                    await bot.edit_message_text(
                        _(TranslationKey.GEN_STATUS_CHECK_TEMP_ERROR),
                        chat_id=chat_id,
                        message_id=message_id,
                    )
                except TelegramBadRequest as error:
                    if "message is not modified" not in str(error):
                        raise
            continue
        consecutive_errors = 0
        status = result.get("status")
        # Status updates removed to avoid unnecessary intermediate messages
        # User sees initial "queue" message, then directly gets the result
        if status == "completed":
            try:
                outputs = await client.get_generation_results(request_id, telegram_id)
            except Exception:
                outputs = []
            duration_seconds = format_duration_seconds(
                result.get("started_at"),
                result.get("completed_at"),
                result.get("created_at"),
            )
            caption_text = build_result_caption(
                prompt, model_name, result.get("cost"), duration_seconds, _
            )
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except TelegramBadRequest:
                pass
            if outputs:
                await send_outputs(
                    bot, chat_id, outputs, prompt_message_id, caption_text, _
                )
            return
        if status == "failed":
            try:
                error_message = result.get("error_message")
                text = _(TranslationKey.GEN_FAILED)
                if error_message:
                    text = _(TranslationKey.GEN_ERROR).format(error=error_message)
                await bot.edit_message_text(
                    text,
                    chat_id=chat_id,
                    message_id=message_id,
                )
            except TelegramBadRequest as exc:
                if "message is not modified" not in str(exc):
                    raise
            return


@router.callback_query(F.data == "gen:submit")
async def submit_generation(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    prompt = data.get("prompt")
    model_id = int(data.get("model_id", 0))
    model_name = data.get("model_name", "-")
    price = int(data.get("price", 0))
    size = data.get("size")
    aspect_ratio = data.get("aspect_ratio")
    resolution = data.get("resolution")
    references = list(data.get("reference_urls", []))
    reference_file_ids = list(data.get("reference_file_ids", []))
    prompt_message_id = data.get("prompt_message_id")
    if not prompt_message_id and call.message.reply_to_message:
        prompt_message_id = call.message.reply_to_message.message_id

    if not prompt or not model_id:
        await call.message.answer("Prompt yoki model topilmadi.")
        return

    show_size, show_aspect, show_resolution = get_support_flags(
        data.get("supports_size"),
        data.get("supports_aspect_ratio"),
        data.get("supports_resolution"),
        data.get("size_options"),
        data.get("aspect_ratio_options"),
        data.get("resolution_options"),
    )
    if not show_size:
        size = None
    if not show_aspect:
        aspect_ratio = None
    if not show_resolution:
        resolution = None

    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)

    try:
        await call.message.edit_text(_(TranslationKey.GEN_IN_QUEUE))
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise

    try:
        result = await client.submit_generation(
            telegram_id=call.from_user.id,
            model_id=model_id,
            prompt=prompt,
            size=size,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            reference_urls=references,
            reference_file_ids=reference_file_ids,
        )
    except ApiError as exc:
        if exc.status == 409:
            detail = exc.data.get("detail") if isinstance(exc.data, dict) else None
            active_id = None
            if isinstance(detail, dict):
                active_id = detail.get("active_request_id")
            suffix = f" (ID: {active_id})" if active_id else ""
            await call.message.edit_text(
                f"{_(TranslationKey.GEN_CONFLICT)}"
                f"{suffix}"
            )
            return
        if exc.status == 402:
            await call.message.edit_text(
                _(TranslationKey.GEN_INSUFFICIENT_BALANCE), reply_markup=profile_menu()
            )
            return
        detail = exc.data.get("detail") if isinstance(exc.data, dict) else None
        if detail:
            if isinstance(detail, dict):
                detail_text = detail.get("message") or str(detail)
            else:
                detail_text = str(detail)
            await call.message.edit_text(_(TranslationKey.GEN_ERROR).format(error=detail_text))
            return
        await call.message.edit_text(
            _(TranslationKey.GEN_ERROR_GENERIC)
        )
        return
    except Exception:
        await call.message.edit_text(
            _(TranslationKey.GEN_ERROR_GENERIC)
        )
        return

    request = result.get("request", {})
    request_id = request.get("id")
    request_status = request.get("status")

    if not request_id:
        await call.message.answer(_(TranslationKey.GEN_ERROR_GENERIC))
        await state.clear()
        return
    if request_status == "completed":
        try:
            outputs = await client.get_generation_results(request_id, call.from_user.id)
        except Exception:
            outputs = []
        duration_seconds = format_duration_seconds(
            request.get("started_at"),
            request.get("completed_at"),
            request.get("created_at"),
        )
        caption_text = build_result_caption(
            prompt, model_name, request.get("cost"), duration_seconds, _
        )
        try:
            await call.message.delete()
        except TelegramBadRequest:
            pass
        if outputs:
            await send_outputs(
                call.message.bot,
                call.message.chat.id,
                outputs,
                prompt_message_id or call.message.message_id,
                caption_text,
                _,
            )
        await state.clear()
        return
    try:
        asyncio.create_task(
            poll_generation_status(
                call.message.bot,
                client,
                call.message.chat.id,
                call.message.message_id,
                request_id,
                call.from_user.id,
                prompt,
                model_name,
                prompt_message_id or call.message.message_id,
                _,
            )
        )
    except Exception:
        pass
    await state.clear()
