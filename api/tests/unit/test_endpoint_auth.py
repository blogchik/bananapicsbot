"""Auth guards on bot-only and user-scoped endpoints."""

from types import SimpleNamespace

import pytest
from app.deps.telegram_auth import generate_internal_api_key
from app.middlewares.rate_limit import RateLimitMiddleware
from app.services import admin_auth

BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


@pytest.fixture(autouse=True)
def reset_rate_limit(client):
    """Clear the per-IP rate limiter so these tests don't trip it."""
    layer = client.app.middleware_stack
    while layer is not None:
        if isinstance(layer, RateLimitMiddleware):
            layer._hits.clear()
        layer = getattr(layer, "app", None)


@pytest.fixture
def bot_token(monkeypatch):
    settings = SimpleNamespace(bot_token=BOT_TOKEN)
    monkeypatch.setattr("app.deps.telegram_auth.get_settings", lambda: settings)
    return BOT_TOKEN


CONFIRM_BODY = {
    "telegram_id": 1,
    "stars_amount": 100000,
    "currency": "XTR",
    "telegram_charge_id": "forged",
}


@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("post", "/api/v1/payments/stars/confirm", {"json": CONFIRM_BODY}),
        ("post", "/api/v1/payments/stars/refund/some-charge", {}),
        ("post", "/api/v1/media/upload", {"files": {"file": ("a.png", b"x")}}),
    ],
)
def test_bot_only_endpoints_reject_missing_key(client, bot_token, method, path, kwargs):
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 401


def test_bot_only_endpoints_reject_wrong_key(client, bot_token):
    response = client.post(
        "/api/v1/payments/stars/confirm",
        json=CONFIRM_BODY,
        headers={"X-Internal-Api-Key": "wrong"},
    )
    assert response.status_code == 401


def test_bot_only_endpoints_accept_valid_key(client, bot_token):
    response = client.post(
        "/api/v1/payments/stars/refund/missing-charge",
        headers={"X-Internal-Api-Key": generate_internal_api_key(bot_token)},
    )
    # Passes auth; mocked DB returns no payment
    assert response.status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/tools/watermark-remove",
        "/api/v1/tools/upscale",
        "/api/v1/tools/denoise",
        "/api/v1/tools/restore",
        "/api/v1/tools/enhance",
    ],
)
def test_tools_reject_other_users_telegram_id(client, mock_telegram_user, path):
    response = client.post(
        path,
        json={"telegram_id": mock_telegram_user.id + 1, "image_url": "https://example.com/a.png"},
    )
    assert response.status_code == 403


def test_referrals_reject_other_user(client, mock_telegram_user):
    response = client.get(f"/api/v1/referrals/{mock_telegram_user.id + 1}")
    assert response.status_code == 403


def test_admin_token_rejected_when_secret_empty(monkeypatch):
    import jwt

    settings = SimpleNamespace(admin_jwt_secret="", admin_ids_list=[42])
    monkeypatch.setattr(admin_auth, "get_settings", lambda: settings)
    forged = jwt.encode({"sub": "42", "type": "admin"}, "", algorithm="HS256")
    assert admin_auth.verify_admin_token(forged) is None
