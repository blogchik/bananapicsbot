from unittest.mock import AsyncMock, MagicMock

import pytest
from app.db.models import ModelCatalog, User


@pytest.fixture
def mock_wavespeed_client(mocker):
    client = AsyncMock()
    mocker.patch("app.api.v1.endpoints.generations.wavespeed_client", return_value=client)
    return client


@pytest.fixture
def mock_service_functions(mocker):
    """Mocks the service functions called by the endpoint."""
    mock_user = User(id=1, telegram_id=123456789)
    mocker.patch("app.api.v1.endpoints.generations.get_or_create_user", return_value=(mock_user, False, False))

    # Mock get_active_model
    mock_model = ModelCatalog(
        id=1, key="seedream-v4", supports_text_to_image=True, supports_image_to_image=True, is_active=True
    )
    mocker.patch("app.api.v1.endpoints.generations.get_active_model", return_value=mock_model)

    # Mock other helpers
    mocker.patch("app.api.v1.endpoints.generations.get_generation_price", return_value=100)
    mocker.patch("app.api.v1.endpoints.generations.count_active_generations", return_value=0)
    mocker.patch("app.api.v1.endpoints.generations.trial_available", return_value=False)
    mocker.patch("app.api.v1.endpoints.generations.get_user_balance", return_value=1000)
    mocker.patch("app.api.v1.endpoints.generations.ensure_wavespeed_balance", return_value=12.0)
    # Mock validation to pass by default
    mocker.patch("app.api.v1.endpoints.generations.validate_model_options")
    # Mock options retrieval
    mocker.patch("app.api.v1.endpoints.generations.get_model_parameter_options_from_wavespeed", new_callable=AsyncMock)

    return {"user": mock_user, "model": mock_model}


@pytest.mark.asyncio
async def test_submit_generation_success(client, mock_wavespeed_client, mock_service_functions, mock_db_session):
    # Setup wavespeed mock response
    mock_response = MagicMock()
    mock_response.data = {"id": "ws-123", "outputs": []}
    mock_wavespeed_client.submit_seedream_v4_t2i.return_value = mock_response

    payload = {
        "telegram_id": 123456789,
        "model_id": 1,
        "prompt": "A beautiful sunset",
        "size": "1024*1024",
        "quality": "standard",
    }

    response = client.post("/api/v1/generations/submit", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["provider_job_id"] == "ws-123"
    assert data["trial_used"] is False

    # Check DB interactions
    assert mock_db_session.add.called
    assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_submit_generation_insufficient_funds(client, mock_service_functions, mocker):
    # Override balance mock to return 0
    mocker.patch("app.api.v1.endpoints.generations.get_user_balance", return_value=0)
    mocker.patch("app.api.v1.endpoints.generations.get_generation_price", return_value=100)

    payload = {"telegram_id": 123456789, "model_id": 1, "prompt": "Expensive creation", "size": "1024*1024"}

    response = client.post("/api/v1/generations/submit", json=payload)

    assert response.status_code == 402
    assert response.json()["error"]["message"] == "Insufficient balance"


@pytest.mark.asyncio
async def test_submit_generation_invalid_input(client, mock_service_functions):
    payload = {
        "telegram_id": 123456789,
        "model_id": 1,
        "prompt": "",  # Empty prompt
        "size": "1024*1024",
    }
    # If the Pydantic schema validates min_length, this might fail with 422.
    # If not, let's see. 'prompt' is just str in schema, so maybe valid?
    # Actually schema doesn't define min_length. Let's send missing required field.

    invalid_payload = {
        "model_id": 1
        # missing telegram_id, prompt
    }
    response = client.post("/api/v1/generations/submit", json=invalid_payload)
    assert response.status_code == 422  # Validation Error
