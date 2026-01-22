"""Celery tasks."""

import asyncio
import mimetypes
import os
import re
import time
from datetime import datetime
from typing import Optional
from urllib.parse import unquote, urlparse

import httpx
from celery import shared_task
from sqlalchemy import select

from app.core.config import get_settings
from app.infrastructure.logging import get_logger
from app.services.redis_client import get_redis

logger = get_logger(__name__)

settings = get_settings()

# Rate limiting: 20 messages per second for Telegram
RATE_LIMIT_MESSAGES_PER_SECOND = 20
RATE_LIMIT_INTERVAL = 1.0 / RATE_LIMIT_MESSAGES_PER_SECOND  # 0.05 seconds
SUPPORTED_LANGUAGES = {"uz", "ru", "en"}

try:
    from bot.locales import TranslationKey, get_text
except Exception:
    TranslationKey = None
    get_text = None


def run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Redis key prefix for generation status tracking
_GEN_STATUS_PREFIX = "gen_status:"
_GEN_STATUS_TTL = 3600  # 1 hour TTL for automatic cleanup


async def _get_generation_status(chat_id: int, message_id: int) -> str | None:
    """Get last known generation status from Redis."""
    redis = get_redis()
    key = f"{_GEN_STATUS_PREFIX}{chat_id}:{message_id}"
    return await redis.get(key)


async def _set_generation_status(chat_id: int, message_id: int, status: str) -> None:
    """Set generation status in Redis with TTL."""
    redis = get_redis()
    key = f"{_GEN_STATUS_PREFIX}{chat_id}:{message_id}"
    await redis.set(key, status, ex=_GEN_STATUS_TTL)


