from dataclasses import dataclass
from typing import Any

import aiohttp


@dataclass
class TrialStatus:
    trial_available: bool
    used_count: int


class ApiError(Exception):
    def __init__(self, status: int, data: Any) -> None:
        super().__init__(f"API error {status}")
        self.status = status
        self.data = data


class ApiClient:
    def __init__(self, base_url: str, timeout_seconds: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async def _request(self, method: str, path: str, json: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.request(method, url, json=json) as resp:
                if resp.status >= 400:
                    if resp.content_type == "application/json":
                        data = await resp.json()
                    else:
                        data = await resp.text()
                    raise ApiError(resp.status, data)
                if resp.content_type == "application/json":
                    return await resp.json()
                return await resp.text()

    async def _upload(self, path: str, file_bytes: bytes, filename: str) -> Any:
        url = f"{self.base_url}{path}"
        data = aiohttp.FormData()
        data.add_field("file", file_bytes, filename=filename)
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(url, data=data) as resp:
                if resp.status >= 400:
                    if resp.content_type == "application/json":
                        payload = await resp.json()
                    else:
                        payload = await resp.text()
                    raise ApiError(resp.status, payload)
                return await resp.json()

    async def sync_user(self, telegram_id: int, referral_code: str | None = None) -> dict:
        payload = {"telegram_id": telegram_id}
        if referral_code:
            payload["referral_code"] = referral_code
        return await self._request("POST", "/api/v1/users/sync", json=payload)

    async def get_balance(self, telegram_id: int) -> int:
        data = await self._request("GET", f"/api/v1/users/{telegram_id}/balance")
        return int(data["balance"])

    async def get_trial(self, telegram_id: int) -> TrialStatus:
        data = await self._request("GET", f"/api/v1/users/{telegram_id}/trial")
        return TrialStatus(
            trial_available=bool(data["trial_available"]),
            used_count=int(data["used_count"]),
        )

    async def get_models(self) -> list[dict]:
        return await self._request("GET", "/api/v1/models")

    async def get_sizes(self) -> list[str]:
        return await self._request("GET", "/api/v1/sizes")

    async def submit_generation(
        self,
        telegram_id: int,
        model_id: int,
        prompt: str,
        size: str | None,
        aspect_ratio: str | None,
        resolution: str | None,
        reference_urls: list[str],
        reference_file_ids: list[str],
    ) -> dict:
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
                "reference_urls": reference_urls,
                "reference_file_ids": reference_file_ids,
            },
        )

    async def refresh_generation(self, request_id: int, telegram_id: int) -> dict:
        return await self._request(
            "POST",
            f"/api/v1/generations/{request_id}/refresh",
            json={"telegram_id": telegram_id},
        )

    async def get_generation_results(self, request_id: int, telegram_id: int) -> list[str]:
        return await self._request(
            "GET", f"/api/v1/generations/{request_id}/results?telegram_id={telegram_id}"
        )

    async def get_active_generation(self, telegram_id: int) -> dict:
        return await self._request(
            "GET", f"/api/v1/generations/active?telegram_id={telegram_id}"
        )

    async def upload_media(self, file_bytes: bytes, filename: str) -> str:
        data = await self._upload("/api/v1/media/upload", file_bytes, filename)
        return str(data.get("download_url", ""))

    async def get_stars_options(self) -> dict:
        return await self._request("GET", "/api/v1/payments/stars/options")

    async def get_referral_info(self, telegram_id: int) -> dict:
        return await self._request("GET", f"/api/v1/referrals/{telegram_id}")

    async def add_admin_credits(
        self,
        telegram_id: int,
        credits: int,
        description: str | None = None,
    ) -> dict:
        payload: dict[str, object] = {
            "telegram_id": telegram_id,
            "credits": credits,
        }
        if description:
            payload["description"] = description
        return await self._request("POST", "/api/v1/admin/credits/add", json=payload)

    async def confirm_stars_payment(
        self,
        telegram_id: int,
        stars_amount: int,
        currency: str,
        telegram_charge_id: str,
        provider_charge_id: str | None,
        invoice_payload: str | None,
    ) -> dict:
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
