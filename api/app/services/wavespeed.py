from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class WavespeedResponse:
    code: int
    message: str
    data: dict[str, Any]


class WavespeedClient:
    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        seedream_v4_t2i_url: str,
        seedream_v4_i2i_url: str,
        nano_banana_t2i_url: str,
        nano_banana_i2i_url: str,
        nano_banana_pro_t2i_url: str,
        nano_banana_pro_i2i_url: str,
        timeout_seconds: int = 30,
    ) -> None:
        self.api_key = api_key
        self.api_base_url = api_base_url.rstrip("/")
        self.seedream_v4_t2i_url = seedream_v4_t2i_url
        self.seedream_v4_i2i_url = seedream_v4_i2i_url
        self.nano_banana_t2i_url = nano_banana_t2i_url
        self.nano_banana_i2i_url = nano_banana_i2i_url
        self.nano_banana_pro_t2i_url = nano_banana_pro_t2i_url
        self.nano_banana_pro_i2i_url = nano_banana_pro_i2i_url
        self.timeout = httpx.Timeout(timeout_seconds)

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _json_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def submit_seedream_v4_t2i(
        self,
        prompt: str,
        size: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = False,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "enable_base64_output": enable_base64_output,
            "enable_sync_mode": enable_sync_mode,
        }
        if size:
            payload["size"] = size
        return await self._post_json(self.seedream_v4_t2i_url, payload)

    async def submit_seedream_v4_i2i(
        self,
        prompt: str,
        images: list[str],
        size: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = False,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "images": images,
            "enable_base64_output": enable_base64_output,
            "enable_sync_mode": enable_sync_mode,
        }
        if size:
            payload["size"] = size
        return await self._post_json(self.seedream_v4_i2i_url, payload)

    async def submit_nano_banana_t2i(
        self,
        prompt: str,
        aspect_ratio: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = False,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "enable_base64_output": enable_base64_output,
            "enable_sync_mode": enable_sync_mode,
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        return await self._post_json(self.nano_banana_t2i_url, payload)

    async def submit_nano_banana_i2i(
        self,
        prompt: str,
        images: list[str],
        aspect_ratio: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = False,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "images": images,
            "enable_base64_output": enable_base64_output,
            "enable_sync_mode": enable_sync_mode,
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        return await self._post_json(self.nano_banana_i2i_url, payload)

    async def submit_nano_banana_pro_t2i(
        self,
        prompt: str,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = False,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "enable_base64_output": enable_base64_output,
            "enable_sync_mode": enable_sync_mode,
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if resolution:
            payload["resolution"] = resolution
        return await self._post_json(self.nano_banana_pro_t2i_url, payload)

    async def submit_nano_banana_pro_i2i(
        self,
        prompt: str,
        images: list[str],
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = False,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "images": images,
            "enable_base64_output": enable_base64_output,
            "enable_sync_mode": enable_sync_mode,
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if resolution:
            payload["resolution"] = resolution
        return await self._post_json(self.nano_banana_pro_i2i_url, payload)

    async def get_prediction_result(self, request_id: str) -> WavespeedResponse:
        url = f"{self.api_base_url}/predictions/{request_id}/result"
        return await self._get_json(url)

    async def upload_media_binary(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> WavespeedResponse:
        url = f"{self.api_base_url}/media/upload/binary"
        files = {
            "file": (
                filename,
                file_bytes,
                content_type or "application/octet-stream",
            )
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=self._auth_headers(), files=files)
            resp.raise_for_status()
            data = resp.json()
            return WavespeedResponse(
                code=int(data.get("code", resp.status_code)),
                message=str(data.get("message", "")),
                data=dict(data.get("data", {})),
            )

    async def _post_json(self, url: str, payload: dict[str, Any]) -> WavespeedResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=self._json_headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            return WavespeedResponse(
                code=int(data.get("code", resp.status_code)),
                message=str(data.get("message", "")),
                data=dict(data.get("data", {})),
            )

    async def _get_json(self, url: str) -> WavespeedResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=self._json_headers())
            resp.raise_for_status()
            data = resp.json()
            return WavespeedResponse(
                code=int(data.get("code", resp.status_code)),
                message=str(data.get("message", "")),
                data=dict(data.get("data", {})),
            )