@shared_task(bind=True, max_retries=3)
def process_generation(
    self,
    generation_request_id: int,
    chat_id: int | None,
    message_id: int | None,
    prompt_message_id: int | None = None,
):
    """Process image generation task with polling.

    This task is responsible for:
    1. Polling Wavespeed API for status
    2. Updating generation status in DB
    3. Sending result to user via Telegram when complete
    """
    from app.db.models import (
        GenerationJob,
        GenerationRequest,
        GenerationStatus,
        ModelCatalog,
        User,
    )
    from app.db.session import sync_session_factory
    from app.services.wavespeed import WavespeedClient

    logger.info(
        "Starting generation polling",
        generation_id=generation_request_id,
        chat_id=chat_id,
        message_id=message_id,
    )

    poll_interval = settings.generation_poll_interval_seconds
    max_duration = settings.generation_poll_max_duration_seconds
    start_time = time.time()

    try:
        with sync_session_factory() as session:
            # Get generation request and job
            request = session.query(GenerationRequest).filter(GenerationRequest.id == generation_request_id).first()

            if not request:
                logger.error("Generation request not found", generation_id=generation_request_id)
                return {"error": "Request not found"}

            job = session.query(GenerationJob).filter(GenerationJob.request_id == request.id).first()

            # Get model for caption
            model = session.query(ModelCatalog).filter(ModelCatalog.id == request.model_id).first()
            model_name = model.name if model else "Unknown"

            input_params = request.input_params or {}
            chat_id = chat_id or input_params.get("chat_id")
            message_id = message_id or input_params.get("message_id")
            prompt_message_id = prompt_message_id or input_params.get("prompt_message_id")
            user = session.query(User).filter(User.id == request.user_id).first()
            telegram_id = user.telegram_id if user else None
            language = _resolve_language(input_params, telegram_id)

            if not chat_id or not message_id:
                logger.warning(
                    "Missing chat/message ids for generation delivery",
                    generation_id=generation_request_id,
                )
                return {"error": "Missing chat/message ids"}

            if request.status == GenerationStatus.completed:
                outputs = _get_generation_outputs(session, request.id)
                if outputs:
                    _notify_user_generation_complete(
                        chat_id,
                        message_id,
                        request.prompt,
                        model_name,
                        request.cost or 0,
                        outputs,
                        prompt_message_id,
                        language,
                    )
                return {"status": "completed", "generation_id": generation_request_id}

            if not job or not job.provider_job_id:
                logger.error("Job not found", generation_id=generation_request_id)
                return {"error": "Job not found"}

            provider_job_id = job.provider_job_id

        # Create Wavespeed client for polling
        client = WavespeedClient(
            api_key=settings.wavespeed_api_key,
            api_base_url=settings.wavespeed_api_base_url,
            timeout_seconds=settings.wavespeed_timeout_seconds,
        )

        # Polling loop
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_duration:
                logger.warning(
                    "Generation polling timeout",
                    generation_id=generation_request_id,
                    elapsed=elapsed,
                )
                _mark_generation_failed(generation_request_id, "Polling timeout - generation took too long")
                _notify_user_generation_failed(
                    chat_id,
                    message_id,
                    _build_timeout_message(language),
                    request.cost or 0,
                    language,
                )
                return {"status": "timeout", "generation_id": generation_request_id}

            time.sleep(poll_interval)

            try:
                response = run_async(client.get_prediction_result(provider_job_id))
            except Exception as e:
                logger.warning(
                    "Wavespeed poll error",
                    generation_id=generation_request_id,
                    error=str(e),
                )
                continue

            status_value = str(response.data.get("status", "")).lower()
            outputs = _normalize_outputs(response.data.get("outputs", []))

            if status_value == "completed" or (not status_value and outputs):
                # Generation completed successfully
                _complete_generation(generation_request_id, outputs)
                _notify_user_generation_complete(
                    chat_id,
                    message_id,
                    request.prompt,
                    model_name,
                    request.cost or 0,
                    outputs,
                    prompt_message_id,
                    language,
                )
                logger.info(
                    "Generation completed",
                    generation_id=generation_request_id,
                    outputs_count=len(outputs),
                )
                return {"status": "completed", "generation_id": generation_request_id}

            elif status_value == "failed":
                # Get error message from response data first, fallback to response message
                error_msg = response.data.get("error") or response.message or "Generation failed"
                _mark_generation_failed(generation_request_id, error_msg)
                _notify_user_generation_failed(chat_id, message_id, error_msg, request.cost or 0, language)
                logger.warning(
                    "Generation failed",
                    generation_id=generation_request_id,
                    error=error_msg,
                )
                return {"status": "failed", "generation_id": generation_request_id}

            # Still running, continue polling
            # Update user with current status if it changed
            _update_user_generation_status(chat_id, message_id, status_value, language)
            logger.debug(
                "Generation still running",
                generation_id=generation_request_id,
                status=status_value,
                elapsed=elapsed,
            )

    except Exception as exc:
        logger.error(
            "Generation processing failed",
            generation_id=generation_request_id,
            error=str(exc),
        )
        _mark_generation_failed(generation_request_id, str(exc))
        raise self.retry(exc=exc, countdown=30)


def _normalize_outputs(outputs) -> list[str]:
    """Normalize outputs to list of URLs."""
    if not outputs:
        return []
    if isinstance(outputs, str):
        return [outputs]
    return [output for output in outputs if output]


def _get_generation_outputs(session, request_id: int) -> list[str]:
    """Fetch generation outputs from DB."""
    from app.db.models import GenerationResult

    return [
        result.image_url
        for result in session.execute(
            select(GenerationResult.image_url).where(GenerationResult.request_id == request_id)
        )
        .scalars()
        .all()
        if result
    ]


def _refund_generation_cost(session, request) -> None:
    """Refund charged credits for failed generation."""
    from app.db.models import LedgerEntry

    if not request.cost or request.cost <= 0:
        return
    refund_id = f"refund_{request.id}"
    existing = (
        session.query(LedgerEntry)
        .filter(
            LedgerEntry.user_id == request.user_id,
            LedgerEntry.entry_type == "refund",
            LedgerEntry.reference_id == refund_id,
        )
        .first()
    )
    if existing:
        return
    session.add(
        LedgerEntry(
            user_id=request.user_id,
            amount=int(request.cost),
            entry_type="refund",
            reference_id=refund_id,
            description=f"Refund for generation {request.id}",
        )
    )


