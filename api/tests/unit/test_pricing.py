from decimal import Decimal

import pytest
from app.api.v1.endpoints.generations import _credits_from_usd, _dynamic_price_for_model
from app.core.config import Settings


@pytest.fixture
def mock_settings():
    return Settings()

@pytest.mark.asyncio
async def test_dynamic_price_seedream(mock_settings):
    price = await _dynamic_price_for_model(
        model_key="seedream-v4",
        size="1024*1024",
        resolution=None,
        quality="standard",
        settings=mock_settings
    )
    # 0.027 * 1000 = 27
    assert price == 27

@pytest.mark.asyncio
async def test_dynamic_price_nano_banana_pro_4k(mock_settings):
    price = await _dynamic_price_for_model(
        model_key="nano-banana-pro",
        size=None,
        resolution="4K",
        quality=None,
        settings=mock_settings
    )
    # 0.24 * 1000 = 240
    assert price == 240

@pytest.mark.asyncio
async def test_dynamic_price_nano_banana_pro_default(mock_settings):
    price = await _dynamic_price_for_model(
        model_key="nano-banana-pro",
        size=None,
        resolution="FHD",
        quality=None,
        settings=mock_settings
    )
    # 0.14 * 1000 = 140
    assert price == 140

def test_credits_from_usd():
    assert _credits_from_usd(Decimal("1.0")) == 1000
    assert _credits_from_usd(Decimal("0.027")) == 27
    assert _credits_from_usd(Decimal("0.1")) == 100
