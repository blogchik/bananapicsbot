from dataclasses import dataclass, field

from app.core.constants import (
    ASPECT_RATIO_OPTIONS,
    NANO_BANANA_PRO_RESOLUTIONS,
    SIZE_OPTIONS,
)


@dataclass(frozen=True)
class ModelParameterOptions:
    supports_size: bool = False
    supports_aspect_ratio: bool = False
    supports_resolution: bool = False
    size_options: list[str] = field(default_factory=list)
    aspect_ratio_options: list[str] = field(default_factory=list)
    resolution_options: list[str] = field(default_factory=list)


MODEL_PARAMETER_OPTIONS: dict[str, ModelParameterOptions] = {
    "seedream-v4": ModelParameterOptions(
        supports_size=True,
        size_options=SIZE_OPTIONS,
    ),
    "nano-banana": ModelParameterOptions(
        supports_aspect_ratio=True,
        aspect_ratio_options=ASPECT_RATIO_OPTIONS,
    ),
    "nano-banana-pro": ModelParameterOptions(
        supports_aspect_ratio=True,
        supports_resolution=True,
        aspect_ratio_options=ASPECT_RATIO_OPTIONS,
        resolution_options=NANO_BANANA_PRO_RESOLUTIONS,
    ),
}


def get_model_parameter_options(model_key: str | None) -> ModelParameterOptions:
    if not model_key:
        return ModelParameterOptions()
    return MODEL_PARAMETER_OPTIONS.get(model_key, ModelParameterOptions())