def _rollback_trial_use(session, request_id: int) -> None:
    """Rollback trial usage for failed generation."""
    from app.db.models import TrialUse

    trial = session.query(TrialUse).filter(TrialUse.request_id == request_id).first()
    if trial:
        session.delete(trial)


def _mark_generation_failed(request_id: int, error_message: str) -> None:
    """Mark generation as failed in DB."""
    from app.db.models import (
        GenerationJob,
        GenerationRequest,
        GenerationStatus,
        JobStatus,
    )
    from app.db.session import sync_session_factory

    try:
        with sync_session_factory() as session:
            request = session.query(GenerationRequest).filter(GenerationRequest.id == request_id).first()
            if request:
                request.status = GenerationStatus.failed
                request.completed_at = datetime.utcnow()
                _refund_generation_cost(session, request)
                _rollback_trial_use(session, request.id)

            job = session.query(GenerationJob).filter(GenerationJob.request_id == request_id).first()
            if job:
                job.status = JobStatus.failed
                job.completed_at = datetime.utcnow()
                job.error_message = error_message

            session.commit()
    except Exception as e:
        logger.error("Failed to mark generation as failed", error=str(e))


def _complete_generation(request_id: int, outputs: list[str]) -> None:
    """Complete generation and save results."""
    from app.db.models import (
        GenerationJob,
        GenerationRequest,
        GenerationResult,
        GenerationStatus,
        JobStatus,
    )
    from app.db.session import sync_session_factory

    try:
        with sync_session_factory() as session:
            request = session.query(GenerationRequest).filter(GenerationRequest.id == request_id).first()
            if request:
                request.status = GenerationStatus.completed
                request.completed_at = datetime.utcnow()

            job = session.query(GenerationJob).filter(GenerationJob.request_id == request_id).first()
            if job:
                job.status = JobStatus.completed
                job.completed_at = datetime.utcnow()

            # Add results
            existing = set(
                session.execute(select(GenerationResult.image_url).where(GenerationResult.request_id == request_id))
                .scalars()
                .all()
            )
            for output in outputs:
                if output and output not in existing:
                    session.add(GenerationResult(request_id=request_id, image_url=output))

            session.commit()
    except Exception as e:
        logger.error("Failed to complete generation", error=str(e))


def _notify_user_generation_complete(
    chat_id: int,
    message_id: int,
    prompt: str,
    model_name: str,
    cost: int,
    outputs: list[str],
    prompt_message_id: int | None,
    language: str,
) -> None:
    """Send generation result to user via Telegram."""
    if not settings.bot_token:
        logger.warning("Bot token not configured, skipping notification")
        return

    try:
        # Delete status message
        run_async(_delete_telegram_message(chat_id, message_id))

        # Send results
        caption_sent = False
        for output_url in outputs:
            caption = _build_result_caption(
                language,
                prompt,
                model_name,
                cost,
            )
            caption_value = caption if not caption_sent else None
            run_async(
                _send_telegram_document(
                    chat_id,
                    output_url,
                    caption_value,
                    prompt_message_id,
                )
            )
            caption_sent = True
    except Exception as e:
        logger.error("Failed to send generation result", error=str(e))


