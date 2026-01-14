import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.deps.db import db_session_dep
from app.core.constants import SIZE_OPTIONS
from app.core.config import get_settings
from app.core.model_options import get_model_parameter_options
from app.deps.redis import redis_dep
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
from app.schemas.generation import (
    GenerationAccessIn,
    GenerationActiveOut,
    GenerationRequestOut,
    GenerationSubmitIn,
    GenerationSubmitOut,
)
from app.services.ledger import get_user_balance
from app.services.users import get_or_create_user, get_user_by_telegram_id

router = APIRouter()

SIZE_RE = re.compile(r"^(\d{3,4})\*(\d{3,4})$")


def validate_size(size: str | None) -> None:
    if not size:
        return
    match = SIZE_RE.match(size)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid size format")
    width = int(match.group(1))
    height = int(match.group(2))
    if width < 1024 or width > 4096 or height < 1024 or height > 4096:
        raise HTTPException(status_code=400, detail="Size out of range")


def validate_model_options(
    model_key: str,
    size: str | None,
    aspect_ratio: str | None,
    resolution: str | None,
) -> None:
    options = get_model_parameter_options(model_key)
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


def get_active_price(db: Session, model_id: int) -> int:
    price = db.execute(
        select(ModelPrice)
        .where(ModelPrice.model_id == model_id, ModelPrice.is_active.is_(True))
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


async def acquire_generation_lock(
    redis: Redis, user_id: int, ttl_seconds: int
) -> bool:
    key = f"gen:active:{user_id}"
    return bool(await redis.set(key, "pending", nx=True, ex=ttl_seconds))


async def set_generation_lock(
    redis: Redis, user_id: int, request_id: int, ttl_seconds: int
) -> None:
    key = f"gen:active:{user_id}"
    await redis.set(key, str(request_id), ex=ttl_seconds)


async def get_generation_lock(redis: Redis, user_id: int) -> str | None:
    key = f"gen:active:{user_id}"
    return await redis.get(key)


async def clear_generation_lock(
    redis: Redis, user_id: int, request_id: int
) -> None:
    key = f"gen:active:{user_id}"
    current = await redis.get(key)
    if current == str(request_id):
        await redis.delete(key)


async def release_generation_lock(redis: Redis, user_id: int) -> None:
    key = f"gen:active:{user_id}"
    await redis.delete(key)


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
):
    if model_key == "seedream-v4":
        if reference_urls:
            return await client.submit_seedream_v4_i2i(
                prompt=prompt,
                images=reference_urls,
                size=size,
                enable_base64_output=False,
                enable_sync_mode=True,
            )
        return await client.submit_seedream_v4_t2i(
            prompt=prompt,
            size=size,
            enable_base64_output=False,
            enable_sync_mode=True,
        )
    if model_key == "nano-banana":
        if reference_urls:
            return await client.submit_nano_banana_i2i(
                prompt=prompt,
                images=reference_urls,
                aspect_ratio=aspect_ratio,
                enable_base64_output=False,
                enable_sync_mode=True,
            )
        return await client.submit_nano_banana_t2i(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            enable_base64_output=False,
            enable_sync_mode=True,
        )
    if model_key == "nano-banana-pro":
        if reference_urls:
            return await client.submit_nano_banana_pro_i2i(
                prompt=prompt,
                images=reference_urls,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                enable_base64_output=False,
                enable_sync_mode=True,
            )
        return await client.submit_nano_banana_pro_t2i(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            enable_base64_output=False,
            enable_sync_mode=True,
        )
    raise HTTPException(status_code=400, detail="Unsupported model")


