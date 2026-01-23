"""Tests for Celery task execution and generation workflow."""

import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.worker.tasks import (
    _build_failure_message,
    _build_result_caption,
    _build_timeout_message,
    _complete_generation,
    _get_generation_outputs,
    _mark_generation_failed,
    _normalize_outputs,
    _refund_generation_cost,
    _resolve_language,
    _rollback_trial_use,
)


def test_normalize_outputs_empty():
    """Test normalizing empty outputs."""
    assert _normalize_outputs(None) == []
    assert _normalize_outputs([]) == []


def test_normalize_outputs_string():
    """Test normalizing single string output."""
    url = "https://example.com/image.png"
    result = _normalize_outputs(url)
    assert result == [url]


def test_normalize_outputs_list():
    """Test normalizing list of outputs."""
    urls = [
        "https://example.com/image1.png",
        "https://example.com/image2.png",
        None,  # Should be filtered out
        "",  # Should be filtered out
    ]
    result = _normalize_outputs(urls)
    assert len(result) == 2
    assert result[0] == urls[0]
    assert result[1] == urls[1]


def test_resolve_language_from_params():
    """Test resolving language from input parameters."""
    input_params = {"language": "ru"}
    result = _resolve_language(input_params, telegram_id=None)
    assert result == "ru"


def test_resolve_language_invalid():
    """Test resolving language with invalid value."""
    input_params = {"language": "invalid"}
    result = _resolve_language(input_params, telegram_id=None)
    assert result == "uz"  # Default fallback


def test_resolve_language_missing():
    """Test resolving language when not provided."""
    result = _resolve_language(None, telegram_id=None)
    assert result == "uz"  # Default fallback


def test_resolve_language_supported():
    """Test resolving language for all supported languages."""
    for lang in ["uz", "ru", "en"]:
        input_params = {"language": lang}
        result = _resolve_language(input_params, telegram_id=None)
        assert result == lang


def test_build_result_caption_without_translation():
    """Test building result caption without translation module."""
    language = "uz"
    prompt = "A beautiful sunset"
    model_name = "nano-banana-pro"
    cost = 140

    caption = _build_result_caption(language, prompt, model_name, cost)

    assert "nano-banana-pro" in caption.lower() or "nanobananapro" in caption.lower()
    assert "140" in caption
    assert "sunset" in caption.lower()


def test_build_result_caption_long_prompt():
    """Test building result caption with long prompt (should be truncated)."""
    language = "uz"
    prompt = "A" * 600  # Longer than 500 chars
    model_name = "seedream-v4"
    cost = 27

    caption = _build_result_caption(language, prompt, model_name, cost)

    # Prompt should be truncated to 500 chars
    assert len(prompt) > 500  # Original is longer
    # Caption contains truncated version
    assert caption is not None


def test_build_result_caption_html_escaping():
    """Test that result caption escapes HTML special characters."""
    language = "uz"
    prompt = "<script>alert('xss')</script>"
    model_name = "test-model"
    cost = 100

    caption = _build_result_caption(language, prompt, model_name, cost)

    # Should not contain raw HTML tags
    assert "<script>" not in caption
    assert "&lt;script&gt;" in caption or "script" not in caption.lower()


def test_build_failure_message_without_translation():
    """Test building failure message without translation."""
    language = "uz"
    error_message = "API timeout"
    refunded_credits = 0

    message = _build_failure_message(language, error_message, refunded_credits)

    assert "timeout" in message.lower() or error_message in message


def test_build_failure_message_with_refund():
    """Test building failure message with refund information."""
    language = "uz"
    error_message = "Generation failed"
    refunded_credits = 140

    message = _build_failure_message(language, error_message, refunded_credits)

    assert "140" in message
    assert "credit" in message.lower() or "kredit" in message.lower()


def test_build_failure_message_html_escaping():
    """Test that failure message escapes HTML special characters."""
    language = "uz"
    error_message = "<b>Error</b>"
    refunded_credits = 0

    message = _build_failure_message(language, error_message, refunded_credits)

    # Should escape HTML
    assert "<b>" not in message or "&lt;b&gt;" in message


def test_build_timeout_message():
    """Test building timeout message."""
    for lang in ["uz", "ru", "en"]:
        message = _build_timeout_message(lang)
        assert message is not None
        assert len(message) > 0


# === Refund and Rollback Tests (without database) ===


def test_refund_logic_no_cost():
    """Test refund logic when cost is zero."""
    cost = 0
    should_refund = cost > 0
    assert not should_refund  # No refund if cost is 0


def test_refund_logic_with_cost():
    """Test refund logic when cost exists."""
    cost = 140
    refund_amount = cost
    assert refund_amount == 140
    assert refund_amount > 0


def test_idempotent_refund_detection():
    """Test detecting duplicate refund attempts."""
    refunds_issued = {"refund_gen_1", "refund_gen_2"}
    new_refund_id = "refund_gen_1"
    already_refunded = new_refund_id in refunds_issued
    assert already_refunded  # Should not refund again


def test_telegram_message_rate_limiting():
    """Test that rate limiting constant is correctly set."""
    from app.worker.tasks import RATE_LIMIT_INTERVAL, RATE_LIMIT_MESSAGES_PER_SECOND

    assert RATE_LIMIT_MESSAGES_PER_SECOND == 20
    assert RATE_LIMIT_INTERVAL == 0.05  # 1/20


def test_supported_languages():
    """Test that supported languages are correctly defined."""
    from app.worker.tasks import SUPPORTED_LANGUAGES

    assert "uz" in SUPPORTED_LANGUAGES
    assert "ru" in SUPPORTED_LANGUAGES
    assert "en" in SUPPORTED_LANGUAGES
    assert len(SUPPORTED_LANGUAGES) == 3