def _notify_user_generation_failed(
    chat_id: int,
    message_id: int,
    error_message: str,
    refunded_credits: int,
    language: str,
) -> None:
    """Notify user that generation failed."""
    if not settings.bot_token:
        return

    try:
        text = _build_failure_message(language, error_message, refunded_credits)
        run_async(_edit_telegram_message(chat_id, message_id, text))
    except Exception as e:
        logger.error("Failed to send failure notification", error=str(e))


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_model_hashtag(model_name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", model_name.title())
    if not cleaned:
        return "#Model"
    return f"#{cleaned}"


def _build_result_caption(
    language: str,
    prompt: str,
    model_name: str,
    cost: int,
) -> str:
    safe_prompt = _escape_html(prompt[:500])
    hashtag = _format_model_hashtag(model_name)
    if get_text and TranslationKey:
        return get_text(
            TranslationKey.GEN_RESULT_CAPTION,
            language,
            {
                "model": hashtag,
                "credits": cost,
                "prompt": safe_prompt,
            },
        )
    return f"Result ready\nModel: {hashtag}\nCredits: {cost}\nPrompt:\n<blockquote>{safe_prompt}</blockquote>"


def _build_failure_message(language: str, error_message: str, refunded_credits: int = 0) -> str:
    """Build failure message with error details and refund info."""
    safe_error = _escape_html(error_message)

    # Build base message
    if get_text and TranslationKey:
        message = get_text(
            TranslationKey.GEN_ERROR,
            language,
            {"error": safe_error},
        )
    else:
        message = f"❌ Generatsiya muvaffaqiyatsiz\n\nSabab: {safe_error}"

    # Add refund info if credits were refunded
    if refunded_credits > 0:
        message += f"\n\n💰 {refunded_credits} credit qaytarildi"

    return message


def _build_timeout_message(language: str) -> str:
    if get_text and TranslationKey:
        return get_text(TranslationKey.GEN_TIMEOUT, language)
    return "Generation timeout. Please try again."


def _update_user_generation_status(
    chat_id: int,
    message_id: int,
    status: str,
    language: str,
) -> None:
    """Update user's status message with current generation status."""
    # Get last status from Redis
    last_status = run_async(_get_generation_status(chat_id, message_id))

    # Only update if status actually changed
    if last_status == status:
        return

    # Update tracking in Redis
    run_async(_set_generation_status(chat_id, message_id, status))

    # Build status message based on Wavespeed status
    if status in ("processing", "in_progress", "running"):
        if get_text and TranslationKey:
            text = get_text(TranslationKey.GEN_PROCESSING, language)
        else:
            text = "⏳ Holat: Jarayonda"
    elif status in ("in_queue", "queued", "pending"):
        if get_text and TranslationKey:
            text = get_text(TranslationKey.GEN_IN_QUEUE, language)
        else:
            text = "⏳ Holat: Navbatda"
    else:
        # Unknown status, don't update
        return

    # Update message
    if not settings.bot_token:
        return

    try:
        run_async(_edit_telegram_message(chat_id, message_id, text))
    except Exception as e:
        logger.debug(f"Failed to update status message: {e}")


def _resolve_language(input_params: dict | None, telegram_id: int | None) -> str:
    lang = None
    if isinstance(input_params, dict):
        value = input_params.get("language")
        if isinstance(value, str) and value in SUPPORTED_LANGUAGES:
            lang = value
    if lang:
        return lang
    if telegram_id:
        lang = _get_language_from_redis(telegram_id)
    return lang or "uz"


def _get_language_from_redis(telegram_id: int) -> str | None:
    async def _fetch() -> str | None:
        redis = get_redis()
        try:
            return await redis.hget("user_languages", str(telegram_id))
        except Exception:
            return None

    value = run_async(_fetch())
    if isinstance(value, str) and value in SUPPORTED_LANGUAGES:
        return value
    return None


async def _delete_telegram_message(chat_id: int, message_id: int) -> None:
    """Delete a Telegram message."""
    url = f"https://api.telegram.org/bot{settings.bot_token}/deleteMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": chat_id, "message_id": message_id})


async def _edit_telegram_message(chat_id: int, message_id: int, text: str) -> None:
    """Edit a Telegram message."""
    url = f"https://api.telegram.org/bot{settings.bot_token}/editMessageText"
    async with httpx.AsyncClient() as client:
        await client.post(
            url,
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
            },
        )


