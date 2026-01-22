from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.generations import ensure_wavespeed_balance
from app.core.config import get_settings
from app.db.models import LedgerEntry
from app.deps.db import db_session_dep
from app.deps.wavespeed import wavespeed_client
from app.schemas.tools import (
    DenoiseIn,
    DenoiseOut,
    EnhanceIn,
    EnhanceOut,
    RestoreIn,
    RestoreOut,
    UpscaleIn,
    UpscaleOut,
    WatermarkRemoveIn,
    WatermarkRemoveOut,
)
from app.services.ledger import get_user_balance
from app.services.users import get_or_create_user

router = APIRouter()

# Tool pricing (credits)
WATERMARK_REMOVE_COST = 12
UPSCALE_COST = 60  # $0.06 ≈ 60 credits
DENOISE_COST = 20  # estimated
RESTORE_COST = 20  # estimated
ENHANCE_COST = 30  # estimated


@router.post("/tools/watermark-remove", response_model=WatermarkRemoveOut)
async def remove_watermark(
    payload: WatermarkRemoveIn,
    db: Session = Depends(db_session_dep),
) -> WatermarkRemoveOut:
    settings = get_settings()
    user, _, _ = get_or_create_user(db, payload.telegram_id)
    await ensure_wavespeed_balance(settings)

    balance = get_user_balance(db, user.id)
    if balance < WATERMARK_REMOVE_COST:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    entry = LedgerEntry(
        user_id=user.id,
        amount=-WATERMARK_REMOVE_COST,
        entry_type="tool_charge",
        reference_id=f"watermark_{uuid4().hex}",
        description="Watermark removal",
    )
    db.add(entry)
    db.flush()

    client = wavespeed_client()
    try:
        response = await client.submit_watermark_remover(
            image=payload.image_url,
            output_format=payload.output_format,
            enable_base64_output=False,
            enable_sync_mode=True,
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=502, detail="Wavespeed request failed")

    outputs = response.data.get("outputs")
    output_url = None
    if isinstance(outputs, list) and outputs:
        output_url = outputs[0]
    elif isinstance(outputs, str):
        output_url = outputs

    if not output_url:
        db.rollback()
        raise HTTPException(status_code=502, detail="Watermark removal failed")

    db.commit()
    return WatermarkRemoveOut(output_url=str(output_url), cost=WATERMARK_REMOVE_COST)


def _extract_output_url(response_data: dict) -> str | None:
    """Extract output URL from wavespeed response."""
    outputs = response_data.get("outputs")
    if isinstance(outputs, list) and outputs:
        return str(outputs[0])
    elif isinstance(outputs, str):
        return outputs
    return None


@router.post("/tools/upscale", response_model=UpscaleOut)
async def upscale_image(
    payload: UpscaleIn,
    db: Session = Depends(db_session_dep),
) -> UpscaleOut:
    """Upscale image to 2K, 4K, or 8K resolution."""
    settings = get_settings()
    user, _, _ = get_or_create_user(db, payload.telegram_id)
    await ensure_wavespeed_balance(settings)

    balance = get_user_balance(db, user.id)
    if balance < UPSCALE_COST:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    entry = LedgerEntry(
        user_id=user.id,
        amount=-UPSCALE_COST,
        entry_type="tool_charge",
        reference_id=f"upscale_{uuid4().hex}",
        description="Image upscaling",
    )
    db.add(entry)
    db.flush()

    client = wavespeed_client()
    try:
        response = await client.submit_upscaler(
            image=payload.image_url,
            target_resolution=payload.target_resolution,
            output_format=payload.output_format,
            enable_base64_output=False,
            enable_sync_mode=True,
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=502, detail="Wavespeed request failed")

    output_url = _extract_output_url(response.data)
    if not output_url:
        db.rollback()
        raise HTTPException(status_code=502, detail="Upscaling failed")

    db.commit()
    return UpscaleOut(output_url=output_url, cost=UPSCALE_COST)


@router.post("/tools/denoise", response_model=DenoiseOut)
async def denoise_image(
    payload: DenoiseIn,
    db: Session = Depends(db_session_dep),
) -> DenoiseOut:
    """Remove noise from image using Topaz AI."""
    settings = get_settings()
    user, _, _ = get_or_create_user(db, payload.telegram_id)
    await ensure_wavespeed_balance(settings)

    balance = get_user_balance(db, user.id)
    if balance < DENOISE_COST:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    entry = LedgerEntry(
        user_id=user.id,
        amount=-DENOISE_COST,
        entry_type="tool_charge",
        reference_id=f"denoise_{uuid4().hex}",
        description="Image denoising",
    )
    db.add(entry)
    db.flush()

    client = wavespeed_client()
    try:
        response = await client.submit_denoise(
            image=payload.image_url,
            model=payload.model,
            output_format=payload.output_format,
            enable_base64_output=False,
            enable_sync_mode=True,
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=502, detail="Wavespeed request failed")

    output_url = _extract_output_url(response.data)
    if not output_url:
        db.rollback()
        raise HTTPException(status_code=502, detail="Denoising failed")

    db.commit()
    return DenoiseOut(output_url=output_url, cost=DENOISE_COST)


@router.post("/tools/restore", response_model=RestoreOut)
async def restore_image(
    payload: RestoreIn,
    db: Session = Depends(db_session_dep),
) -> RestoreOut:
    """Restore old photos by removing dust and scratches."""
    settings = get_settings()
    user, _, _ = get_or_create_user(db, payload.telegram_id)
    await ensure_wavespeed_balance(settings)

    balance = get_user_balance(db, user.id)
    if balance < RESTORE_COST:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    entry = LedgerEntry(
        user_id=user.id,
        amount=-RESTORE_COST,
        entry_type="tool_charge",
        reference_id=f"restore_{uuid4().hex}",
        description="Image restoration",
    )
    db.add(entry)
    db.flush()

    client = wavespeed_client()
    try:
        response = await client.submit_restore(
            image=payload.image_url,
            model=payload.model,
            output_format=payload.output_format,
            enable_base64_output=False,
            enable_sync_mode=True,
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=502, detail="Wavespeed request failed")

    output_url = _extract_output_url(response.data)
    if not output_url:
        db.rollback()
        raise HTTPException(status_code=502, detail="Restoration failed")

    db.commit()
    return RestoreOut(output_url=output_url, cost=RESTORE_COST)


@router.post("/tools/enhance", response_model=EnhanceOut)
async def enhance_image(
    payload: EnhanceIn,
    db: Session = Depends(db_session_dep),
) -> EnhanceOut:
    """Enhance image quality with AI upscaling and sharpening."""
    settings = get_settings()
    user, _, _ = get_or_create_user(db, payload.telegram_id)
    await ensure_wavespeed_balance(settings)

    balance = get_user_balance(db, user.id)
    if balance < ENHANCE_COST:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    entry = LedgerEntry(
        user_id=user.id,
        amount=-ENHANCE_COST,
        entry_type="tool_charge",
        reference_id=f"enhance_{uuid4().hex}",
        description="Image enhancement",
    )
    db.add(entry)
    db.flush()

    client = wavespeed_client()
    try:
        response = await client.submit_enhance(
            image=payload.image_url,
            size=payload.size,
            model=payload.model,
            output_format=payload.output_format,
            enable_base64_output=False,
            enable_sync_mode=True,
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=502, detail="Wavespeed request failed")

    output_url = _extract_output_url(response.data)
    if not output_url:
        db.rollback()
        raise HTTPException(status_code=502, detail="Enhancement failed")

    db.commit()
    return EnhanceOut(output_url=output_url, cost=ENHANCE_COST)
