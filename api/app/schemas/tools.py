from pydantic import BaseModel, Field


class WatermarkRemoveIn(BaseModel):
    telegram_id: int = Field(..., gt=0)
    image_url: str
    output_format: str | None = None


class WatermarkRemoveOut(BaseModel):
    output_url: str
    cost: int
