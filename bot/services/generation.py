"""Generation service."""

import asyncio
import html
import json
import mimetypes
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from urllib.parse import unquote, urlparse

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, URLInputFile
from aiohttp import ClientSession, ClientTimeout
from core.constants import BotConstants
from core.container import get_container
from core.exceptions import (
    ActiveGenerationError,
    APIError,
    InsufficientBalanceError,
    ProviderUnavailableError,
)
from core.logging import get_logger
from keyboards import GenerationKeyboard
from locales import TranslationKey

logger = get_logger(__name__)


@dataclass
class NormalizedModel:
    """Normalized model data."""
    id: int
    key: str
    name: str
    price: int
    supports_size: bool
    supports_aspect_ratio: bool
    supports_resolution: bool
    supports_quality: bool
    supports_input_fidelity: bool
    quality_stars: int | None
    avg_duration_seconds_min: int | None
    avg_duration_seconds_max: int | None
    avg_duration_text: str | None
    size_options: list[str]
    aspect_ratio_options: list[str]
    resolution_options: list[str]
    quality_options: list[str]
    input_fidelity_options: list[str]


@dataclass
class GenerationConfig:
    """Generation configuration."""
    prompt: str
    model_id: int
    model_name: str
    model_key: str
    price: int
    size: str | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
    quality: str | None = None
    input_fidelity: str | None = None
    language: str | None = None
    reference_urls: list[str] | None = None
    reference_file_ids: list[str] | None = None
    chat_id: int | None = None
    message_id: int | None = None
    prompt_message_id: int | None = None