@router.post("/generations/submit", response_model=GenerationSubmitOut)
async def submit_generation(
    payload: GenerationSubmitIn,
    db: Session = Depends(db_session_dep),
    redis: Redis = Depends(redis_dep),
) -> GenerationSubmitOut:
    settings = get_settings()
    user = get_or_create_user(db, payload.telegram_id)
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": user.id})
    model = get_active_model(db, payload.model_id)
    price = get_active_price(db, model.id)
    validate_model_options(
        model.key,
        payload.size,
        payload.aspect_ratio,
        payload.resolution,
    )

    try:
        lock_acquired = await acquire_generation_lock(
            redis, user.id, settings.redis_active_generation_ttl_seconds
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Redis unavailable")

    if not lock_acquired:
        active_request = get_active_generation(db, user.id)
        if active_request:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Another generation is in progress",
                    "active_request_id": active_request.id,
                    "status": active_request.status,
                },
            )
        await release_generation_lock(redis, user.id)
        lock_acquired = await acquire_generation_lock(
            redis, user.id, settings.redis_active_generation_ttl_seconds
        )
        if not lock_acquired:
            active_id = await get_generation_lock(redis, user.id)
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Another generation is in progress",
                    "active_request_id": active_id,
                },
            )

    active_request = get_active_generation(db, user.id)
    if active_request:
        await release_generation_lock(redis, user.id)
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Another generation is in progress",
                "active_request_id": active_request.id,
                "status": active_request.status,
            },
        )

    reference_urls = [url for url in payload.reference_urls if url]
    reference_file_ids = [fid for fid in payload.reference_file_ids if fid]
    if reference_urls and not model.supports_image_to_image:
        await release_generation_lock(redis, user.id)
        raise HTTPException(status_code=400, detail="Model does not support image-to-image")
    if not reference_urls and not model.supports_text_to_image:
        await release_generation_lock(redis, user.id)
        raise HTTPException(status_code=400, detail="Model does not support text-to-image")
    if len(reference_urls) > 10:
        await release_generation_lock(redis, user.id)
        raise HTTPException(status_code=400, detail="Too many reference images")

    request = GenerationRequest(
        user_id=user.id,
        model_id=model.id,
        prompt=payload.prompt,
        status=GenerationStatus.configuring,
        references_count=len(reference_urls),
        size=payload.size,
        aspect_ratio=payload.aspect_ratio,
        cost=0,
        input_params={
            "size": payload.size,
            "aspect_ratio": payload.aspect_ratio,
            "resolution": payload.resolution,
            "reference_urls": reference_urls,
            "reference_file_ids": reference_file_ids,
        },
    )
    db.add(request)
    db.flush()

    await set_generation_lock(
        redis, user.id, request.id, settings.redis_active_generation_ttl_seconds
    )

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
            await clear_generation_lock(redis, user.id, request.id)
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
            payload.size,
            payload.aspect_ratio,
            payload.resolution,
        )
    except HTTPException:
        request.status = GenerationStatus.failed
        db.commit()
        await clear_generation_lock(redis, user.id, request.id)
        raise
    except Exception:
        request.status = GenerationStatus.failed
        db.commit()
        await clear_generation_lock(redis, user.id, request.id)
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
        await clear_generation_lock(redis, user.id, request.id)
    else:
        request.status = GenerationStatus.queued
    db.commit()
    db.refresh(request)

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
    redis: Redis = Depends(redis_dep),
) -> GenerationRequestOut:
    request = get_request_for_user(db, request_id, payload.telegram_id)

    job = db.execute(
        select(GenerationJob).where(GenerationJob.request_id == request.id)
    ).scalar_one_or_none()
    if not job or not job.provider_job_id:
        raise HTTPException(status_code=404, detail="Job not found")

    client = wavespeed_client()
    response = await client.get_prediction_result(job.provider_job_id)
    status_value = str(response.data.get("status", ""))
    outputs = normalize_outputs(response.data.get("outputs", []))

    if status_value == "completed" or (not status_value and outputs):
        add_generation_results(db, request.id, outputs)
        request.status = GenerationStatus.completed
        request.completed_at = datetime.utcnow()
        job.status = JobStatus.completed
        job.completed_at = datetime.utcnow()
        await clear_generation_lock(redis, request.user_id, request.id)
    elif status_value == "failed":
        request.status = GenerationStatus.failed
        request.completed_at = datetime.utcnow()
        job.status = JobStatus.failed
        job.completed_at = datetime.utcnow()
        job.error_message = response.message
        await clear_generation_lock(redis, request.user_id, request.id)
    else:
        request.status = GenerationStatus.running
        if not request.started_at:
            request.started_at = datetime.utcnow()
        job.status = JobStatus.running
        if not job.started_at:
            job.started_at = datetime.utcnow()

    db.commit()
    db.refresh(request)
    return GenerationRequestOut.model_validate(request)


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
