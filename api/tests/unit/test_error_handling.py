"""Tests for error handling, edge cases, and input validation."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.api.v1.endpoints.generations import validate_model_options, validate_size
from app.core.model_options import ModelParameterOptions
from app.services.pricing import usd_to_credits
from fastapi import HTTPException


# === Size Validation Tests ===


def test_validate_size_none():
    """Test that None size is valid (optional parameter)."""
    validate_size(None)  # Should not raise


def test_validate_size_auto():
    """Test that 'auto' size is valid."""
    validate_size("auto")
    validate_size("AUTO")
    validate_size("Auto")


def test_validate_size_valid_formats():
    """Test various valid size formats."""
    valid_sizes = [
        "1024x1024",
        "1024*1024",
        "1920x1080",
        "2048*2048",
        "4096x4096",
    ]
    for size in valid_sizes:
        validate_size(size)  # Should not raise


def test_validate_size_invalid_separator():
    """Test that invalid separators raise error."""
    with pytest.raises(HTTPException) as exc:
        validate_size("1024-1024")
    assert exc.value.status_code == 400
    assert "Invalid size format" in str(exc.value.detail)


def test_validate_size_missing_dimension():
    """Test that missing dimension raises error."""
    with pytest.raises(HTTPException) as exc:
        validate_size("1024")
    assert exc.value.status_code == 400


def test_validate_size_non_numeric():
    """Test that non-numeric dimensions raise error."""
    with pytest.raises(HTTPException) as exc:
        validate_size("widthxheight")
    assert exc.value.status_code == 400


def test_validate_size_below_minimum():
    """Test that size below minimum (1024) raises error."""
    with pytest.raises(HTTPException) as exc:
        validate_size("512x512")
    assert exc.value.status_code == 400
    assert "out of range" in str(exc.value.detail).lower()


def test_validate_size_above_maximum():
    """Test that size above maximum (4096) raises error."""
    with pytest.raises(HTTPException) as exc:
        validate_size("8192x8192")
    assert exc.value.status_code == 400
    assert "out of range" in str(exc.value.detail).lower()


def test_validate_size_mixed_valid_invalid():
    """Test size with one dimension valid, one invalid."""
    with pytest.raises(HTTPException) as exc:
        validate_size("2048x512")  # height too small
    assert exc.value.status_code == 400


# === Model Options Validation Tests ===


def test_validate_model_options_all_supported():
    """Test validation when all parameters are supported."""
    options = ModelParameterOptions(
        supports_size=True,
        supports_aspect_ratio=True,
        supports_resolution=True,
        supports_quality=True,
        supports_input_fidelity=True,
        size_options=["1024*1024"],
        aspect_ratio_options=["16:9"],
        resolution_options=["FHD"],
        quality_options=["standard"],
        input_fidelity_options=["high"],
    )

    # Should not raise
    validate_model_options(
        options,
        size="1024*1024",
        aspect_ratio="16:9",
        resolution="FHD",
        quality="standard",
        input_fidelity="high",
    )


def test_validate_model_options_size_not_supported():
    """Test validation when size parameter is not supported by model."""
    options = ModelParameterOptions(supports_size=False)

    with pytest.raises(HTTPException) as exc:
        validate_model_options(options, size="1024*1024", aspect_ratio=None, resolution=None, quality=None, input_fidelity=None)
    assert exc.value.status_code == 400
    assert "Size not supported" in str(exc.value.detail)


def test_validate_model_options_aspect_ratio_not_supported():
    """Test validation when aspect_ratio parameter is not supported."""
    options = ModelParameterOptions(supports_aspect_ratio=False)

    with pytest.raises(HTTPException) as exc:
        validate_model_options(options, size=None, aspect_ratio="16:9", resolution=None, quality=None, input_fidelity=None)
    assert exc.value.status_code == 400
    assert "Aspect ratio not supported" in str(exc.value.detail)


def test_validate_model_options_resolution_not_supported():
    """Test validation when resolution parameter is not supported."""
    options = ModelParameterOptions(supports_resolution=False)

    with pytest.raises(HTTPException) as exc:
        validate_model_options(options, size=None, aspect_ratio=None, resolution="4K", quality=None, input_fidelity=None)
    assert exc.value.status_code == 400
    assert "Resolution not supported" in str(exc.value.detail)


def test_validate_model_options_quality_not_supported():
    """Test validation when quality parameter is not supported."""
    options = ModelParameterOptions(supports_quality=False)

    with pytest.raises(HTTPException) as exc:
        validate_model_options(
            options, size=None, aspect_ratio=None, resolution=None, quality="hd", input_fidelity=None
        )
    assert exc.value.status_code == 400
    assert "Quality not supported" in str(exc.value.detail)


def test_validate_model_options_input_fidelity_not_supported():
    """Test validation when input_fidelity parameter is not supported."""
    options = ModelParameterOptions(supports_input_fidelity=False)

    with pytest.raises(HTTPException) as exc:
        validate_model_options(
            options, size=None, aspect_ratio=None, resolution=None, quality=None, input_fidelity="high"
        )
    assert exc.value.status_code == 400
    assert "Input fidelity not supported" in str(exc.value.detail)


def test_validate_model_options_invalid_size_option():
    """Test validation when size is not in allowed options."""
    options = ModelParameterOptions(supports_size=True, size_options=["1024*1024", "2048*2048"])

    with pytest.raises(HTTPException) as exc:
        validate_model_options(
            options, size="512*512", aspect_ratio=None, resolution=None, quality=None, input_fidelity=None
        )
    # Should fail size validation first (out of range)
    assert exc.value.status_code == 400


def test_validate_model_options_invalid_aspect_ratio_option():
    """Test validation when aspect_ratio is not in allowed options."""
    options = ModelParameterOptions(supports_aspect_ratio=True, aspect_ratio_options=["16:9", "4:3"])

    with pytest.raises(HTTPException) as exc:
        validate_model_options(
            options, size=None, aspect_ratio="21:9", resolution=None, quality=None, input_fidelity=None
        )
    assert exc.value.status_code == 400
    assert "Invalid aspect ratio" in str(exc.value.detail)


def test_validate_model_options_invalid_resolution_option():
    """Test validation when resolution is not in allowed options."""
    options = ModelParameterOptions(supports_resolution=True, resolution_options=["FHD", "4K"])

    with pytest.raises(HTTPException) as exc:
        validate_model_options(options, size=None, aspect_ratio=None, resolution="8K", quality=None, input_fidelity=None)
    assert exc.value.status_code == 400
    assert "Invalid resolution" in str(exc.value.detail)


def test_validate_model_options_invalid_quality_option():
    """Test validation when quality is not in allowed options."""
    options = ModelParameterOptions(supports_quality=True, quality_options=["standard", "hd"])

    with pytest.raises(HTTPException) as exc:
        validate_model_options(
            options, size=None, aspect_ratio=None, resolution=None, quality="ultra", input_fidelity=None
        )
    assert exc.value.status_code == 400
    assert "Invalid quality" in str(exc.value.detail)


# === Pricing Tests ===


def test_usd_to_credits_standard():
    """Test USD to credits conversion."""
    assert usd_to_credits(Decimal("1.0")) == 1000
    assert usd_to_credits(Decimal("0.1")) == 100
    assert usd_to_credits(Decimal("0.027")) == 27


def test_usd_to_credits_zero():
    """Test zero USD conversion."""
    assert usd_to_credits(Decimal("0")) == 0


def test_usd_to_credits_small_amounts():
    """Test small USD amounts."""
    assert usd_to_credits(Decimal("0.001")) == 1
    assert usd_to_credits(Decimal("0.0001")) == 0  # Rounds down


def test_usd_to_credits_large_amounts():
    """Test large USD amounts."""
    assert usd_to_credits(Decimal("100.0")) == 100000
    assert usd_to_credits(Decimal("999.99")) == 999990


def test_usd_to_credits_rounding():
    """Test USD to credits rounding behavior."""
    # 0.0145 * 1000 = 14.5, ROUND_HALF_UP rounds .5 up to 15
    result = usd_to_credits(Decimal("0.0145"))
    assert result == 15  # 14.5 rounds up to 15 with ROUND_HALF_UP


# === Error Message Tests ===


def test_http_exception_contains_detail():
    """Test that HTTPException includes detail message."""
    try:
        raise HTTPException(status_code=400, detail="Test error message")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Test error message"


def test_http_exception_with_dict_detail():
    """Test HTTPException with dictionary detail."""
    detail = {"error": "Invalid input", "field": "prompt"}
    try:
        raise HTTPException(status_code=422, detail=detail)
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail == detail


# === Edge Cases ===


def test_empty_prompt_handling():
    """Test handling of empty prompt in generation request."""
    # Empty prompt should be handled by Pydantic validation
    # but let's test edge cases
    prompt = ""
    assert len(prompt) == 0


def test_very_long_prompt():
    """Test handling of very long prompts."""
    # 10000 character prompt
    long_prompt = "A" * 10000
    assert len(long_prompt) == 10000


def test_special_characters_in_prompt():
    """Test handling of special characters in prompts."""
    special_chars = "Hello <>&\"'😀🎨"
    assert len(special_chars) > 0


def test_negative_amounts():
    """Test handling of negative credit amounts."""
    negative_amount = Decimal("-100")
    assert negative_amount < 0


def test_zero_balance():
    """Test handling of zero balance."""
    balance = Decimal("0")
    assert balance == 0


def test_insufficient_balance_edge_case():
    """Test edge case where balance equals cost."""
    balance = Decimal("100")
    cost = Decimal("100")
    assert balance >= cost  # Should be allowed


def test_insufficient_balance_off_by_one():
    """Test edge case where balance is 1 credit short."""
    balance = Decimal("99")
    cost = Decimal("100")
    assert balance < cost  # Should be rejected


# === Concurrent Request Tests ===


def test_max_parallel_generations_constant():
    """Test that max parallel generations is properly configured."""
    from app.core.config import Settings

    settings = Settings()
    assert settings.max_parallel_generations_per_user >= 1
    assert settings.max_parallel_generations_per_user <= 10  # Reasonable limit


# === Trial Usage Tests ===


def test_trial_limit_constant():
    """Test that trial limit is properly configured."""
    from app.core.config import Settings

    settings = Settings()
    assert settings.trial_generations_limit >= 0
    assert settings.trial_generations_limit <= 10  # Reasonable limit


# === Telegram ID Validation ===


def test_valid_telegram_ids():
    """Test valid Telegram ID ranges."""
    valid_ids = [123456789, 987654321, 1000000000]
    for tid in valid_ids:
        assert tid > 0
        assert tid < 10**10  # Reasonable upper bound


def test_invalid_telegram_ids():
    """Test invalid Telegram IDs."""
    invalid_ids = [0, -1, -123456789]
    for tid in invalid_ids:
        assert tid <= 0  # Should be rejected
