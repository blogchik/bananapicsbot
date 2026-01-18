from dataclasses import dataclass, field

from app.core.constants import (
    ASPECT_RATIO_OPTIONS,
    NANO_BANANA_PRO_RESOLUTIONS,
    GPT_IMAGE_1_5_SIZE_OPTIONS,
    SIZE_OPTIONS,
)


@dataclass(frozen=True)
class ModelParameterOptions:
    supports_size: bool = False
    supports_aspect_ratio: bool = False
    supports_resolution: bool = False
    supports_quality: bool = False
    supports_input_fidelity: bool = False
    quality_stars: int | None = None
    avg_duration_seconds_min: int | None = None
    avg_duration_seconds_max: int | None = None
    avg_duration_text: str | None = None
    size_options: list[str] = field(default_factory=list)
    aspect_ratio_options: list[str] = field(default_factory=list)
    resolution_options: list[str] = field(default_factory=list)
    quality_options: list[str] = field(default_factory=list)
    input_fidelity_options: list[str] = field(default_factory=list)


MODEL_PARAMETER_OPTIONS: dict[str, ModelParameterOptions] = {
    "seedream-v4": ModelParameterOptions(
        supports_resolution=True,
        quality_stars=4,
        avg_duration_seconds_min=10,
        avg_duration_seconds_max=30,
        avg_duration_text="10-30 сек",
        resolution_options=SIZE_OPTIONS,
    ),
    "nano-banana": ModelParameterOptions(
        supports_aspect_ratio=True,
        quality_stars=4,
        avg_duration_seconds_min=10,
        avg_duration_seconds_max=20,
        avg_duration_text="10-20 сек",
        aspect_ratio_options=ASPECT_RATIO_OPTIONS,
    ),
    "nano-banana-pro": ModelParameterOptions(
        supports_aspect_ratio=True,
        supports_resolution=True,
        quality_stars=5,
        avg_duration_seconds_min=60,
        avg_duration_seconds_max=120,
        avg_duration_text="1-2 мин",
        aspect_ratio_options=ASPECT_RATIO_OPTIONS,
        resolution_options=NANO_BANANA_PRO_RESOLUTIONS,
    ),
    "gpt-image-1.5": ModelParameterOptions(
        supports_size=True,
        supports_quality=True,
        supports_input_fidelity=True,
        quality_stars=5,
        avg_duration_seconds_min=20,
        avg_duration_seconds_max=60,
        avg_duration_text="20-60 sec",
        size_options=GPT_IMAGE_1_5_SIZE_OPTIONS,
        quality_options=["low", "medium", "high"],
        input_fidelity_options=["low", "high"],
    ),
}


def get_model_parameter_options(model_key: str | None) -> ModelParameterOptions:
    if not model_key:
        return ModelParameterOptions()
    return MODEL_PARAMETER_OPTIONS.get(model_key, ModelParameterOptions())
