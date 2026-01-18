from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.generations import ensure_wavespeed_balance
from app.core.config import get_settings
from app.db.models import LedgerEntry
from app.deps.db import db_session_dep
from app.deps.wavespeed import wavespeed_client
from app.schemas.tools import WatermarkRemoveIn, WatermarkRemoveOut
from app.services.ledger import get_user_balance
from app.services.users import get_or_create_user

router = APIRouter()

WATERMARK_REMOVE_COST = 12


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