class GenerationService:
    """Generation-related business logic."""

    _DEFAULTS_KEY_PREFIX = "gen_defaults"
    _LAST_REQUEST_KEY_PREFIX = "gen_last_request"
    _LAST_REQUEST_TTL_SECONDS = 3600

    @staticmethod
    def calculate_generation_price(
        model_key: str | None,
        base_price: int,
        size: str | None,
        resolution: str | None,
        quality: str | None,
        is_image_to_image: bool = False,
    ) -> int:
        key = (model_key or "").strip().lower().replace("_", "-").replace(" ", "-")
        res = (resolution or "").strip().lower()
        if res in {"4k", "4096", "4096x4096", "4096*4096"}:
            res = "4k"
        if key == "seedream-v4":
            return 27
        if key == "nano-banana-pro":
            return 240 if res == "4k" else 140
        if key == "gpt-image-1.5":
            price = GenerationService._price_from_size(
                size or resolution,
                quality,
                is_image_to_image=is_image_to_image,
            )
            return price if price is not None else base_price
        return base_price

    @staticmethod
    def _price_from_size(
        size: str | None,
        quality: str | None,
        is_image_to_image: bool = False,
    ) -> int | None:
        if not size:
            size = "auto"
        normalized = size.lower().replace("x", "*")
        if normalized == "auto":
            normalized = "1024*1024"
        match = re.match(r"^(\\d{3,4})\\*(\\d{3,4})$", normalized)
        if not match:
            return None
        size_key = normalized
        quality_key = (quality or "medium").lower()
        t2i_prices = {
            "low": {
                "1024*1024": 9,
                "1024*1536": 13,
                "1536*1024": 13,
            },
            "medium": {
                "1024*1024": 34,
                "1024*1536": 51,
                "1536*1024": 51,
            },
            "high": {
                "1024*1024": 133,
                "1024*1536": 200,
                "1536*1024": 200,
            },
        }
        i2i_prices = {
            "low": {
                "1024*1024": 9,
                "1024*1536": 34,
                "1536*1024": 13,
            },
            "medium": {
                "1024*1024": 34,
                "1024*1536": 51,
                "1536*1024": 51,
            },
            "high": {
                "1024*1024": 133,
                "1024*1536": 200,
                "1536*1024": 200,
            },
        }
        prices = i2i_prices if is_image_to_image else t2i_prices
        bucket = prices.get(quality_key) or prices["medium"]
        return bucket.get(size_key) or bucket["1024*1024"]

    @staticmethod
    async def get_models() -> list[NormalizedModel]:
        """Get available models (normalized)."""
        container = get_container()
        cache_key = "models:active"
        raw_models: list[dict] | None = None
        try:
            cached = await container.redis_client.cache_get(cache_key)
            if cached:
                raw_models = json.loads(cached)
        except Exception:
            raw_models = None
        if raw_models is None:
            raw_models = await container.api_client.get_models()
            try:
                await container.redis_client.cache_set(
                    cache_key,
                    json.dumps(raw_models),
                    ttl_seconds=BotConstants.MODELS_CACHE_TTL_SECONDS,
                )
            except Exception:
                logger.warning("Failed to cache models")
        return GenerationService._normalize_models(raw_models)

    @staticmethod
    def _normalize_models(raw_models: list[dict]) -> list[NormalizedModel]:
        """Normalize model data from API."""
        normalized: list[NormalizedModel] = []

        for item in raw_models:
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
            quality_options = list(options.get("quality_options") or [])
            input_fidelity_options = list(options.get("input_fidelity_options") or [])
            quality_stars = options.get("quality_stars")
            avg_duration_seconds_min = options.get("avg_duration_seconds_min")
            avg_duration_seconds_max = options.get("avg_duration_seconds_max")
            avg_duration_text = options.get("avg_duration_text")

            supports_size = bool(options.get("supports_size")) or bool(size_options)
            supports_aspect_ratio = bool(options.get("supports_aspect_ratio")) or bool(aspect_ratio_options)
            supports_resolution = bool(options.get("supports_resolution")) or bool(resolution_options)
            supports_quality = bool(options.get("supports_quality")) or bool(quality_options)
            supports_input_fidelity = bool(options.get("supports_input_fidelity")) or bool(input_fidelity_options)

            key = str(model.get("key") or "").strip()
            name = model.get("name") or model.get("key") or str(model_id)
            if not key and name:
                key = (
                    str(name)
                    .strip()
                    .lower()
                    .replace("_", "-")
                    .replace(" ", "-")
                )

            normalized.append(NormalizedModel(
                id=int(model_id),
                key=key,
                name=name,
                price=price,
                supports_size=supports_size,
                supports_aspect_ratio=supports_aspect_ratio,
                supports_resolution=supports_resolution,
                supports_quality=supports_quality,
                supports_input_fidelity=supports_input_fidelity,
                quality_stars=int(quality_stars) if quality_stars is not None else None,
                avg_duration_seconds_min=(
                    int(avg_duration_seconds_min)
                    if avg_duration_seconds_min is not None
                    else None
                ),
                avg_duration_seconds_max=(
                    int(avg_duration_seconds_max)
                    if avg_duration_seconds_max is not None
                    else None
                ),
                avg_duration_text=str(avg_duration_text) if avg_duration_text else None,
                size_options=size_options,
                aspect_ratio_options=aspect_ratio_options,
                resolution_options=resolution_options,
                quality_options=quality_options,
                input_fidelity_options=input_fidelity_options,
            ))

        return normalized

    @staticmethod
    def find_model(models: list[NormalizedModel], model_id: int) -> NormalizedModel | None:
        """Find model by ID."""
        for model in models:
            if model.id == model_id:
                return model
        return None

    @staticmethod
    async def has_active_generation(telegram_id: int) -> bool:
        """Check if user has active generation."""
        try:
            container = get_container()
            data = await container.api_client.get_active_generation(telegram_id)
            return bool(data.get("has_active"))
        except Exception:
            return False

    @staticmethod
    async def get_generation_defaults(telegram_id: int) -> dict[str, object]:
        """Get last selected generation defaults for user."""
        container = get_container()
        key = f"{GenerationService._DEFAULTS_KEY_PREFIX}:{telegram_id}"
        try:
            data = await container.redis_client.hgetall(key)
        except Exception:
            return {}
        model_id_raw = data.get("model_id")
        try:
            model_id = int(model_id_raw) if model_id_raw else None
        except (TypeError, ValueError):
            model_id = None
        size = data.get("size") or None
        aspect_ratio = data.get("aspect_ratio") or None
        resolution = data.get("resolution") or None
        quality = data.get("quality") or None
        input_fidelity = data.get("input_fidelity") or None
        return {
            "model_id": model_id,
            "size": size,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "quality": quality,
            "input_fidelity": input_fidelity,
        }

    @staticmethod
    async def save_generation_defaults(
        telegram_id: int,
        model_id: int,
        size: str | None,
        aspect_ratio: str | None,
        resolution: str | None,
        quality: str | None,
        input_fidelity: str | None,
        store_resolution: bool = True,
    ) -> None:
        """Persist last selected generation defaults for user."""
        container = get_container()
        key = f"{GenerationService._DEFAULTS_KEY_PREFIX}:{telegram_id}"
        try:
            await container.redis_client.hset(key, "model_id", str(model_id))
            await container.redis_client.hset(key, "size", size or "")
            await container.redis_client.hset(key, "aspect_ratio", aspect_ratio or "")
            if store_resolution:
                await container.redis_client.hset(key, "resolution", resolution or "")
            await container.redis_client.hset(key, "quality", quality or "")
            await container.redis_client.hset(key, "input_fidelity", input_fidelity or "")
        except Exception:
            logger.warning("Failed to save generation defaults", user_id=telegram_id)

    @staticmethod
    async def save_last_request(
        telegram_id: int,
        payload: dict[str, object],
    ) -> None:
        """Persist last generation request payload for retry."""
        container = get_container()
        key = f"{GenerationService._LAST_REQUEST_KEY_PREFIX}:{telegram_id}"
        try:
            data = json.dumps(payload)
            await container.redis_client.set(
                key, data, expire_seconds=GenerationService._LAST_REQUEST_TTL_SECONDS
            )
        except Exception:
            logger.warning("Failed to save last generation request", user_id=telegram_id)

    @staticmethod
    async def get_last_request(telegram_id: int) -> dict[str, object]:
        """Get last generation request payload."""
        container = get_container()
        key = f"{GenerationService._LAST_REQUEST_KEY_PREFIX}:{telegram_id}"
        try:
            raw = await container.redis_client.get(key)
        except Exception:
            return {}
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    async def submit_generation(
        telegram_id: int,
        config: GenerationConfig,
    ) -> dict:
        """Submit generation request."""
        container = get_container()

        try:
            return await container.api_client.submit_generation(
                telegram_id=telegram_id,
                model_id=config.model_id,
                prompt=config.prompt,
                size=config.size,
                aspect_ratio=config.aspect_ratio,
                resolution=config.resolution,
                quality=config.quality,
                input_fidelity=config.input_fidelity,
                language=config.language,
                reference_urls=config.reference_urls or [],
                reference_file_ids=config.reference_file_ids or [],
                chat_id=config.chat_id,
                message_id=config.message_id,
                prompt_message_id=config.prompt_message_id,
            )
        except APIError as e:
            if e.status == 409:
                detail = e.data.get("detail") if isinstance(e.data, dict) else None
                active_id = detail.get("active_request_id") if isinstance(detail, dict) else None
                raise ActiveGenerationError(active_id)
            if e.status == 402:
                raise InsufficientBalanceError()
            if e.status in {401, 403, 502}:
                raise ProviderUnavailableError()
            if e.status == 503:
                detail = e.data.get("detail") if isinstance(e.data, dict) else None
                if isinstance(detail, dict):
                    code = detail.get("code")
                    if code == "provider_balance_low":
                        raise ProviderUnavailableError()
                if isinstance(e.data, dict):
                    error = e.data.get("error")
                    message = error.get("message") if isinstance(error, dict) else None
                    code = message.get("code") if isinstance(message, dict) else None
                    if code == "provider_balance_low":
                        raise ProviderUnavailableError()
            raise

    @staticmethod
    async def refresh_generation(request_id: int, telegram_id: int) -> dict:
        """Refresh generation status."""
        container = get_container()
        return await container.api_client.refresh_generation(request_id, telegram_id)

    @staticmethod
    async def get_results(request_id: int, telegram_id: int) -> list[str]:
        """Get generation results."""
        container = get_container()
        return await container.api_client.get_generation_results(request_id, telegram_id)

    @staticmethod
    async def upload_media(file_bytes: bytes, filename: str) -> str:
        """Upload media file."""
        container = get_container()
        return await container.api_client.upload_media(file_bytes, filename)

    @staticmethod
    def _get_status_message(
        status: str | None,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> str | None:
        """Get localized status message for queue/processing."""
        if not status:
            return None
        normalized = status.lower()
        if normalized in BotConstants.QUEUE_STATUSES:
            return _(TranslationKey.GEN_IN_QUEUE, None)
        if normalized == "running":
            return _(TranslationKey.GEN_PROCESSING, None)
        return None

    @staticmethod
    def format_model_hashtag(model_name: str) -> str:
        """Format model name as hashtag."""
        cleaned = re.sub(r"[^A-Za-z0-9]+", "", model_name.title())
        if not cleaned:
            return "#Model"
        return f"#{cleaned}"

    @staticmethod
    def build_result_caption(
        prompt: str,
        model_name: str,
        cost: int | None,
        duration_seconds: int | None,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> str:
        """Build result caption with prompt."""
        hashtag = GenerationService.format_model_hashtag(model_name)
        credits = cost if cost is not None else 0
        template = _(TranslationKey.GEN_RESULT_CAPTION, {
            "model": hashtag,
            "credits": credits,
            "prompt": "{PROMPT_PLACEHOLDER}",
        })
        return GenerationService._inject_prompt(template, prompt)

    @staticmethod
    def _build_escaped_prompt(prompt: str, max_len: int) -> str:
        """Build HTML-escaped prompt with length limit."""
        if max_len <= 0:
            return ""

        ellipsis = "..."
        truncated = False
        target_len = max_len - len(ellipsis) if max_len > len(ellipsis) else max_len

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

    @staticmethod
    def _inject_prompt(template: str, prompt: str) -> str:
        """Replace placeholder with escaped prompt respecting caption limits."""
        placeholder = "{PROMPT_PLACEHOLDER}"
        if placeholder not in template:
            return template
        prefix, suffix = template.split(placeholder, 1)
        max_prompt_len = max(
            0, BotConstants.MAX_CAPTION_LENGTH - len(prefix) - len(suffix)
        )
        escaped_prompt = GenerationService._build_escaped_prompt(prompt, max_prompt_len)
        return f"{prefix}{escaped_prompt}{suffix}"

    @staticmethod
    def parse_duration_seconds(
        started_at: str | None,
        completed_at: str | None,
        created_at: str | None,
    ) -> int | None:
        """Parse generation duration in seconds."""
        def parse_datetime(value: str | None) -> datetime | None:
            if not value:
                return None
            try:
                if value.endswith("Z"):
                    value = value[:-1] + "+00:00"
                return datetime.fromisoformat(value)
            except ValueError:
                return None

        start_time = parse_datetime(started_at) or parse_datetime(created_at)
        end_time = parse_datetime(completed_at)

        if not start_time or not end_time:
            return None

        delta = end_time - start_time
        seconds = int(delta.total_seconds())
        return seconds if seconds >= 0 else None

    @staticmethod
    def extract_filename_from_url(url: str) -> str:
        """Extract filename from URL."""
        path = urlparse(url).path
        name = unquote(path.rsplit("/", 1)[-1]) if path else ""
        return name or "result"

    @staticmethod
    def _extract_filename_from_disposition(value: str | None) -> str | None:
        if not value:
            return None
        match = re.search(r"filename\\*?=([^;]+)", value, flags=re.IGNORECASE)
        if not match:
            return None
        filename = match.group(1).strip().strip("\"'")
        if filename.lower().startswith("utf-8''"):
            filename = filename[7:]
        filename = unquote(filename)
        return filename or None

    @staticmethod
    def _ensure_extension(filename: str, content_type: str | None) -> str:
        if not content_type:
            return filename
        extension = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
        if not extension:
            return filename
        if filename.lower().endswith(extension.lower()):
            return filename
        return f"{filename}{extension}"

    @staticmethod
    async def _download_output_file(url: str) -> tuple[bytes, str]:
        timeout = ClientTimeout(total=60)
        async with ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get("Content-Type")
                disposition = resp.headers.get("Content-Disposition")
                filename = (
                    GenerationService._extract_filename_from_disposition(disposition)
                    or GenerationService.extract_filename_from_url(url)
                    or "result"
                )
                filename = os.path.basename(filename)
                filename = GenerationService._ensure_extension(filename, content_type)
                return await resp.read(), filename

    @staticmethod
    async def send_results(
        bot: Bot,
        chat_id: int,
        outputs: list[str],
        reply_to_message_id: int | None,
        caption_text: str,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> None:
        """Send generation results to user."""
        caption_pending = True
        document_failed = False

        for url in outputs:
            caption_value = caption_text if caption_pending else None
            try:
                file_bytes, filename = await GenerationService._download_output_file(url)
                sent_document = await GenerationService._retry_send(
                    lambda c=caption_value, f=filename, b=file_bytes: bot.send_document(
                        chat_id,
                        BufferedInputFile(b, filename=f),
                        reply_to_message_id=reply_to_message_id,
                        caption=c,
                        parse_mode="HTML",
                    )
                )
            except Exception:
                filename = GenerationService.extract_filename_from_url(url)
                sent_document = await GenerationService._retry_send(
                    lambda u=url, f=filename, c=caption_value: bot.send_document(
                        chat_id,
                        URLInputFile(u, filename=f),
                        reply_to_message_id=reply_to_message_id,
                        caption=c,
                        parse_mode="HTML",
                    )
                )

            if not sent_document:
                document_failed = True
            if sent_document and caption_pending:
                caption_pending = False

            # Fallback: send URL as text
            if not sent_document:
                await GenerationService._retry_send(
                    lambda u=url: bot.send_message(
                        chat_id, u, reply_to_message_id=reply_to_message_id
                    )
                )

        if document_failed:
            await GenerationService._retry_send(
                lambda: bot.send_message(
                    chat_id,
                    _(TranslationKey.GEN_SEND_ERROR, None),
                    reply_to_message_id=reply_to_message_id,
                )
            )

    @staticmethod
    async def _retry_send(
        action,
        attempts: int = BotConstants.SEND_RETRY_ATTEMPTS,
        delay_seconds: float = BotConstants.SEND_RETRY_DELAY_SECONDS,
    ) -> bool:
        """Retry send action with exponential backoff."""
        for attempt in range(attempts):
            try:
                await action()
                return True
            except Exception:
                if attempt == attempts - 1:
                    return False
                await asyncio.sleep(delay_seconds * (attempt + 1))
        return False

    @staticmethod
    async def poll_generation_status(
        bot: Bot,
        chat_id: int,
        message_id: int,
        request_id: int,
        telegram_id: int,
        prompt: str,
        model_name: str,
        prompt_message_id: int | None,
        _: Callable[[TranslationKey, dict | None], str],
    ) -> None:
        """Poll generation status and send results when done."""
        container = get_container()
        last_status_text = None

        while True:
            await asyncio.sleep(BotConstants.POLL_INTERVAL_SECONDS)

            try:
                result = await container.api_client.refresh_generation(request_id, telegram_id)
            except APIError as exc:
                logger.warning("Generation status check failed", error=str(exc))
                continue
            except Exception:
                logger.warning("Generation status check failed")
                continue

            status = result.get("status")

            # Update status message only for queue/processing
            status_text = GenerationService._get_status_message(status, _)
            if status_text and status_text != last_status_text:
                try:
                    await bot.edit_message_text(
                        status_text,
                        chat_id=chat_id,
                        message_id=message_id,
                    )
                except TelegramBadRequest:
                    pass
                last_status_text = status_text

            # Handle completion
            if status == "completed":
                try:
                    outputs = await container.api_client.get_generation_results(request_id, telegram_id)
                except Exception:
                    outputs = []

                duration_seconds = GenerationService.parse_duration_seconds(
                    result.get("started_at"),
                    result.get("completed_at"),
                    result.get("created_at"),
                )

                caption_text = GenerationService.build_result_caption(
                    prompt, model_name, result.get("cost"), duration_seconds, _
                )

                try:
                    await bot.edit_message_text(
                        _(TranslationKey.GEN_COMPLETED, None),
                        chat_id=chat_id,
                        message_id=message_id,
                    )
                except TelegramBadRequest:
                    pass

                if outputs:
                    await GenerationService.send_results(
                        bot, chat_id, outputs, prompt_message_id, caption_text, _
                    )
                return

            # Handle failure
            if status == "failed":
                try:
                    error_message = result.get("error_message")
                    if error_message:
                        text = _(TranslationKey.GEN_ERROR, {"error": error_message})
                    else:
                        text = _(TranslationKey.GEN_FAILED, None)
                    await bot.edit_message_text(
                        text,
                        chat_id=chat_id,
                        message_id=message_id,
                        reply_markup=GenerationKeyboard.retry(_),
                    )
                except TelegramBadRequest:
                    pass
                return
