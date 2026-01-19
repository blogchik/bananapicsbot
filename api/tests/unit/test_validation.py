import pytest
from app.api.v1.endpoints.generations import validate_model_options, validate_size
from app.core.model_options import ModelParameterOptions
from fastapi import HTTPException


def test_validate_size_valid():
    validate_size("1024*1024")
    validate_size("1024x1024")
    validate_size("auto")

def test_validate_size_invalid_format():
    with pytest.raises(HTTPException) as exc:
        validate_size("invalid")
    assert exc.value.status_code == 400
    assert "Invalid size format" in str(exc.value.detail)

def test_validate_size_out_of_range():
    with pytest.raises(HTTPException) as exc:
        validate_size("100x100")
    assert exc.value.status_code == 400
    assert "Size out of range" in str(exc.value.detail)

def test_validate_model_options_supports_size():
    options = ModelParameterOptions(
        supports_size=True,
        size_options=["1024*1024"]
    )
    # Should not raise
    validate_model_options(
        options,
        size="1024*1024",
        aspect_ratio=None,
        resolution=None,
        quality=None,
        input_fidelity=None
    )

def test_validate_model_options_unsupported_param():
    options = ModelParameterOptions(
        supports_size=False
    )
    with pytest.raises(HTTPException) as exc:
        validate_model_options(
            options,
            size="1024*1024",
            aspect_ratio=None,
            resolution=None,
            quality=None,
            input_fidelity=None
        )
    assert exc.value.status_code == 400
    assert "Size not supported" in str(exc.value.detail)