async def _send_telegram_document(
    chat_id: int,
    document_url: str,
    caption: str | None,
    prompt_message_id: int | None,
) -> None:
    """Send a document via Telegram."""
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendDocument"
    async with httpx.AsyncClient(timeout=60) as client:
        data = {
            "chat_id": chat_id,
            "parse_mode": "HTML",
        }
        if caption:
            data["caption"] = caption
        if prompt_message_id:
            data["reply_to_message_id"] = prompt_message_id
        try:
            file_bytes, filename, content_type = await _download_output_file(document_url)
            files = {
                "document": (
                    filename,
                    file_bytes,
                    content_type or "application/octet-stream",
                )
            }
            await client.post(url, data=data, files=files)
        except Exception:
            data["document"] = document_url
            await client.post(url, data=data)


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


def _extract_filename_from_url(url: str) -> str | None:
    path = urlparse(url).path
    name = unquote(path.rsplit("/", 1)[-1]) if path else ""
    return name or None


def _ensure_extension(filename: str, content_type: str | None) -> str:
    if not content_type:
        return filename
    extension = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
    if not extension:
        return filename
    if filename.lower().endswith(extension.lower()):
        return filename
    return f"{filename}{extension}"


async def _download_output_file(url: str) -> tuple[bytes, str, str | None]:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type")
        disposition = resp.headers.get("Content-Disposition")
        filename = _extract_filename_from_disposition(disposition) or _extract_filename_from_url(url) or "result"
        filename = os.path.basename(filename)
        filename = _ensure_extension(filename, content_type)
        return resp.content, filename, content_type


@shared_task(bind=True)
def start_broadcast_task(self, broadcast_id: int):
    """Start a broadcast - prepare recipients and begin sending.

    This task:
    1. Updates broadcast status to running
    2. Gets filtered user list
    3. Queues individual send tasks
    """
    from app.db.models import Broadcast, BroadcastStatus
    from app.db.session import sync_session_factory

    logger.info("Starting broadcast", broadcast_id=broadcast_id)

    try:
        with sync_session_factory() as session:
            # Get broadcast
            broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
            if not broadcast:
                logger.error("Broadcast not found", broadcast_id=broadcast_id)
                return {"error": "Broadcast not found"}

            if broadcast.status != BroadcastStatus.pending:
                logger.warning("Broadcast not pending", broadcast_id=broadcast_id, status=broadcast.status.value)
                return {"error": f"Broadcast is {broadcast.status.value}"}

            # Update status to running
            broadcast.status = BroadcastStatus.running
            broadcast.started_at = datetime.utcnow()
            session.commit()

            # Get filtered user IDs
            user_ids = _get_filtered_user_ids(session, broadcast.filter_type, broadcast.filter_params)

            # Update total users count
            broadcast.total_users = len(user_ids)
            session.commit()

            logger.info("Broadcasting to users", broadcast_id=broadcast_id, total_users=len(user_ids))

            # Queue individual send tasks with rate limiting
            for telegram_id in user_ids:
                send_broadcast_message.apply_async(
                    args=[
                        broadcast_id,
                        telegram_id,
                        broadcast.content_type,
                        broadcast.text,
                        broadcast.media_file_id,
                        broadcast.inline_button_text,
                        broadcast.inline_button_url,
                    ],
                    countdown=0,  # Will be rate limited in the task
                )

        return {"status": "started", "total_users": len(user_ids)}

    except Exception as exc:
        logger.exception("Failed to start broadcast", broadcast_id=broadcast_id, error=str(exc))

        # Mark as failed
        try:
            with sync_session_factory() as session:
                broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
                if broadcast:
                    broadcast.status = BroadcastStatus.failed
                    broadcast.completed_at = datetime.utcnow()
                    session.commit()
        except Exception:
            pass

        return {"error": str(exc)}


