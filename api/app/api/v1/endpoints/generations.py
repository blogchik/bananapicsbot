import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import SIZE_OPTIONS
from app.core.model_options import ModelParameterOptions
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
from app.deps.db import db_session_dep
from app.deps.telegram_auth import TelegramUserDep
from app.deps.wavespeed import wavespeed_client
from app.infrastructure.logging import get_logger
from app.schemas.generation import (
    GenerationAccessIn,
    GenerationActiveOut,
    GenerationHistoryItemOut,
    GenerationHistoryOut,
    GenerationRequestOut,
    GenerationSubmitIn,
    GenerationSubmitOut,
)
from app.schemas.pricing import GenerationPriceIn, GenerationPriceOut
from app.services.ledger import get_user_balance
from app.services.model_options import get_model_parameter_options_from_wavespeed
from app.services.pricing import (
    apply_price_markup,
    build_pricing_cache_key,
    get_cached_price,
    get_model_price_from_wavespeed,
    set_cached_price,
    usd_to_credits,
)
from app.services.redis_client import get_redis
from app.services.telegram_utils import send_telegram_message_async
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
    quality: str | None,
    input_fidelity: str | None,
) -> None:
    if size and not options.supports_size:
        raise HTTPException(status_code=400, detail="Size not supported")
    if aspect_ratio and not options.supports_aspect_ratio:
        raise HTTPException(status_code=400, detail="Aspect ratio not supported")
    if resolution and not options.supports_resolution:
        raise HTTPException(status_code=400, detail="Resolution not supported")
    if quality and not options.supports_quality:
        raise HTTPException(status_code=400, detail="Quality not supported")
    if input_fidelity and not options.supports_input_fidelity:
        raise HTTPException(status_code=400, detail="Input fidelity not supported")
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
    if quality and options.quality_options:
        if quality not in options.quality_options:
            raise HTTPException(status_code=400, detail="Invalid quality")
    if input_fidelity and options.input_fidelity_options:
        if input_fidelity not in options.input_fidelity_options:
            raise HTTPException(status_code=400, detail="Invalid input fidelity")


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
    """Convert USD to credits. Deprecated: use usd_to_credits from pricing module."""
    return usd_to_credits(value)


