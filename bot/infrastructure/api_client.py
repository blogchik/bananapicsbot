"""HTTP API client with connection pooling and retry logic."""

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector

from core.exceptions import APIError, APIConnectionError
from core.logging import get_logger

logger = get_logger(__name__)


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
    """
    
    def __init__(
        self,
        base_url: str,
        timeout_seconds: int = 180,
        max_connections: int = 100,
        retry_attempts: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = ClientTimeout(total=timeout_seconds)
        self.max_connections = max_connections
        self.retry_attempts = retry_attempts
        self._session: ClientSession | None = None
        self._connector: TCPConnector | None = None
    
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
    
    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        retry: bool = True,
    ) -> Any:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{path}"
        attempts = self.retry_attempts if retry else 1
        last_error: Exception | None = None
        
        for attempt in range(attempts):
            try:
                session = await self._get_session()
                async with session.request(method, url, json=json) as resp:
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
        return await self._request("POST", "/api/v1/users/sync", json=payload)
    
    async def get_balance(self, telegram_id: int) -> int:
        """Get user balance."""
        data = await self._request("GET", f"/api/v1/users/{telegram_id}/balance")
        return int(data["balance"])
    
    async def get_trial(self, telegram_id: int) -> TrialStatus:
        """Get user trial status."""
        data = await self._request("GET", f"/api/v1/users/{telegram_id}/trial")
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
        reference_urls: list[str] | None = None,
        reference_file_ids: list[str] | None = None,
    ) -> dict:
        """Submit generation request."""
        return await self._request(
            "POST",
            "/api/v1/generations/submit",
            json={
                "telegram_id": telegram_id,
                "model_id": model_id,
                "prompt": prompt,
                "size": size,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "reference_urls": reference_urls or [],
                "reference_file_ids": reference_file_ids or [],
            },
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
        )
    
    async def get_active_generation(self, telegram_id: int) -> dict:
        """Check for active generation."""
        return await self._request(
            "GET",
            f"/api/v1/generations/active?telegram_id={telegram_id}",
        )
    
    # Media endpoints
    async def upload_media(self, file_bytes: bytes, filename: str) -> str:
        """Upload media file."""
        data = await self._upload("/api/v1/media/upload", file_bytes, filename)
        return str(data.get("download_url", ""))
    
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
            "credits": credits,
        }
        if description:
            payload["description"] = description
        return await self._request("POST", "/api/v1/admin/credits/add", json=payload)
    
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
    
    # Extended admin endpoints
    async def get_admin_overview_stats(self) -> dict:
        """Get overview statistics for admin panel."""
        return await self._request("GET", "/api/v1/admin/stats/overview")
    
    async def get_admin_user_stats(self) -> dict:
        """Get user statistics."""
        return await self._request("GET", "/api/v1/admin/stats/users")
    
    async def get_admin_generation_stats(self) -> dict:
        """Get generation statistics."""
        return await self._request("GET", "/api/v1/admin/stats/generations")
    
    async def get_admin_revenue_stats(self) -> dict:
        """Get revenue statistics."""
        return await self._request("GET", "/api/v1/admin/stats/revenue")
    
    async def search_users(self, query: str) -> list[dict]:
        """Search users by ID or username."""
        return await self._request(
            "GET",
            f"/api/v1/admin/users/search?q={query}",
        )
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> dict | None:
        """Get user by telegram ID."""
        try:
            return await self._request("GET", f"/api/v1/admin/users/{telegram_id}")
        except APIError as e:
            if e.status == 404:
                return None
            raise
    
    async def get_users_page(self, page: int = 0, per_page: int = 20) -> dict:
        """Get paginated users list."""
        return await self._request(
            "GET",
            f"/api/v1/admin/users?page={page}&per_page={per_page}",
        )
    
    async def toggle_user_ban(self, telegram_id: int) -> dict:
        """Toggle user ban status."""
        return await self._request(
            "POST",
            f"/api/v1/admin/users/{telegram_id}/toggle-ban",
        )
    
    async def adjust_user_credits(
        self,
        telegram_id: int,
        amount: int,
        reason: str = "Admin adjustment",
    ) -> dict:
        """Adjust user credits."""
        return await self._request(
            "POST",
            "/api/v1/admin/credits/adjust",
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
    
    async def start_broadcast(self, broadcast_data: dict) -> dict:
        """Start a new broadcast."""
        return await self._request(
            "POST",
            "/api/v1/admin/broadcast",
            json=broadcast_data,
        )
    
    async def get_broadcasts(self, limit: int = 10) -> list[dict]:
        """Get broadcast history."""
        return await self._request(
            "GET",
            f"/api/v1/admin/broadcasts?limit={limit}",
        )
    
    async def get_broadcast_status(self, broadcast_id: str) -> dict:
        """Get broadcast status."""
        return await self._request(
            "GET",
            f"/api/v1/admin/broadcasts/{broadcast_id}",
        )