def _get_filtered_user_ids(session, filter_type: str, filter_params: Optional[dict] = None) -> list:
    """Get user IDs matching the filter (sync version)."""
    from datetime import timedelta

    from sqlalchemy import func

    from app.db.models import LedgerEntry, User

    now = datetime.utcnow()

    if filter_type == "all":
        users = session.query(User.telegram_id).filter(User.is_banned == False).all()

    elif filter_type == "active_7d":
        cutoff = now - timedelta(days=7)
        users = (
            session.query(User.telegram_id)
            .filter(
                User.is_banned == False,
                User.last_active_at >= cutoff,
            )
            .all()
        )

    elif filter_type == "active_30d":
        cutoff = now - timedelta(days=30)
        users = (
            session.query(User.telegram_id)
            .filter(
                User.is_banned == False,
                User.last_active_at >= cutoff,
            )
            .all()
        )

    elif filter_type == "with_balance":
        balance_subq = (
            session.query(LedgerEntry.user_id, func.sum(LedgerEntry.amount).label("balance"))
            .group_by(LedgerEntry.user_id)
            .having(func.sum(LedgerEntry.amount) > 0)
            .subquery()
        )
        users = (
            session.query(User.telegram_id)
            .join(balance_subq, User.id == balance_subq.c.user_id)
            .filter(User.is_banned == False)
            .all()
        )

    elif filter_type == "paid_users":
        paid_subq = session.query(LedgerEntry.user_id).filter(LedgerEntry.entry_type == "deposit").distinct().subquery()
        users = (
            session.query(User.telegram_id)
            .join(paid_subq, User.id == paid_subq.c.user_id)
            .filter(User.is_banned == False)
            .all()
        )

    elif filter_type == "new_users":
        cutoff = now - timedelta(days=7)
        users = (
            session.query(User.telegram_id)
            .filter(
                User.is_banned == False,
                User.created_at >= cutoff,
            )
            .all()
        )

    else:
        users = session.query(User.telegram_id).filter(User.is_banned == False).all()

    return [u[0] for u in users]


@shared_task(bind=True, max_retries=2, rate_limit="20/s")
def send_broadcast_message(
    self,
    broadcast_id: int,
    telegram_id: int,
    content_type: str,
    text: Optional[str] = None,
    media_file_id: Optional[str] = None,
    inline_button_text: Optional[str] = None,
    inline_button_url: Optional[str] = None,
):
    """Send broadcast message to a single user.

    Rate limited to 20 messages per second by Celery.
    """
    from sqlalchemy import update

    from app.db.models import Broadcast, BroadcastRecipient, BroadcastStatus, User
    from app.db.session import sync_session_factory

    try:
        # Check if broadcast is still running
        with sync_session_factory() as session:
            broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
            if not broadcast or broadcast.status == BroadcastStatus.cancelled:
                logger.info("Broadcast cancelled, skipping", broadcast_id=broadcast_id, telegram_id=telegram_id)
                return {"status": "skipped", "reason": "cancelled"}

            admin_id = broadcast.admin_id

        # Send message via Telegram Bot API
        result = _send_telegram_message(
            telegram_id=telegram_id,
            content_type=content_type,
            text=text,
            media_file_id=media_file_id,
            inline_button_text=inline_button_text,
            inline_button_url=inline_button_url,
        )

        # Update counters atomically
        with sync_session_factory() as session:
            # Use atomic update to avoid race conditions
            if result["success"]:
                session.execute(
                    update(Broadcast).where(Broadcast.id == broadcast_id).values(sent_count=Broadcast.sent_count + 1)
                )
                status = "sent"
            elif result.get("blocked"):
                session.execute(
                    update(Broadcast)
                    .where(Broadcast.id == broadcast_id)
                    .values(blocked_count=Broadcast.blocked_count + 1)
                )
                status = "blocked"
            else:
                session.execute(
                    update(Broadcast)
                    .where(Broadcast.id == broadcast_id)
                    .values(failed_count=Broadcast.failed_count + 1)
                )
                status = "failed"

            # Get user_id from telegram_id
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            user_id = user.id if user else None

            # Add recipient record
            if user_id:
                recipient = BroadcastRecipient(
                    broadcast_id=broadcast_id,
                    user_id=user_id,
                    telegram_id=telegram_id,
                    status=status,
                    error_message=result.get("error"),
                    sent_at=datetime.utcnow(),
                )
                session.add(recipient)

            session.commit()

            # Re-fetch broadcast to check completion
            broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
            if broadcast:
                total_processed = (
                    (broadcast.sent_count or 0) + (broadcast.failed_count or 0) + (broadcast.blocked_count or 0)
                )
                if total_processed >= broadcast.total_users and broadcast.status != BroadcastStatus.completed:
                    broadcast.status = BroadcastStatus.completed
                    broadcast.completed_at = datetime.utcnow()
                    session.commit()

                    logger.info("Broadcast completed", broadcast_id=broadcast_id)

                    # Send notification to admin
                    _notify_admin_broadcast_completed(
                        admin_id=admin_id,
                        broadcast_id=broadcast_id,
                        public_id=broadcast.public_id,
                        total=broadcast.total_users,
                        sent=broadcast.sent_count or 0,
                        failed=broadcast.failed_count or 0,
                        blocked=broadcast.blocked_count or 0,
                    )

        return result

    except Exception as exc:
        logger.error(
            "Broadcast message failed",
            broadcast_id=broadcast_id,
            telegram_id=telegram_id,
            error=str(exc),
        )

        # Update failed counter atomically
        try:
            from sqlalchemy import update

            from app.db.models import Broadcast, BroadcastStatus
            from app.db.session import sync_session_factory

            with sync_session_factory() as session:
                session.execute(
                    update(Broadcast)
                    .where(Broadcast.id == broadcast_id)
                    .values(failed_count=Broadcast.failed_count + 1)
                )
                session.commit()

                # Check completion
                broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
                if broadcast:
                    total_processed = (
                        (broadcast.sent_count or 0) + (broadcast.failed_count or 0) + (broadcast.blocked_count or 0)
                    )
                    if total_processed >= broadcast.total_users and broadcast.status != BroadcastStatus.completed:
                        broadcast.status = BroadcastStatus.completed
                        broadcast.completed_at = datetime.utcnow()
                        session.commit()

                        _notify_admin_broadcast_completed(
                            admin_id=broadcast.admin_id,
                            broadcast_id=broadcast_id,
                            public_id=broadcast.public_id,
                            total=broadcast.total_users,
                            sent=broadcast.sent_count or 0,
                            failed=broadcast.failed_count or 0,
                            blocked=broadcast.blocked_count or 0,
                        )
        except Exception as inner_exc:
            logger.error("Failed to update broadcast counter", error=str(inner_exc))

        # Return error instead of retrying (message may have been sent)
        return {"success": False, "error": str(exc)}