_GPT_IMAGE_1_5_T2I_PRICES: dict[str, dict[str, int]] = {
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
_GPT_IMAGE_1_5_I2I_PRICES: dict[str, dict[str, int]] = {
    "low": {
        "1024*1024": 9000,
        "1024*1536": 34000,
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
    return int((Decimal(value) / Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _normalize_gpt_image_size(size: str | None) -> str:
    if not size:
        return "1024*1024"
    normalized = size.lower().replace("x", "*")
    if normalized == "auto":
        return "1024*1024"
    return normalized


def _get_gpt_image_prices(is_image_to_image: bool) -> dict[str, dict[str, int]]:
    return _GPT_IMAGE_1_5_I2I_PRICES if is_image_to_image else _GPT_IMAGE_1_5_T2I_PRICES


async def _dynamic_price_for_model(
    model_key: str | None,
    size: str | None,
    resolution: str | None,
    quality: str | None,
    settings,
    is_image_to_image: bool = False,
    aspect_ratio: str | None = None,
) -> int | None:
    """Get dynamic price for model using Wavespeed pricing API.

    Fetches real-time pricing from Wavespeed's pricing endpoint and converts
    USD to credits using the formula: $1 = 1000 credits.

    Applies admin-configured markup from settings.generation_price_markup.

    Falls back to hardcoded prices if API is unavailable.
    """
    if not model_key:
        return None
    key = model_key.strip().lower().replace("_", "-").replace(" ", "-")

    # Get markup from settings
    markup = settings.generation_price_markup

    # Build cache key for this pricing request
    cache_key = build_pricing_cache_key(
        model_id=key,
        size=size,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        quality=quality,
        is_i2i=is_image_to_image,
    )

    # Check cache first (cache contains prices with markup already applied)
    cached_price = await get_cached_price(cache_key)
    if cached_price is not None:
        return cached_price

    # Map model key to Wavespeed model ID
    model_id_map = {
        "seedream-v4": "bytedance/seedream-v4" if not is_image_to_image else "bytedance/seedream-v4/edit",
        "nano-banana": "google/nano-banana/text-to-image" if not is_image_to_image else "google/nano-banana/edit",
        "nano-banana-pro": "google/nano-banana-pro/text-to-image"
        if not is_image_to_image
        else "google/nano-banana-pro/edit",
        "gpt-image-1.5": "openai/gpt-image-1.5/text-to-image" if not is_image_to_image else "openai/gpt-image-1.5/edit",
    }

    wavespeed_model_id = model_id_map.get(key)
    if wavespeed_model_id:
        # Build inputs for pricing request
        inputs: dict[str, object] = {"prompt": "test"}
        if size:
            inputs["size"] = size
        if aspect_ratio:
            inputs["aspect_ratio"] = aspect_ratio
        if resolution:
            inputs["resolution"] = resolution
        if quality:
            inputs["quality"] = quality

        # Try fetching from Wavespeed pricing API (with markup)
        try:
            client = wavespeed_client()
            price = await get_model_price_from_wavespeed(client, wavespeed_model_id, inputs, markup)
            if price is not None:
                await set_cached_price(cache_key, price)
                return price
        except Exception as exc:
            # Log and fall through to hardcoded prices
            logger.debug(
                "Wavespeed pricing API unavailable, using fallback",
                model_key=key,
                error=str(exc),
            )

    # Fallback to hardcoded prices if API fails (apply markup to fallbacks too)
    if key == "seedream-v4":
        base_price = usd_to_credits(Decimal("0.027"))
        price = apply_price_markup(base_price, markup)
        await set_cached_price(cache_key, price)
        return price
    if key == "nano-banana":
        base_price = usd_to_credits(Decimal("0.038"))
        price = apply_price_markup(base_price, markup)
        await set_cached_price(cache_key, price)
        return price
    if key == "nano-banana-pro":
        res = (resolution or "").lower()
        usd = Decimal("0.24") if res == "4k" else Decimal("0.14")
        base_price = usd_to_credits(usd)
        price = apply_price_markup(base_price, markup)
        await set_cached_price(cache_key, price)
        return price
    if key == "gpt-image-1.5":
        size_value = _normalize_gpt_image_size(size)
        quality_value = (quality or "medium").lower()
        prices = _get_gpt_image_prices(is_image_to_image)
        quality_prices = prices.get(quality_value) or prices.get("medium") or _GPT_IMAGE_1_5_T2I_PRICES["medium"]
        price_units = (
            quality_prices.get(size_value)
            or quality_prices.get("1024*1024")
            or _GPT_IMAGE_1_5_T2I_PRICES["medium"]["1024*1024"]
        )
        base_price = _credits_from_price_units(int(price_units))
        price = apply_price_markup(base_price, markup)
        await set_cached_price(cache_key, price)
        return price
    return None


async def get_generation_price(
    db: Session,
    model: ModelCatalog,
    size: str | None,
    resolution: str | None,
    quality: str | None,
    settings,
    is_image_to_image: bool = False,
    aspect_ratio: str | None = None,
) -> int:
    """Get generation price for a model with given parameters.

    Tries to get dynamic price from Wavespeed pricing API first,
    falls back to database price if not available.

    Applies admin-configured markup from settings.generation_price_markup.
    """
    dynamic_price = await _dynamic_price_for_model(
        model.key, size, resolution, quality, settings, is_image_to_image, aspect_ratio
    )
    if dynamic_price is not None:
        return dynamic_price

    # Fallback to database price if dynamic pricing unavailable
    price = db.execute(
        select(ModelPrice)
        .where(ModelPrice.model_id == model.id, ModelPrice.is_active.is_(True))
        .order_by(ModelPrice.created_at.desc())
    ).scalar_one_or_none()
    if not price:
        raise HTTPException(status_code=400, detail="Model price not found")

    # Apply markup to database price as well
    base_price = int(price.unit_price)
    markup = settings.generation_price_markup
    return apply_price_markup(base_price, markup)


@router.get("/generations", response_model=GenerationHistoryOut)
async def list_generations(
    tg_user: TelegramUserDep,
    telegram_id: int = Query(..., gt=0),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session_dep),
) -> GenerationHistoryOut:
    """List user's generation history with results.
    Protected by Telegram initData authentication.
    """
    # Ensure user can only access their own generations
    if telegram_id != tg_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access generations for another user",
        )

    user = get_user_by_telegram_id(db, telegram_id)
    if not user:
        return GenerationHistoryOut(items=[], total=0, limit=limit, offset=offset)

    # Get total count
    total_count = db.execute(
        select(func.count()).select_from(GenerationRequest).where(GenerationRequest.user_id == user.id)
    ).scalar_one()

    # Get generations with model info, ordered by newest first
    requests = (
        db.execute(
            select(GenerationRequest)
            .where(GenerationRequest.user_id == user.id)
            .order_by(GenerationRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    items = []
    for req in requests:
        # Get model info
        model = db.execute(select(ModelCatalog).where(ModelCatalog.id == req.model_id)).scalar_one_or_none()
        model_key = model.key if model else "unknown"
        model_name = model.name if model else "Unknown"

        # Get results (image URLs)
        results = db.execute(select(GenerationResult).where(GenerationResult.request_id == req.id)).scalars().all()
        result_urls = [r.image_url for r in results if r.image_url]

        # Get references (input images for i2i)
        references = (
            db.execute(select(GenerationReference).where(GenerationReference.request_id == req.id)).scalars().all()
        )
        reference_urls = [r.url for r in references if r.url]

        # Determine mode (t2i or i2i)
        mode = "i2i" if req.references_count > 0 or reference_urls else "t2i"

        # Get error message if failed
        error_message = None
        if req.status == GenerationStatus.failed:
            job = db.execute(select(GenerationJob).where(GenerationJob.request_id == req.id)).scalar_one_or_none()
            if job and job.error_message:
                error_message = job.error_message

        # Get params from input_params
        input_params = req.input_params or {}
        resolution = input_params.get("resolution")
        quality = input_params.get("quality")

        items.append(
            GenerationHistoryItemOut(
                id=req.id,
                public_id=req.public_id,
                prompt=req.prompt,
                status=req.status.value if hasattr(req.status, "value") else str(req.status),
                mode=mode,
                model_key=model_key,
                model_name=model_name,
                aspect_ratio=req.aspect_ratio,
                size=req.size,
                resolution=resolution,
                quality=quality,
                cost=req.cost,
                result_urls=result_urls,
                reference_urls=reference_urls,
                error_message=error_message,
                created_at=req.created_at,
                completed_at=req.completed_at,
            )
        )

    return GenerationHistoryOut(items=items, total=int(total_count), limit=limit, offset=offset)


@router.post("/generations/price", response_model=GenerationPriceOut)
async def calculate_generation_price(
    payload: GenerationPriceIn,
    tg_user: TelegramUserDep,
    db: Session = Depends(db_session_dep),
) -> GenerationPriceOut:
    """Get dynamic generation price from Wavespeed pricing API.
    Protected by Telegram initData authentication.
    """
    # Ensure user can only get prices for themselves
    if payload.telegram_id != tg_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot get price for another user",
        )

    settings = get_settings()
    markup = settings.generation_price_markup

    # Rate limiting: 60 requests per minute per user
    redis = await get_redis()
    rate_key = f"rate_limit:price:{payload.telegram_id}"
    current = await redis.incr(rate_key)
    if current == 1:
        await redis.expire(rate_key, 60)

    if current > 60:
        logger.warning("Rate limit exceeded", user_id=payload.telegram_id, count=current)
        raise HTTPException(status_code=429, detail="Too many pricing requests. Please wait a moment.")

    # Get model from database
    model = db.execute(
        select(ModelCatalog).where(ModelCatalog.id == payload.model_id, ModelCatalog.is_active.is_(True))
    ).scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    logger.info(
        "Calculating generation price",
        model_id=payload.model_id,
        model_key=model.key,
        size=payload.size,
        aspect_ratio=payload.aspect_ratio,
        resolution=payload.resolution,
        quality=payload.quality,
        is_i2i=payload.is_image_to_image,
        markup=markup,
    )

    # Build cache key
    cache_key = build_pricing_cache_key(
        model_id=model.key,
        size=payload.size,
        aspect_ratio=payload.aspect_ratio,
        resolution=payload.resolution,
        quality=payload.quality,
        is_i2i=payload.is_image_to_image,
    )

    # Check cache first (cache already contains markup)
    cached_price = await get_cached_price(cache_key)
    if cached_price is not None:
        price_usd = float(cached_price) / 1000
        logger.info(
            "Using cached price",
            model_key=model.key,
            price_credits=cached_price,
            price_usd=price_usd,
            cache_key=cache_key,
        )
        return GenerationPriceOut(
            model_id=model.id,
            model_key=model.key,
            price_credits=cached_price,
            price_usd=price_usd,
            is_dynamic=True,
            cached=True,
        )

    # Try to get price from Wavespeed pricing API
    wavespeed_model_id = _get_wavespeed_model_id(model.key, payload.is_image_to_image)
    price_credits = None
    price_usd = None

    if wavespeed_model_id:
        # Build inputs for pricing request
        inputs: dict[str, object] = {"prompt": "test"}
        if payload.size:
            inputs["size"] = payload.size
        if payload.aspect_ratio:
            inputs["aspect_ratio"] = payload.aspect_ratio
        if payload.resolution:
            inputs["resolution"] = payload.resolution
        if payload.quality:
            inputs["quality"] = payload.quality
        if payload.input_fidelity:
            inputs["input_fidelity"] = payload.input_fidelity

        try:
            client = wavespeed_client()
            response = await client.get_model_pricing(wavespeed_model_id, inputs)

            if response.code == 200 and response.data:
                price_usd = float(response.data.get("unit_price", 0))
                base_price = usd_to_credits(price_usd)
                price_credits = apply_price_markup(base_price, markup)

                logger.info(
                    "Got price from Wavespeed API",
                    model_key=model.key,
                    wavespeed_model_id=wavespeed_model_id,
                    inputs=inputs,
                    base_price_usd=price_usd,
                    base_price_credits=base_price,
                    markup=markup,
                    final_price_credits=price_credits,
                )

                # Update price_usd to reflect final price with markup
                price_usd = float(price_credits) / 1000

                # Cache the price (with markup included)
                await set_cached_price(cache_key, price_credits)
            else:
                logger.warning(
                    "Wavespeed pricing API returned error",
                    model_key=model.key,
                    code=response.code,
                    message=response.message,
                )
        except Exception as exc:
            logger.warning(
                "Failed to get price from Wavespeed API",
                model_key=model.key,
                error=str(exc),
            )

    # Fallback to hardcoded prices if API failed (markup applied in _get_fallback_price)
    if price_credits is None:
        price_credits = await _get_fallback_price(
            model.key,
            payload.size,
            payload.resolution,
            payload.quality,
            payload.is_image_to_image,
            markup,
        )
        price_usd = float(price_credits) / 1000

        logger.info(
            "Using fallback price",
            model_key=model.key,
            price_credits=price_credits,
            price_usd=price_usd,
            markup=markup,
        )

    if price_credits is None:
        raise HTTPException(status_code=400, detail="Unable to calculate price")

    return GenerationPriceOut(
        model_id=model.id,
        model_key=model.key,
        price_credits=price_credits,
        price_usd=price_usd,
        is_dynamic=True,
        cached=False,
    )


def _get_wavespeed_model_id(model_key: str, is_image_to_image: bool = False) -> str | None:
    """Map model key to Wavespeed model ID."""
    key = model_key.strip().lower().replace("_", "-").replace(" ", "-")
    model_id_map = {
        "seedream-v4": "bytedance/seedream-v4" if not is_image_to_image else "bytedance/seedream-v4/edit",
        "nano-banana": "google/nano-banana/text-to-image" if not is_image_to_image else "google/nano-banana/edit",
        "nano-banana-pro": "google/nano-banana-pro/text-to-image"
        if not is_image_to_image
        else "google/nano-banana-pro/edit",
        "gpt-image-1.5": "openai/gpt-image-1.5/text-to-image" if not is_image_to_image else "openai/gpt-image-1.5/edit",
    }
    return model_id_map.get(key)


async def _get_fallback_price(
    model_key: str,
    size: str | None,
    resolution: str | None,
    quality: str | None,
    is_image_to_image: bool = False,
    markup: int = 0,
) -> int | None:
    """Get fallback price if Wavespeed API is unavailable.

    Args:
        model_key: Model key identifier
        size: Size parameter
        resolution: Resolution parameter
        quality: Quality parameter
        is_image_to_image: Whether this is image-to-image mode
        markup: Markup amount in credits to add to base price

    Returns:
        Final price with markup applied, or None if model not recognized
    """
    key = model_key.strip().lower().replace("_", "-").replace(" ", "-")
    res = (resolution or "").strip().lower()
    if res in {"4k", "4096", "4096x4096", "4096*4096"}:
        res = "4k"

    if key == "seedream-v4":
        base_price = usd_to_credits(Decimal("0.027"))
        return apply_price_markup(base_price, markup)
    if key == "nano-banana":
        base_price = usd_to_credits(Decimal("0.038"))
        return apply_price_markup(base_price, markup)
    if key == "nano-banana-pro":
        usd = Decimal("0.24") if res == "4k" else Decimal("0.14")
        base_price = usd_to_credits(usd)
        return apply_price_markup(base_price, markup)
    if key == "gpt-image-1.5":
        size_value = _normalize_gpt_image_size(size)
        quality_value = (quality or "medium").lower()
        prices = _get_gpt_image_prices(is_image_to_image)
        quality_prices = prices.get(quality_value) or prices.get("medium") or _GPT_IMAGE_1_5_T2I_PRICES["medium"]
        price_units = (
            quality_prices.get(size_value)
            or quality_prices.get("1024*1024")
            or _GPT_IMAGE_1_5_T2I_PRICES["medium"]["1024*1024"]
        )
        base_price = _credits_from_price_units(int(price_units))
        return apply_price_markup(base_price, markup)
    return None


def trial_available(db: Session, user_id: int) -> bool:
    trial = db.execute(select(TrialUse).where(TrialUse.user_id == user_id)).scalar_one_or_none()
    return trial is None


def get_active_generation(db: Session, user_id: int) -> GenerationRequest | None:
    active_statuses = [
        GenerationStatus.pending,
        GenerationStatus.configuring,
        GenerationStatus.queued,
        GenerationStatus.running,
    ]
    return db.execute(
        select(GenerationRequest)
        .where(
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


def get_request_for_user(db: Session, request_id: int, telegram_id: int) -> GenerationRequest:
    request = db.execute(select(GenerationRequest).where(GenerationRequest.id == request_id)).scalar_one_or_none()
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

    text = f"Wavespeed balance low. balance={balance:.4f} threshold={threshold:.4f}. Generations paused."
    for admin_id in settings.admin_ids_list:
        try:
            await send_telegram_message_async(
                bot_token=settings.bot_token,
                chat_id=admin_id,
                text=text,
                parse_mode="HTML",
                timeout=10.0,
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
    trial = db.execute(select(TrialUse).where(TrialUse.request_id == request_id)).scalar_one_or_none()
    if trial:
        db.delete(trial)


def add_generation_results(db: Session, request_id: int, outputs: list[str] | str | None) -> None:
    normalized = normalize_outputs(outputs)
    if not normalized:
        return
    existing = set(
        db.execute(select(GenerationResult.image_url).where(GenerationResult.request_id == request_id)).scalars().all()
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
    if model_key == "qwen":
        qwen_size = size or resolution
        if reference_urls:
            return await client.submit_qwen_i2i(
                prompt=prompt,
                images=reference_urls,
                size=qwen_size,
                enable_base64_output=False,
                enable_sync_mode=False,
            )
        return await client.submit_qwen_t2i(
            prompt=prompt,
            size=qwen_size,
            enable_base64_output=False,
            enable_sync_mode=False,
        )
    raise HTTPException(status_code=400, detail="Unsupported model")


@router.post("/generations/submit", response_model=GenerationSubmitOut)
async def submit_generation(
    payload: GenerationSubmitIn,
    tg_user: TelegramUserDep,
    db: Session = Depends(db_session_dep),
) -> GenerationSubmitOut:
    """Submit a new generation request.
    Protected by Telegram initData authentication.
    """
    # Ensure user can only submit for themselves
    if payload.telegram_id != tg_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot submit generation for another user",
        )

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
    reference_urls = [url for url in payload.reference_urls if url]
    reference_file_ids = [fid for fid in payload.reference_file_ids if fid]
    price = await get_generation_price(
        db,
        model,
        size_value,
        resolution_value,
        payload.quality,
        settings,
        is_image_to_image=bool(reference_urls),
        aspect_ratio=payload.aspect_ratio,
    )
    model_options = await get_model_parameter_options_from_wavespeed(model.key)
    validate_model_options(
        model_options,
        size_value,
        payload.aspect_ratio,
        resolution_value,
        payload.quality,
        payload.input_fidelity,
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
        db.add(GenerationReference(request_id=request.id, url=url, telegram_file_id=file_id))

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
    tg_user: TelegramUserDep,
    telegram_id: int = Query(..., gt=0),
    db: Session = Depends(db_session_dep),
) -> GenerationActiveOut:
    """Get active generation status.
    Protected by Telegram initData authentication.
    """
    # Ensure user can only check their own generations
    if telegram_id != tg_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access generations for another user",
        )

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
    tg_user: TelegramUserDep,
    telegram_id: int = Query(..., gt=0),
    db: Session = Depends(db_session_dep),
) -> GenerationRequestOut:
    """Get generation request details.
    Protected by Telegram initData authentication.
    """
    # Ensure user can only access their own generations
    if telegram_id != tg_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access generation for another user",
        )

    request = get_request_for_user(db, request_id, telegram_id)
    return GenerationRequestOut.model_validate(request)


@router.post("/generations/{request_id}/refresh", response_model=GenerationRequestOut)
async def refresh_generation(
    request_id: int,
    payload: GenerationAccessIn,
    tg_user: TelegramUserDep,
    db: Session = Depends(db_session_dep),
) -> GenerationRequestOut:
    """Refresh generation status from provider.
    Protected by Telegram initData authentication.
    """
    # Ensure user can only refresh their own generations
    if payload.telegram_id != tg_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot refresh generation for another user",
        )

    request = get_request_for_user(db, request_id, payload.telegram_id)

    job = db.execute(select(GenerationJob).where(GenerationJob.request_id == request.id)).scalar_one_or_none()
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
        request_out = request_out.model_copy(update={"error_message": job.error_message})
    return request_out


@router.get("/generations/{request_id}/results")
async def get_generation_results(
    request_id: int,
    tg_user: TelegramUserDep,
    telegram_id: int = Query(..., gt=0),
    db: Session = Depends(db_session_dep),
) -> list[str]:
    """Get generation result images.
    Protected by Telegram initData authentication.
    """
    # Ensure user can only access their own generation results
    if telegram_id != tg_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access generation results for another user",
        )

    request = get_request_for_user(db, request_id, telegram_id)
    results = db.execute(select(GenerationResult).where(GenerationResult.request_id == request.id)).scalars().all()
    return [result.image_url for result in results if result.image_url]


@router.get("/sizes")
async def list_sizes() -> list[str]:
    return SIZE_OPTIONS
