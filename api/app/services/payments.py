from typing import Iterable

from app.core.config import get_settings


def parse_presets(value: str) -> list[int]:
    presets: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            amount = int(item)
        except ValueError:
            continue
        if amount > 0:
            presets.append(amount)
    return sorted(set(presets))


def calculate_credits(stars_amount: int, numerator: int, denominator: int) -> int:
    if stars_amount <= 0 or denominator <= 0:
        return 0
    return int(round(stars_amount * numerator / denominator))


def get_stars_settings() -> dict[str, object]:
    settings = get_settings()
    presets = parse_presets(settings.stars_presets)
    return {
        "enabled": settings.stars_enabled,
        "min_stars": settings.stars_min_amount,
        "presets": presets,
        "numerator": settings.stars_exchange_numerator,
        "denominator": settings.stars_exchange_denominator,
        "currency": "XTR",
    }
