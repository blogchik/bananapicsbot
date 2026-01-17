import re
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.deps.db import db_session_dep
from app.core.constants import SIZE_OPTIONS
from app.core.config import get_settings
from app.core.model_options import ModelParameterOptions
from app.deps.wavespeed import wavespeed_client
from app.db.models import (
    GenerationJob,
    GenerationReference,
    GenerationRequest,
    GenerationResult,
    GenerationStatus,
    JobStatus,
    LedgerEntry,
    ModelCatalog,
    ModelPrice,
    TrialUse,
)
from app.infrastructure.logging import get_logger
from app.schemas.generation import (
    GenerationAccessIn,
    GenerationActiveOut,
    GenerationRequestOut,
    GenerationSubmitIn,
    GenerationSubmitOut,
)
from app.services.ledger import get_user_balance
from app.services.model_options import get_model_parameter_options_from_wavespeed
from app.services.redis_client import get_redis
from app.services.users import get_or_create_user, get_user_by_telegram_id

router = APIRouter()
logger = get_logger(__name__)

SIZE_RE = re.compile(r"^(\d{3,4})[x*](\d{3,4})$")
WAVESPEED_BALANCE_CACHE_KEY = "wavespeed:balance"
WAVESPEED_BALANCE_ALERT_KEY = "wavespeed:balance:alerted"


def validate_size(size: str | None) -> None:
    if not size:
        return
    if size.lower() == "auto":
        return
    match = SIZE_RE.match(size.lower())
    if not match:
        raise HTTPException(status_code=400, detail="Invalid size format")
    width = int(match.group(1))
    height = int(match.group(2))
    if width < 1024 or width > 4096 or height < 1024 or height > 4096:
        raise HTTPException(status_code=400, detail="Size out of range")


def validate_model_options(
    options: ModelParameterOptions,
    size: str | None,
    aspect_ratio: str | None,
    resolution: str | None,
) -> None:
    if size and not options.supports_size:
        raise HTTPException(status_code=400, detail="Size not supported")
    if aspect_ratio and not options.supports_aspect_ratio:
        raise HTTPException(status_code=400, detail="Aspect ratio not supported")
    if resolution and not options.supports_resolution:
        raise HTTPException(status_code=400, detail="Resolution not supported")
    if size:
        validate_size(size)
        if options.size_options and size not in options.size_options:
            raise HTTPException(status_code=400, detail="Invalid size")
    if aspect_ratio and options.aspect_ratio_options:
        if aspect_ratio not in options.aspect_ratio_options:
            raise HTTPException(status_code=400, detail="Invalid aspect ratio")
    if resolution and options.resolution_options:
        if resolution not in options.resolution_options:
            raise HTTPException(status_code=400, detail="Invalid resolution")


