from dataclasses import dataclass
from typing import Any

import aiohttp


@dataclass
class TrialStatus:
    trial_available: bool
    used_count: int


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, path: str, json: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json, timeout=10) as resp:
                resp.raise_for_status()
                if resp.content_type == "application/json":
                    return await resp.json()
                return await resp.text()

    async def sync_user(self, telegram_id: int) -> dict:
        return await self._request("POST", "/api/v1/users/sync", json={"telegram_id": telegram_id})

    async def get_balance(self, telegram_id: int) -> int:
        data = await self._request("GET", f"/api/v1/users/{telegram_id}/balance")
        return int(data["balance"])

    async def get_trial(self, telegram_id: int) -> TrialStatus:
        data = await self._request("GET", f"/api/v1/users/{telegram_id}/trial")
        return TrialStatus(
            trial_available=bool(data["trial_available"]),
            used_count=int(data["used_count"]),
        )