def _notify_admin_broadcast_completed(
    admin_id: int,
    broadcast_id: int,
    public_id: str,
    total: int,
    sent: int,
    failed: int,
    blocked: int,
) -> None:
    """Send notification to admin when broadcast is completed."""
    bot_token = settings.bot_token
    if not bot_token:
        logger.warning("BOT_TOKEN not configured, skipping admin notification")
        return

    success_rate = (sent / total * 100) if total > 0 else 0

    message = (
        f"✅ <b>Broadcast Completed!</b>\n\n"
        f"📋 ID: <code>{public_id}</code>\n\n"
        f"📊 <b>Results:</b>\n"
        f"👥 Total: {total}\n"
        f"📤 Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"🚫 Blocked: {blocked}\n"
        f"📈 Success Rate: {success_rate:.1f}%"
    )

    try:
        import httpx

        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": admin_id,
                    "text": message,
                    "parse_mode": "HTML",
                },
            )
            if not response.json().get("ok"):
                logger.warning(
                    "Failed to send admin notification",
                    admin_id=admin_id,
                    error=response.json(),
                )
    except Exception as e:
        logger.error("Failed to send admin notification", error=str(e))


def _send_telegram_message(
    telegram_id: int,
    content_type: str,
    text: Optional[str] = None,
    media_file_id: Optional[str] = None,
    inline_button_text: Optional[str] = None,
    inline_button_url: Optional[str] = None,
) -> dict:
    """Send a message via Telegram Bot API (sync)."""
    bot_token = settings.bot_token
    if not bot_token:
        return {"success": False, "error": "BOT_TOKEN not configured"}

    base_url = f"https://api.telegram.org/bot{bot_token}"

    # Build inline keyboard if button provided
    reply_markup = None
    if inline_button_text and inline_button_url:
        reply_markup = {"inline_keyboard": [[{"text": inline_button_text, "url": inline_button_url}]]}

    try:
        with httpx.Client(timeout=30.0) as client:
            if content_type == "text":
                payload = {
                    "chat_id": telegram_id,
                    "text": text or "",
                    "parse_mode": "HTML",
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                response = client.post(f"{base_url}/sendMessage", json=payload)

            elif content_type == "photo":
                payload = {
                    "chat_id": telegram_id,
                    "photo": media_file_id,
                    "caption": text or "",
                    "parse_mode": "HTML",
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                response = client.post(f"{base_url}/sendPhoto", json=payload)

            elif content_type == "video":
                payload = {
                    "chat_id": telegram_id,
                    "video": media_file_id,
                    "caption": text or "",
                    "parse_mode": "HTML",
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                response = client.post(f"{base_url}/sendVideo", json=payload)

            elif content_type == "audio":
                payload = {
                    "chat_id": telegram_id,
                    "audio": media_file_id,
                    "caption": text or "",
                    "parse_mode": "HTML",
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                response = client.post(f"{base_url}/sendAudio", json=payload)

            elif content_type == "sticker":
                payload = {
                    "chat_id": telegram_id,
                    "sticker": media_file_id,
                }
                response = client.post(f"{base_url}/sendSticker", json=payload)

            else:
                return {"success": False, "error": f"Unknown content type: {content_type}"}

            data = response.json()

            if data.get("ok"):
                return {"success": True, "telegram_id": telegram_id}
            else:
                error_code = data.get("error_code", 0)
                description = data.get("description", "Unknown error")

                # Check if user blocked bot
                if error_code == 403 or "blocked" in description.lower() or "deactivated" in description.lower():
                    return {"success": False, "blocked": True, "error": description}

                return {"success": False, "error": description}

    except httpx.TimeoutException:
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@shared_task
def cleanup_expired_generations():
    """Cleanup expired/stuck generations.

    This task runs periodically to:
    1. Find stuck generations (pending/running > 10 minutes)
    2. Mark them as failed
    3. Clear Redis locks
    """
    from datetime import timedelta

    from app.db.models import (
        GenerationJob,
        GenerationRequest,
        GenerationStatus,
        JobStatus,
    )
    from app.db.session import sync_session_factory

    logger.info("Running generation cleanup")

    # Generations stuck for more than 10 minutes
    cutoff_time = datetime.utcnow() - timedelta(minutes=10)
    cleaned_count = 0

    try:
        with sync_session_factory() as session:
            # Find stuck generations
            stuck_statuses = [
                GenerationStatus.pending,
                GenerationStatus.configuring,
                GenerationStatus.queued,
                GenerationStatus.running,
            ]

            stuck_generations = (
                session.query(GenerationRequest)
                .filter(
                    GenerationRequest.status.in_(stuck_statuses),
                    GenerationRequest.created_at < cutoff_time,
                )
                .all()
            )

            for gen in stuck_generations:
                logger.warning(
                    "Cleaning up stuck generation",
                    generation_id=gen.id,
                    status=gen.status.value,
                    created_at=gen.created_at.isoformat(),
                )

                # Mark as failed
                gen.status = GenerationStatus.failed
                gen.completed_at = datetime.utcnow()

                # Update job status
                job = session.query(GenerationJob).filter(GenerationJob.request_id == gen.id).first()
                if job:
                    job.status = JobStatus.failed
                    job.completed_at = datetime.utcnow()
                    job.error_message = "Generation timeout - cleaned up by system"

                cleaned_count += 1

            session.commit()

        logger.info("Generation cleanup completed", cleaned_count=cleaned_count)

    except Exception as e:
        logger.error("Generation cleanup failed", error=str(e))

    return {"cleaned_up": cleaned_count}