def get_active_model(db: Session, model_id: int) -> ModelCatalog:
    model = db.execute(
        select(ModelCatalog).where(
            ModelCatalog.id == model_id,
            ModelCatalog.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


def _credits_from_usd(value: Decimal) -> int:
    return int((value * Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


_GPT_IMAGE_1_5_PRICES: dict[str, dict[str, int]] = {
    "low": {
        "1024*1024": 9000,
        "1024*1536": 13000,
        "1536*1024": 13000,
    },
    "medium": {
        "1024*1024": 34000,
        "1024*1536": 51000,
        "1536*1024": 51000,
    },
    "high": {
        "1024*1024": 133000,
        "1024*1536": 200000,
        "1536*1024": 200000,
    },
}


def _credits_from_price_units(value: int) -> int:
    return int(
        (Decimal(value) / Decimal("1000")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


def _normalize_gpt_image_size(size: str | None) -> str:
    if not size:
        return "1024*1024"
    normalized = size.lower().replace("x", "*")
    if normalized == "auto":
        return "1024*1024"
    return normalized


def _dynamic_price_for_model(
    model_key: str | None,
    size: str | None,
    resolution: str | None,
    quality: str | None,
) -> int | None:
    if not model_key:
        return None
    key = model_key.lower()
    if key == "seedream-v4":
        return _credits_from_usd(Decimal("0.027"))
    if key == "nano-banana-pro":
        res = (resolution or "").lower()
        usd = Decimal("0.24") if res == "4k" else Decimal("0.14")
        return _credits_from_usd(usd)
    if key == "gpt-image-1.5":
        size_value = _normalize_gpt_image_size(size)
        quality_value = (quality or "medium").lower()
        quality_prices = _GPT_IMAGE_1_5_PRICES.get(quality_value) or _GPT_IMAGE_1_5_PRICES["medium"]
        price_units = quality_prices.get(size_value) or quality_prices["1024*1024"]
        return _credits_from_price_units(price_units)
    return None


def get_generation_price(
    db: Session,
    model: ModelCatalog,
    size: str | None,
    resolution: str | None,
    quality: str | None,
) -> int:
    dynamic_price = _dynamic_price_for_model(model.key, size, resolution, quality)
    if dynamic_price is not None:
        return dynamic_price
    price = db.execute(
        select(ModelPrice)
        .where(ModelPrice.model_id == model.id, ModelPrice.is_active.is_(True))
        .order_by(ModelPrice.created_at.desc())
    ).scalar_one_or_none()
    if not price:
        raise HTTPException(status_code=400, detail="Model price not found")
    return int(price.unit_price)


def trial_available(db: Session, user_id: int) -> bool:
    trial = db.execute(
        select(TrialUse).where(TrialUse.user_id == user_id)
    ).scalar_one_or_none()
    return trial is None


def get_active_generation(db: Session, user_id: int) -> GenerationRequest | None:
    active_statuses = [
        GenerationStatus.pending,
        GenerationStatus.configuring,
        GenerationStatus.queued,
        GenerationStatus.running,
    ]
    return db.execute(
        select(GenerationRequest).where(
            GenerationRequest.user_id == user_id,
            GenerationRequest.status.in_(active_statuses),
        )
        .order_by(GenerationRequest.created_at.desc())
    ).scalar_one_or_none()


def count_active_generations(db: Session, user_id: int) -> int:
    active_statuses = [
        GenerationStatus.pending,
        GenerationStatus.configuring,
        GenerationStatus.queued,
        GenerationStatus.running,
    ]
    result = db.execute(
        select(func.count())
        .select_from(GenerationRequest)
        .where(
            GenerationRequest.user_id == user_id,
            GenerationRequest.status.in_(active_statuses),
        )
    ).scalar_one()
    return int(result or 0)


def get_request_for_user(
    db: Session, request_id: int, telegram_id: int
) -> GenerationRequest:
    request = db.execute(
        select(GenerationRequest).where(GenerationRequest.id == request_id)
    ).scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=404, detail="Generation not found")
    user = get_user_by_telegram_id(db, telegram_id)
    if not user or request.user_id != user.id:
        raise HTTPException(status_code=404, detail="Generation not found")
    return request


def normalize_outputs(outputs: list[str] | str | None) -> list[str]:
    if not outputs:
        return []
    if isinstance(outputs, str):
        return [outputs]
    return [output for output in outputs if output]


def extract_wavespeed_error(response) -> str | None:
    data = response.data if isinstance(response.data, dict) else {}
    candidates = [
        data.get("error_message"),
        data.get("error"),
        data.get("detail"),
        data.get("message"),
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()
    message = str(getattr(response, "message", "") or "").strip()
    if message and message.lower() != "success":
        return message
    return None


def extract_wavespeed_balance(data: dict[str, object] | None) -> float | None:
    if not isinstance(data, dict):
        return None
    candidates = [
        data.get("balance"),
        data.get("available_balance"),
        data.get("credits"),
        data.get("amount"),
        (data.get("account") or {}).get("balance"),
    ]
    for value in candidates:
        try:
            if value is None:
                continue
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


async def get_wavespeed_balance_cached(client, settings) -> float | None:
    redis = get_redis()
    try:
        cached = await redis.get(WAVESPEED_BALANCE_CACHE_KEY)
        if cached:
            return float(cached)
    except Exception as exc:
        logger.warning("Wavespeed balance cache read failed", error=str(exc))

    try:
        response = await client.get_balance()
    except Exception as exc:
        logger.warning("Wavespeed balance request failed", error=str(exc))
        return None

    balance = extract_wavespeed_balance(response.data)
    if balance is None:
        logger.warning("Wavespeed balance missing in response", data=response.data)
        return None

    try:
        await redis.set(
            WAVESPEED_BALANCE_CACHE_KEY,
            str(balance),
            ex=settings.wavespeed_balance_cache_ttl_seconds,
        )
    except Exception as exc:
        logger.warning("Wavespeed balance cache write failed", error=str(exc))
    return balance


async def notify_admins_low_balance(
    balance: float,
    threshold: float,
    settings,
) -> None:
    if not settings.bot_token or not settings.admin_ids_list:
        return
    redis = get_redis()
    try:
        lock = await redis.set(
            WAVESPEED_BALANCE_ALERT_KEY,
            "1",
            ex=settings.wavespeed_balance_alert_ttl_seconds,
            nx=True,
        )
        if not lock:
            return
    except Exception:
        pass

    text = (
        "Wavespeed balance low. "
        f"balance={balance:.4f} threshold={threshold:.4f}. "
        "Generations paused."
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        for admin_id in settings.admin_ids_list:
            try:
                await client.post(
                    f"https://api.telegram.org/bot{settings.bot_token}/sendMessage",
                    json={"chat_id": admin_id, "text": text},
                )
            except Exception as exc:
                logger.warning(
                    "Failed to notify admin about low balance",
                    admin_id=admin_id,
                    error=str(exc),
                )


async def ensure_wavespeed_balance(settings) -> float | None:
    client = wavespeed_client()
    balance = await get_wavespeed_balance_cached(client, settings)
    if balance is None:
        return None
    if balance < settings.wavespeed_min_balance:
        await notify_admins_low_balance(balance, settings.wavespeed_min_balance, settings)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "provider_balance_low",
                "message": "Wavespeed balance low",
                "balance": balance,
                "threshold": settings.wavespeed_min_balance,
            },
        )
    return balance


def rollback_generation_cost(db: Session, request: GenerationRequest) -> None:
    if not request.cost or request.cost <= 0:
        return
    refund_id = f"refund_{request.id}"
    existing = db.execute(
        select(LedgerEntry).where(
            LedgerEntry.user_id == request.user_id,
            LedgerEntry.entry_type == "refund",
            LedgerEntry.reference_id == refund_id,
        )
    ).scalar_one_or_none()
    if existing:
        return
    db.add(
        LedgerEntry(
            user_id=request.user_id,
            amount=int(request.cost),
            entry_type="refund",
            reference_id=refund_id,
            description=f"Refund for generation {request.id}",
        )
    )


def rollback_trial_use(db: Session, request_id: int) -> None:
    trial = db.execute(
        select(TrialUse).where(TrialUse.request_id == request_id)
    ).scalar_one_or_none()
    if trial:
        db.delete(trial)


def add_generation_results(
    db: Session, request_id: int, outputs: list[str] | str | None
) -> None:
    normalized = normalize_outputs(outputs)
    if not normalized:
        return
    existing = set(
        db.execute(
            select(GenerationResult.image_url).where(
                GenerationResult.request_id == request_id
            )
        )
        .scalars()
        .all()
    )
    for output in normalized:
        if output in existing:
            continue
        db.add(GenerationResult(request_id=request_id, image_url=output))


async def submit_wavespeed_generation(
    client,
    model_key: str,
    prompt: str,
    reference_urls: list[str],
    size: str | None,
    aspect_ratio: str | None,
    resolution: str | None,
    quality: str | None,
    input_fidelity: str | None,
):
    if model_key == "seedream-v4":
        seedream_size = size or resolution
        if reference_urls:
            return await client.submit_seedream_v4_i2i(
                prompt=prompt,
                images=reference_urls,
                size=seedream_size,
                enable_base64_output=False,
                enable_sync_mode=False,
            )
        return await client.submit_seedream_v4_t2i(
            prompt=prompt,
            size=seedream_size,
            enable_base64_output=False,
            enable_sync_mode=False,
        )
    if model_key == "nano-banana":
        if reference_urls:
            return await client.submit_nano_banana_i2i(
                prompt=prompt,
                images=reference_urls,
                aspect_ratio=aspect_ratio,
                enable_base64_output=False,
                enable_sync_mode=False,
            )
        return await client.submit_nano_banana_t2i(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            enable_base64_output=False,
            enable_sync_mode=False,
        )
    if model_key == "nano-banana-pro":
        if reference_urls:
            return await client.submit_nano_banana_pro_i2i(
                prompt=prompt,
                images=reference_urls,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                enable_base64_output=False,
                enable_sync_mode=False,
            )
        return await client.submit_nano_banana_pro_t2i(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            enable_base64_output=False,
            enable_sync_mode=False,
        )
    if model_key == "gpt-image-1.5":
        if reference_urls:
            return await client.submit_gpt_image_1_5_i2i(
                prompt=prompt,
                images=reference_urls,
                size=size,
                quality=quality,
                input_fidelity=input_fidelity,
                enable_base64_output=False,
                enable_sync_mode=False,
            )
        return await client.submit_gpt_image_1_5_t2i(
            prompt=prompt,
            size=size,
            quality=quality,
            enable_base64_output=False,
            enable_sync_mode=False,
        )
    raise HTTPException(status_code=400, detail="Unsupported model")


@router.post("/generations/submit", response_model=GenerationSubmitOut)
async def submit_generation(
    payload: GenerationSubmitIn,
    db: Session = Depends(db_session_dep),
) -> GenerationSubmitOut:
    settings = get_settings()
    user, _, _ = get_or_create_user(db, payload.telegram_id)
    await ensure_wavespeed_balance(settings)
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": user.id})
    model = get_active_model(db, payload.model_id)
    size_value = payload.size
    resolution_value = payload.resolution
    if model.key == "seedream-v4" and size_value and not resolution_value:
        resolution_value = size_value
        size_value = None
    price = get_generation_price(
        db,
        model,
        size_value,
        resolution_value,
        payload.quality,
    )
    model_options = await get_model_parameter_options_from_wavespeed(model.key)
    validate_model_options(
        model_options,
        size_value,
        payload.aspect_ratio,
        resolution_value,
    )

    active_count = count_active_generations(db, user.id)
    if active_count >= settings.max_parallel_generations_per_user:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Active generation limit reached",
                "active_count": active_count,
                "limit": settings.max_parallel_generations_per_user,
            },
        )

    reference_urls = [url for url in payload.reference_urls if url]
    reference_file_ids = [fid for fid in payload.reference_file_ids if fid]
    if reference_urls and not model.supports_image_to_image:
        raise HTTPException(status_code=400, detail="Model does not support image-to-image")
    if not reference_urls and not model.supports_text_to_image:
        raise HTTPException(status_code=400, detail="Model does not support text-to-image")
    if len(reference_urls) > 10:
        raise HTTPException(status_code=400, detail="Too many reference images")

    request = GenerationRequest(
        user_id=user.id,
        model_id=model.id,
        prompt=payload.prompt,
        status=GenerationStatus.configuring,
        references_count=len(reference_urls),
        size=size_value,
        aspect_ratio=payload.aspect_ratio,
        cost=0,
        input_params={
            "size": size_value,
            "aspect_ratio": payload.aspect_ratio,
            "resolution": resolution_value,
            "quality": payload.quality,
            "input_fidelity": payload.input_fidelity,
            "reference_urls": reference_urls,
            "reference_file_ids": reference_file_ids,
            "chat_id": payload.chat_id,
            "message_id": payload.message_id,
            "prompt_message_id": payload.prompt_message_id,
            "language": payload.language,
        },
    )
    db.add(request)
    db.flush()

    for idx, url in enumerate(reference_urls):
        file_id = reference_file_ids[idx] if idx < len(reference_file_ids) else None
        db.add(
            GenerationReference(
                request_id=request.id, url=url, telegram_file_id=file_id
            )
        )

    use_trial = trial_available(db, user.id)
    if use_trial:
        db.add(TrialUse(user_id=user.id, request_id=request.id))
        request.cost = 0
    else:
        balance = get_user_balance(db, user.id)
        if balance < price:
            request.status = GenerationStatus.failed
            db.commit()
            raise HTTPException(status_code=402, detail="Insufficient balance")
        db.add(
            LedgerEntry(
                user_id=user.id,
                amount=-price,
                entry_type="generation_charge",
                reference_id=str(request.id),
                description="Generation charge",
            )
        )
        request.cost = price

    client = wavespeed_client()

    try:
        response = await submit_wavespeed_generation(
            client,
            model.key,
            payload.prompt,
            reference_urls,
            size_value,
            payload.aspect_ratio,
            resolution_value,
            payload.quality,
            payload.input_fidelity,
        )
    except HTTPException:
        request.status = GenerationStatus.failed
        rollback_generation_cost(db, request)
        rollback_trial_use(db, request.id)
        db.commit()
        raise
    except Exception:
        request.status = GenerationStatus.failed
        rollback_generation_cost(db, request)
        rollback_trial_use(db, request.id)
        db.commit()
        raise HTTPException(status_code=502, detail="Wavespeed request failed")

    outputs = normalize_outputs(response.data.get("outputs", []))

    job = GenerationJob(
        request_id=request.id,
        provider="wavespeed",
        status=JobStatus.queued,
        provider_job_id=str(response.data.get("id")) if response.data.get("id") else None,
    )
    db.add(job)

    if outputs:
        add_generation_results(db, request.id, outputs)
        request.status = GenerationStatus.completed
        request.completed_at = datetime.utcnow()
        job.status = JobStatus.completed
        job.completed_at = datetime.utcnow()
    else:
        request.status = GenerationStatus.queued
    db.commit()
    db.refresh(request)

    if payload.chat_id and payload.message_id:
        try:
            from app.worker.tasks import process_generation

            process_generation.apply_async(
                args=[
                    request.id,
                    payload.chat_id,
                    payload.message_id,
                    payload.prompt_message_id,
                ]
            )
        except Exception:
            pass

    return GenerationSubmitOut(
        request=GenerationRequestOut.model_validate(request),
        job_id=job.id,
        provider_job_id=job.provider_job_id,
        trial_used=use_trial,
    )


@router.get("/generations/active", response_model=GenerationActiveOut)
async def get_active_generation_status(
    telegram_id: int = Query(..., gt=0),
    db: Session = Depends(db_session_dep),
) -> GenerationActiveOut:
    user = get_user_by_telegram_id(db, telegram_id)
    if not user:
        return GenerationActiveOut(has_active=False)
    active_request = get_active_generation(db, user.id)
    if not active_request:
        return GenerationActiveOut(has_active=False)
    return GenerationActiveOut(
        has_active=True,
        request_id=active_request.id,
        public_id=active_request.public_id,
        status=active_request.status,
    )


@router.get("/generations/{request_id}", response_model=GenerationRequestOut)
async def get_generation(
    request_id: int,
    telegram_id: int = Query(..., gt=0),
    db: Session = Depends(db_session_dep),
) -> GenerationRequestOut:
    request = get_request_for_user(db, request_id, telegram_id)
    return GenerationRequestOut.model_validate(request)


@router.post("/generations/{request_id}/refresh", response_model=GenerationRequestOut)
async def refresh_generation(
    request_id: int,
    payload: GenerationAccessIn,
    db: Session = Depends(db_session_dep),
) -> GenerationRequestOut:
    request = get_request_for_user(db, request_id, payload.telegram_id)

    job = db.execute(
        select(GenerationJob).where(GenerationJob.request_id == request.id)
    ).scalar_one_or_none()
    if not job or not job.provider_job_id:
        raise HTTPException(status_code=404, detail="Job not found")

    client = wavespeed_client()
    response = await client.get_prediction_result(job.provider_job_id)
    status_value = str(response.data.get("status", "")).lower()
    outputs = normalize_outputs(response.data.get("outputs", []))

    if status_value == "completed" or (not status_value and outputs):
        add_generation_results(db, request.id, outputs)
        request.status = GenerationStatus.completed
        request.completed_at = datetime.utcnow()
        job.status = JobStatus.completed
        job.completed_at = datetime.utcnow()
    elif status_value == "failed":
        error_message = extract_wavespeed_error(response)
        request.status = GenerationStatus.failed
        request.completed_at = datetime.utcnow()
        job.status = JobStatus.failed
        job.completed_at = datetime.utcnow()
        job.error_message = error_message or response.message
        rollback_generation_cost(db, request)
        rollback_trial_use(db, request.id)
    else:
        if status_value in {"created", "queued"}:
            request.status = GenerationStatus.queued
            job.status = JobStatus.queued
        else:
            request.status = GenerationStatus.running
            job.status = JobStatus.running
            if not request.started_at:
                request.started_at = datetime.utcnow()
            if not job.started_at:
                job.started_at = datetime.utcnow()

    db.commit()
    db.refresh(request)
    request_out = GenerationRequestOut.model_validate(request)
    if job.error_message:
        request_out = request_out.model_copy(
            update={"error_message": job.error_message}
        )
    return request_out


@router.get("/generations/{request_id}/results")
async def get_generation_results(
    request_id: int,
    telegram_id: int = Query(..., gt=0),
    db: Session = Depends(db_session_dep),
) -> list[str]:
    request = get_request_for_user(db, request_id, telegram_id)
    results = db.execute(
        select(GenerationResult).where(GenerationResult.request_id == request.id)
    ).scalars().all()
    return [result.image_url for result in results if result.image_url]


@router.get("/sizes")
async def list_sizes() -> list[str]:
    return SIZE_OPTIONS
