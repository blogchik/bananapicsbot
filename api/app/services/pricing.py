"""Centralized pricing service for generation costs.

This module provides utilities for:
- Fetching dynamic prices from Wavespeed's pricing API
- Converting USD prices to credits ($1 = 1000 credits)
- Calculating average model prices for estimated generations
- Caching pricing data to reduce API calls
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.infrastructure.logging import get_logger
from app.services.redis_client import get_redis

logger = get_logger(__name__)

# Conversion constant: $1 = 1000 credits
CREDITS_PER_USD = 1000

# Cache keys
PRICING_CACHE_PREFIX = "pricing:"
AVERAGE_PRICE_CACHE_KEY = "pricing:average"
PRICING_CACHE_TTL_SECONDS = 600  # 10 minutes


def usd_to_credits(usd_amount: float | Decimal) -> int:
    """Convert USD amount to credits.
    
    Formula: credits = usd_amount * 1000
    
    Args:
        usd_amount: Price in USD (e.g., 0.027 for seedream-v4)
    
    Returns:
        Integer credit amount (e.g., 27 credits)
    
    Examples:
        >>> usd_to_credits(0.027)
        27
        >>> usd_to_credits(0.14)
        140
        >>> usd_to_credits(0.45)
        450
    """
    if isinstance(usd_amount, float):
        usd_amount = Decimal(str(usd_amount))
    credits = (usd_amount * Decimal(str(CREDITS_PER_USD))).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(credits)


def credits_to_usd(credits_amount: int) -> Decimal:
    """Convert credits to USD amount.
    
    Formula: usd = credits / 1000
    
    Args:
        credits_amount: Credit amount (e.g., 27)
    
    Returns:
        Decimal USD amount (e.g., 0.027)
    """
    return Decimal(str(credits_amount)) / Decimal(str(CREDITS_PER_USD))


def apply_price_markup(base_price: int, markup: int = 0) -> int:
    """Apply admin-configured markup to base price.
    
    Args:
        base_price: Base price in credits from Wavespeed
        markup: Markup amount in credits to add
    
    Returns:
        Final price with markup applied
    
    Examples:
        >>> apply_price_markup(240, 40)
        280
        >>> apply_price_markup(100, 0)
        100
    """
    if markup < 0:
        markup = 0
    return base_price + markup


async def get_cached_price(cache_key: str) -> int | None:
    """Get cached price value.
    
    Args:
        cache_key: Redis cache key
    
    Returns:
        Cached price in credits, or None if not found
    """
    redis = get_redis()
    try:
        cached = await redis.get(cache_key)
        if cached:
            return int(cached)
    except Exception as exc:
        logger.warning("Pricing cache read failed", key=cache_key, error=str(exc))
    return None


async def set_cached_price(
    cache_key: str,
    price: int,
    ttl_seconds: int = PRICING_CACHE_TTL_SECONDS,
) -> None:
    """Cache price value.
    
    Args:
        cache_key: Redis cache key
        price: Price in credits
        ttl_seconds: Cache TTL in seconds
    """
    redis = get_redis()
    try:
        await redis.set(cache_key, str(price), ex=ttl_seconds)
    except Exception as exc:
        logger.warning("Pricing cache write failed", key=cache_key, error=str(exc))


def build_pricing_cache_key(
    model_id: str,
    size: str | None = None,
    aspect_ratio: str | None = None,
    resolution: str | None = None,
    quality: str | None = None,
    is_i2i: bool = False,
) -> str:
    """Build cache key for model pricing.
    
    Args:
        model_id: Full model identifier
        size: Size parameter
        aspect_ratio: Aspect ratio parameter
        resolution: Resolution parameter
        quality: Quality parameter
        is_i2i: Whether this is image-to-image mode
    
    Returns:
        Unique cache key for this parameter combination
    """
    parts = [
        PRICING_CACHE_PREFIX,
        model_id.replace("/", "_"),
        f"i2i={is_i2i}",
    ]
    if size:
        parts.append(f"size={size}")
    if aspect_ratio:
        parts.append(f"ar={aspect_ratio}")
    if resolution:
        parts.append(f"res={resolution}")
    if quality:
        parts.append(f"q={quality}")
    return ":".join(parts)


async def get_model_price_from_wavespeed(
    wavespeed_client,
    model_id: str,
    inputs: dict[str, Any] | None = None,
    markup: int = 0,
) -> int | None:
    """Fetch model price from Wavespeed pricing API.
    
    Args:
        wavespeed_client: WavespeedClient instance
        model_id: Full model identifier (e.g., "bytedance/seedream-v4")
        inputs: Optional input parameters
        markup: Markup amount in credits to add to base price
    
    Returns:
        Price in credits with markup applied, or None if fetch failed
    """
    try:
        response = await wavespeed_client.get_model_pricing(model_id, inputs)
        if response.code != 200:
            logger.warning(
                "Wavespeed pricing request failed",
                model_id=model_id,
                code=response.code,
                message=response.message,
            )
            return None
        
        unit_price = response.data.get("unit_price")
        if unit_price is None:
            logger.warning(
                "Wavespeed pricing response missing unit_price",
                model_id=model_id,
                data=response.data,
            )
            return None
        
        base_price = usd_to_credits(float(unit_price))
        return apply_price_markup(base_price, markup)
    except Exception as exc:
        logger.warning(
            "Wavespeed pricing request failed",
            model_id=model_id,
            error=str(exc),
        )
        return None


async def get_average_model_price(model_prices: list[int]) -> int:
    """Calculate average model price for estimated generations.
    
    Args:
        model_prices: List of model prices in credits
    
    Returns:
        Average price in credits, or 0 if no prices available
    """
    if not model_prices:
        return 0
    
    valid_prices = [p for p in model_prices if p > 0]
    if not valid_prices:
        return 0
    
    return int(sum(valid_prices) / len(valid_prices))


async def get_cached_average_price() -> int | None:
    """Get cached average model price.
    
    Returns:
        Cached average price, or None if not found
    """
    return await get_cached_price(AVERAGE_PRICE_CACHE_KEY)


async def set_cached_average_price(price: int) -> None:
    """Cache average model price.
    
    Args:
        price: Average price in credits
    """
    await set_cached_price(AVERAGE_PRICE_CACHE_KEY, price)
