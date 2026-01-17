import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.deps.db import db_session_dep
from app.core.constants import SIZE_OPTIONS
from app.core.config import get_settings
from app.core.model_options import get_model_parameter_options
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
):
    if model_key == "seedream-v4":
        if reference_urls:
            return await client.submit_seedream_v4_i2i(
                prompt=prompt,
                images=reference_urls,
                size=size,
                enable_base64_output=False,
                enable_sync_mode=False,
            )
        return await client.submit_seedream_v4_t2i(
            prompt=prompt,
            size=size,
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
    raise HTTPException(status_code=400, detail="Unsupported model")


@router.post("/generations/submit", response_model=GenerationSubmitOut)
async def submit_generation(
    payload: GenerationSubmitIn,
    db: Session = Depends(db_session_dep),
) -> GenerationSubmitOut:
    settings = get_settings()
    user, _, _ = get_or_create_user(db, payload.telegram_id)
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": user.id})
    model = get_active_model(db, payload.model_id)
    price = get_active_price(db, model.id)
    size_value = payload.size
    resolution_value = payload.resolution
    if model.key == "seedream-v4" and size_value and not resolution_value:
        resolution_value = size_value
        size_value = None
    validate_model_options(
        model.key,
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
            "reference_urls": reference_urls,
            "reference_file_ids": reference_file_ids,
            "chat_id": payload.chat_id,
            "message_id": payload.message_id,
            "prompt_message_id": payload.prompt_message_id,
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
