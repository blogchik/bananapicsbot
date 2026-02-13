"""HTTP API client with connection pooling and retry logic."""

import asyncio
import hashlib
import hmac
from dataclasses import dataclass
from typing import Any

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from core.exceptions import APIConnectionError, APIError
from core.logging import get_logger

logger = get_logger(__name__)


def generate_internal_api_key(bot_token: str) -> str:
    """
    Generate internal API key from bot token.
    This key is used for bot-to-API authentication.
    Must match the algorithm in api/app/deps/telegram_auth.py.
    """
    secret = hmac.new(b"InternalApiKey", bot_token.encode(), hashlib.sha256).hexdigest()
    return secret


@dataclass
class TrialStatus:
    """Trial status response."""

    trial_available: bool
    used_count: int


@dataclass
class GenerationResult:
    """Generation submit result."""

    request_id: int
    public_id: str | None
    status: str
    trial_used: bool
    cost: int | None


class ApiClient:
    """
    HTTP API client with connection pooling.

    Features:
    - Connection pooling for better performance
    - Automatic retry on transient failures
    - Proper resource cleanup
    - Structured logging
    - Internal API key authentication for bot-to-API calls
    """

    def __init__(
        self,
        base_url: str,
        timeout_seconds: int = 180,
        max_connections: int = 100,
        retry_attempts: int = 3,
        bot_token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = ClientTimeout(total=timeout_seconds)
        self.max_connections = max_connections
        self.retry_attempts = retry_attempts
        self._session: ClientSession | None = None
        self._connector: TCPConnector | None = None
        self._internal_api_key: str | None = None
        if bot_token:
            self._internal_api_key = generate_internal_api_key(bot_token)

    async def _get_session(self) -> ClientSession:
        """Get or create HTTP session with connection pooling."""
        if self._session is None or self._session.closed:
            self._connector = TCPConnector(
                limit=self.max_connections,
                limit_per_host=50,
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
            )
            self._session = ClientSession(
                timeout=self.timeout,
                connector=self._connector,
            )
        return self._session

    async def close(self) -> None:
        """Close HTTP session and connector."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None
        if self._connector is not None and not self._connector.closed:
            await self._connector.close()
            self._connector = None

    def _get_auth_headers(self, telegram_user_id: int | None = None) -> dict[str, str]:
        """Get authentication headers for internal API calls."""
        headers: dict[str, str] = {}
        if self._internal_api_key and telegram_user_id is not None:
            headers["X-Internal-Api-Key"] = self._internal_api_key
            headers["X-Telegram-User-Id"] = str(telegram_user_id)
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        retry: bool = True,
        telegram_user_id: int | None = None,
    ) -> Any:
        """Make HTTP request with retry logic and optional authentication."""
        url = f"{self.base_url}{path}"
        attempts = self.retry_attempts if retry else 1
        last_error: Exception | None = None
        headers = self._get_auth_headers(telegram_user_id)

        for attempt in range(attempts):
            try:
                session = await self._get_session()
                async with session.request(method, url, json=json, headers=headers or None) as resp:
                    if resp.status >= 400:
                        if resp.content_type == "application/json":
                            data = await resp.json()
                        else:
                            data = await resp.text()
                        raise APIError(resp.status, data)

                    if resp.content_type == "application/json":
                        return await resp.json()
                    return await resp.text()

            except APIError:
                raise
            except aiohttp.ClientError as e:
                last_error = e
                logger.warning(
                    "API request failed",
                    url=url,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
            except Exception as e:
                last_error = e
                logger.error(
                    "Unexpected API error",
                    url=url,
                    error=str(e),
                    exc_info=True,
                )
                if attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))

        raise APIConnectionError(str(last_error) if last_error else "Connection failed")

    async def _upload(
        self,
        path: str,
        file_bytes: bytes,
        filename: str,
    ) -> Any:
        """Upload file to API."""
        url = f"{self.base_url}{path}"
        data = aiohttp.FormData()
        data.add_field("file", file_bytes, filename=filename)

        try:
            session = await self._get_session()
            async with session.post(url, data=data) as resp:
                if resp.status >= 400:
                    if resp.content_type == "application/json":
                        payload = await resp.json()
                    else:
                        payload = await resp.text()
                    raise APIError(resp.status, payload)
                return await resp.json()
        except APIError:
            raise
        except Exception as e:
            raise APIConnectionError(str(e))

    # User endpoints
    async def sync_user(
        self,
        telegram_id: int,
        referral_code: str | None = None,
    ) -> dict:
        """Sync user with API."""
        payload = {"telegram_id": telegram_id}
        if referral_code:
            payload["referral_code"] = referral_code
        return await self._request("POST", "/api/v1/users/sync", json=payload, telegram_user_id=telegram_id)

    async def check_user_ban(self, telegram_id: int) -> dict | None:
        """Check if user is banned."""
        try:
            data = await self._request(
                "GET",
                f"/api/v1/users/{telegram_id}/ban-status",
                telegram_user_id=telegram_id,
            )
            return data
        except Exception:
            return None

    async def get_balance(self, telegram_id: int) -> int:
        """Get user balance."""
        data = await self._request("GET", f"/api/v1/users/{telegram_id}/balance", telegram_user_id=telegram_id)
        return int(data["balance"])

    async def get_trial(self, telegram_id: int) -> TrialStatus:
        """Get user trial status."""
        data = await self._request("GET", f"/api/v1/users/{telegram_id}/trial", telegram_user_id=telegram_id)
        return TrialStatus(
            trial_available=bool(data["trial_available"]),
            used_count=int(data["used_count"]),
        )

    # Model endpoints
    async def get_models(self) -> list[dict]:
        """Get available models."""
        return await self._request("GET", "/api/v1/models")

    async def get_sizes(self) -> list[str]:
        """Get available sizes."""
        return await self._request("GET", "/api/v1/sizes")

    # Generation endpoints
    async def submit_generation(
        self,
        telegram_id: int,
        model_id: int,
        prompt: str,
        size: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        quality: str | None = None,
        input_fidelity: str | None = None,
        language: str | None = None,
        reference_urls: list[str] | None = None,
        reference_file_ids: list[str] | None = None,
        chat_id: int | None = None,
        message_id: int | None = None,
        prompt_message_id: int | None = None,
    ) -> dict:
        """Submit generation request."""
        payload: dict[str, object] = {
            "telegram_id": telegram_id,
            "model_id": model_id,
            "prompt": prompt,
            "size": size,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "quality": quality,
            "input_fidelity": input_fidelity,
            "reference_urls": reference_urls or [],
            "reference_file_ids": reference_file_ids or [],
        }
        if language:
            payload["language"] = language
        if chat_id is not None:
            payload["chat_id"] = chat_id
        if message_id is not None:
            payload["message_id"] = message_id
        if prompt_message_id is not None:
            payload["prompt_message_id"] = prompt_message_id
        return await self._request(
            "POST",
            "/api/v1/generations/submit",
            json=payload,
            telegram_user_id=telegram_id,
        )

    async def get_generation_price(
        self,
        telegram_id: int,
        model_id: int,
        size: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        quality: str | None = None,
        input_fidelity: str | None = None,
        is_image_to_image: bool = False,
    ) -> dict:
        """Get dynamic generation price from API."""
        return await self._request(
            "POST",
            "/api/v1/generations/price",
            json={
                "telegram_id": telegram_id,
                "model_id": model_id,
                "size": size,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "quality": quality,
                "input_fidelity": input_fidelity,
                "is_image_to_image": is_image_to_image,
            },
            telegram_user_id=telegram_id,
        )

    async def refresh_generation(
        self,
        request_id: int,
        telegram_id: int,
    ) -> dict:
        """Refresh generation status."""
        return await self._request(
            "POST",
            f"/api/v1/generations/{request_id}/refresh",
            json={"telegram_id": telegram_id},
            telegram_user_id=telegram_id,
        )

    async def get_generation_results(
        self,
        request_id: int,
        telegram_id: int,
    ) -> list[str]:
        """Get generation results."""
        return await self._request(
            "GET",
            f"/api/v1/generations/{request_id}/results?telegram_id={telegram_id}",
            telegram_user_id=telegram_id,
        )

    async def get_active_generation(self, telegram_id: int) -> dict:
        """Check for active generation."""
        return await self._request(
            "GET",
            f"/api/v1/generations/active?telegram_id={telegram_id}",
            telegram_user_id=telegram_id,
        )

    # Media endpoints
    async def upload_media(self, file_bytes: bytes, filename: str) -> str:
        """Upload media file."""
        data = await self._upload("/api/v1/media/upload", file_bytes, filename)
        return str(data.get("download_url", ""))

    async def remove_watermark(self, telegram_id: int, image_url: str) -> dict:
        """Remove watermark from image."""
        return await self._request(
            "POST",
            "/api/v1/tools/watermark-remove",
            json={"telegram_id": telegram_id, "image_url": image_url},
            telegram_user_id=telegram_id,
        )

    async def upscale_image(self, telegram_id: int, image_url: str, target_resolution: str = "4k") -> dict:
        """Upscale image to higher resolution."""
        return await self._request(
            "POST",
            "/api/v1/tools/upscale",
            json={
                "telegram_id": telegram_id,
                "image_url": image_url,
                "target_resolution": target_resolution,
            },
            telegram_user_id=telegram_id,
        )

    async def denoise_image(self, telegram_id: int, image_url: str, model: str = "Normal") -> dict:
        """Remove noise from image."""
        return await self._request(
            "POST",
            "/api/v1/tools/denoise",
            json={
                "telegram_id": telegram_id,
                "image_url": image_url,
                "model": model,
            },
            telegram_user_id=telegram_id,
        )

    async def restore_image(self, telegram_id: int, image_url: str, model: str = "Dust-Scratch") -> dict:
        """Restore old photo by removing dust and scratches."""
        return await self._request(
            "POST",
            "/api/v1/tools/restore",
            json={
                "telegram_id": telegram_id,
                "image_url": image_url,
                "model": model,
            },
            telegram_user_id=telegram_id,
        )

    async def enhance_image(
        self,
        telegram_id: int,
        image_url: str,
        size: str = "1080*1080",
        model: str = "Standard V2",
    ) -> dict:
        """Enhance image with AI upscaling and sharpening."""
        return await self._request(
            "POST",
            "/api/v1/tools/enhance",
            json={
                "telegram_id": telegram_id,
                "image_url": image_url,
                "size": size,
                "model": model,
            },
            telegram_user_id=telegram_id,
        )

    # Payment endpoints
    async def get_stars_options(self) -> dict:
        """Get stars payment options."""
        return await self._request("GET", "/api/v1/payments/stars/options")

    async def confirm_stars_payment(
        self,
        telegram_id: int,
        stars_amount: int,
        currency: str,
        telegram_charge_id: str,
        provider_charge_id: str | None = None,
        invoice_payload: str | None = None,
    ) -> dict:
        """Confirm stars payment."""
        return await self._request(
            "POST",
            "/api/v1/payments/stars/confirm",
            json={
                "telegram_id": telegram_id,
                "stars_amount": stars_amount,
                "currency": currency,
                "telegram_charge_id": telegram_charge_id,
                "provider_charge_id": provider_charge_id,
                "invoice_payload": invoice_payload,
            },
        )

    # Referral endpoints
    async def get_referral_info(self, telegram_id: int) -> dict:
        """Get referral info."""
        return await self._request("GET", f"/api/v1/referrals/{telegram_id}")

    # Admin endpoints
    async def add_admin_credits(
        self,
        telegram_id: int,
        credits: int,
        description: str | None = None,
    ) -> dict:
        """Add credits to user (admin only)."""
        payload: dict[str, object] = {
            "telegram_id": telegram_id,
            "amount": credits,  # Changed from 'credits' to 'amount'
        }
        if description:
            payload["reason"] = description  # Changed from 'description' to 'reason'
        return await self._request("POST", "/api/v1/admin/credits", json=payload)

    async def get_admin_stats(self) -> dict:
        """Get admin statistics."""
        return await self._request("GET", "/api/v1/admin/stats")

    async def get_users_list(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Get users list (admin only)."""
        return await self._request(
            "GET",
            f"/api/v1/admin/users?limit={limit}&offset={offset}",
        )

    # Extended admin endpoints - all use /api/v1/admin/stats now
    async def get_admin_overview_stats(self) -> dict:
        """Get overview statistics for admin panel."""
        stats = await self._request("GET", "/api/v1/admin/stats")
        # Transform to expected format
        return {
            "users": {
                "total": stats.get("total_users", 0),
                "today": stats.get("new_users_today", 0),
                "week": stats.get("new_users_week", 0),
                "month": stats.get("new_users_month", 0),
            },
            "generations": {
                "total": stats.get("total_generations", 0),
                "today": 0,  # Not available in current stats
                "week": 0,
            },
            "revenue": {
                "total_stars": stats.get("total_deposits", 0),
                "today_stars": stats.get("today_deposits", 0),
                "week_stars": stats.get("week_deposits", 0),
            },
        }

    async def get_admin_user_stats(self) -> dict:
        """Get user statistics."""
        stats = await self._request("GET", "/api/v1/admin/stats")
        return {
            "total": stats.get("total_users", 0),
            "active": stats.get("active_users_7d", 0),
            "paying": stats.get("completed_payments", 0),
            "avg_balance": 0,
            "total_balance": 0,
        }

    async def get_admin_generation_stats(self) -> dict:
        """Get generation statistics."""
        stats = await self._request("GET", "/api/v1/admin/stats")
        return {
            "total": stats.get("total_generations", 0),
            "completed": stats.get("completed_generations", 0),
            "failed": stats.get("failed_generations", 0),
            "credits_spent": stats.get("total_spent", 0),
            "by_model": stats.get("by_model", {}),
        }

    async def get_admin_revenue_stats(self) -> dict:
        """Get revenue statistics."""
        stats = await self._request("GET", "/api/v1/admin/stats")
        return {
            "total_stars": stats.get("total_deposits", 0),
            "today_stars": stats.get("today_deposits", 0),
            "week_stars": stats.get("week_deposits", 0),
            "month_stars": stats.get("month_deposits", 0),
            "total_credits_purchased": 0,
            "credits_spent": stats.get("total_spent", 0),
        }

    async def search_users(self, query: str) -> list[dict]:
        """Search users by ID or username."""
        # Use /api/v1/admin/users with query param
        result = await self._request(
            "GET",
            f"/api/v1/admin/users?query={query}&limit=20",
        )
        users = result.get("users", [])

        # Transform to expected format
        transformed = []
        for user in users:
            transformed.append(
                {
                    "telegram_id": user.get("telegram_id"),
                    "username": user.get("username"),
                    "full_name": f"{user.get('first_name', '') or ''} {user.get('last_name', '') or ''}".strip()
                    or None,
                    "balance": int(user.get("balance", 0)),
                    "trial_credits": user.get("trial_remaining", 0),
                    "total_generations": user.get("generation_count", 0),
                    "created_at": user.get("created_at", "-"),
                    "last_active": user.get("last_active_at", "-"),
                    "is_banned": user.get("is_banned", False),
                }
            )
        return transformed

    async def get_user_by_telegram_id(self, telegram_id: int) -> dict | None:
        """Get user by telegram ID."""
        try:
            result = await self._request("GET", f"/api/v1/admin/users/{telegram_id}")
            # Transform to expected format for bot
            return {
                "telegram_id": result.get("telegram_id"),
                "username": result.get("username"),
                "full_name": f"{result.get('first_name', '')} {result.get('last_name', '')}".strip() or "-",
                "balance": int(result.get("balance", 0)),
                "trial_credits": result.get("trial_remaining", 0),
                "total_generations": result.get("generation_count", 0),
                "created_at": result.get("created_at", "-"),
                "last_active": result.get("last_active_at", "-"),
                "is_banned": result.get("is_banned", False),
            }
        except APIError as e:
            if e.status == 404:
                return None
            raise

    async def get_users_page(self, page: int = 0, per_page: int = 20) -> dict:
        """Get paginated users list."""
        offset = page * per_page
        result = await self._request(
            "GET",
            f"/api/v1/admin/users?offset={offset}&limit={per_page}",
        )
        users = result.get("users", [])
        total = result.get("total", 0)
        has_more = (offset + len(users)) < total

        # Transform users to expected format
        transformed_users = []
        for user in users:
            transformed_users.append(
                {
                    "telegram_id": user.get("telegram_id"),
                    "username": user.get("username"),
                    "full_name": f"{user.get('first_name', '') or ''} {user.get('last_name', '') or ''}".strip()
                    or None,
                    "balance": int(user.get("balance", 0)),
                }
            )

        return {
            "users": transformed_users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_more": has_more,
        }

    async def toggle_user_ban(self, telegram_id: int) -> dict:
        """Toggle user ban status."""
        # This endpoint doesn't exist yet - return mock for now
        logger.warning("toggle_user_ban endpoint not implemented")
        return {"error": True, "message": "Not implemented"}

    async def adjust_user_credits(
        self,
        telegram_id: int,
        amount: int,
        reason: str = "Admin adjustment",
    ) -> dict:
        """Adjust user credits (for negative amounts)."""
        # Use same endpoint as add_credits
        return await self._request(
            "POST",
            "/api/v1/admin/credits",
            json={
                "telegram_id": telegram_id,
                "amount": amount,
                "reason": reason,
            },
        )

    async def get_user_generations(
        self,
        telegram_id: int,
        limit: int = 10,
    ) -> list[dict]:
        """Get user's recent generations."""
        return await self._request(
            "GET",
            f"/api/v1/admin/users/{telegram_id}/generations?limit={limit}",
        )

    async def refund_generation(
        self,
        telegram_id: int,
        generation_id: str,
    ) -> dict:
        """Refund a specific generation."""
        return await self._request(
            "POST",
            f"/api/v1/admin/generations/{generation_id}/refund",
            json={"telegram_id": telegram_id},
        )

    # Broadcast endpoints
    async def create_broadcast(
        self,
        admin_id: int,
        content_type: str,
        text: str | None = None,
        media_file_id: str | None = None,
        inline_button_text: str | None = None,
        inline_button_url: str | None = None,
        filter_type: str = "all",
    ) -> dict:
        """Create a new broadcast."""
        return await self._request(
            "POST",
            "/api/v1/admin/broadcasts",
            json={
                "admin_id": admin_id,
                "content_type": content_type,
                "text": text,
                "media_file_id": media_file_id,
                "inline_button_text": inline_button_text,
                "inline_button_url": inline_button_url,
                "filter_type": filter_type,
            },
        )

    async def start_broadcast(self, public_id: str) -> dict:
        """Start sending a broadcast."""
        return await self._request(
            "POST",
            f"/api/v1/admin/broadcasts/{public_id}/start",
        )

    async def cancel_broadcast(self, public_id: str) -> dict:
        """Cancel a broadcast."""
        return await self._request(
            "POST",
            f"/api/v1/admin/broadcasts/{public_id}/cancel",
        )

    async def get_broadcasts(self, limit: int = 10) -> dict:
        """Get broadcast history."""
        return await self._request(
            "GET",
            f"/api/v1/admin/broadcasts?limit={limit}",
        )

    async def get_broadcast_status(self, public_id: str) -> dict:
        """Get broadcast status."""
        return await self._request(
            "GET",
            f"/api/v1/admin/broadcasts/{public_id}",
        )

    async def get_users_count(self, filter_type: str = "all") -> dict:
        """Get users count by filter."""
        return await self._request(
            "GET",
            f"/api/v1/admin/users/count?filter_type={filter_type}",
        )

    async def get_user_payments(
        self,
        telegram_id: int,
        limit: int = 10,
    ) -> list[dict]:
        """Get user's payment history."""
        return await self._request(
            "GET",
            f"/api/v1/admin/users/{telegram_id}/payments?limit={limit}",
        )

    async def get_wavespeed_status(self) -> dict:
        """Get Wavespeed provider status and analytics."""
        return await self._request("GET", "/api/v1/admin/wavespeed/status")

    async def mark_payment_refunded(self, telegram_charge_id: str) -> dict:
        """Mark a payment as refunded by telegram_charge_id."""
        return await self._request(
            "POST",
            f"/api/v1/payments/stars/refund/{telegram_charge_id}",
        )
