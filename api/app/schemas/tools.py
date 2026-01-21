from pydantic import BaseModel, Field


class WatermarkRemoveIn(BaseModel):
    telegram_id: int = Field(..., gt=0)
    image_url: str
    output_format: str | None = None


class WatermarkRemoveOut(BaseModel):
    output_url: str
    cost: int


# Ultimate Image Upscaler
class UpscaleIn(BaseModel):
    telegram_id: int = Field(..., gt=0)
    image_url: str
    target_resolution: str = "4k"  # 2k, 4k, 8k
    output_format: str | None = None


class UpscaleOut(BaseModel):
    output_url: str
    cost: int


# Topaz Denoise
class DenoiseIn(BaseModel):
    telegram_id: int = Field(..., gt=0)
    image_url: str
    model: str = "Normal"  # Normal, Strong, Extreme
    output_format: str | None = None


class DenoiseOut(BaseModel):
    output_url: str
    cost: int


# Topaz Restore
class RestoreIn(BaseModel):
    telegram_id: int = Field(..., gt=0)
    image_url: str
    model: str = "Dust-Scratch"  # Dust-Scratch, Dust-Scratch V2
    output_format: str | None = None


class RestoreOut(BaseModel):
    output_url: str
    cost: int


# Topaz Enhance
class EnhanceIn(BaseModel):
    telegram_id: int = Field(..., gt=0)
    image_url: str
    size: str = "1080*1080"  # up to 4096*4096
    model: str = "Standard V2"  # Standard V2, Low Resolution V2, CGI, High Fidelity V2, Text Refine
    output_format: str | None = None


class EnhanceOut(BaseModel):
    output_url: str
    cost: int
