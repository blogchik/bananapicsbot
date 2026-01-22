"""Pricing schemas."""

from pydantic import BaseModel


class GenerationPriceIn(BaseModel):
    """Request body for getting dynamic generation price."""

    telegram_id: int
    model_id: int
    size: str | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
    quality: str | None = None
    input_fidelity: str | None = None
    is_image_to_image: bool = False


class GenerationPriceOut(BaseModel):
    """Response for generation price calculation."""

    model_id: int
    model_key: str
    price_credits: int
    price_usd: float
    is_dynamic: bool = True
    cached: bool = False
