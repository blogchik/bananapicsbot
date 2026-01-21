import asyncio
import io
from dataclasses import dataclass
from typing import Any

import requests
from wavespeed import Client as WavespeedSdkClient


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
        timeout_seconds: int = 30,
    ) -> None:
        self._timeout_seconds = float(timeout_seconds)
        base_url = api_base_url.rstrip("/")
        if base_url.endswith("/api/v3"):
            base_url = base_url[: -len("/api/v3")]
        self._client = WavespeedSdkClient(
            api_key=api_key,
            base_url=base_url,
            connection_timeout=self._timeout_seconds,
        )

        self._seedream_v4_t2i_model = "bytedance/seedream-v4"
        self._seedream_v4_i2i_model = "bytedance/seedream-v4/edit"
        self._nano_banana_t2i_model = "google/nano-banana/text-to-image"
        self._nano_banana_i2i_model = "google/nano-banana/edit"
        self._nano_banana_pro_t2i_model = "google/nano-banana-pro/text-to-image"
        self._nano_banana_pro_i2i_model = "google/nano-banana-pro/edit"
        self._gpt_image_1_5_t2i_model = "openai/gpt-image-1.5/text-to-image"
        self._gpt_image_1_5_i2i_model = "openai/gpt-image-1.5/edit"
        self._qwen_t2i_model = "wavespeed-ai/qwen-image/text-to-image"
        self._qwen_i2i_model = "wavespeed-ai/qwen-image/edit"
        self._watermark_remover_model = "wavespeed-ai/image-watermark-remover"
        # Image tools
        self._upscaler_model = "wavespeed-ai/ultimate-image-upscaler"
        self._denoise_model = "topaz/image/denoise"
        self._restore_model = "topaz/image/restore"
        self._enhance_model = "topaz/image/enhance"

        self._model_map: dict[str, dict[str, str]] = {
            "seedream-v4": {
                "t2i": self._seedream_v4_t2i_model,
                "i2i": self._seedream_v4_i2i_model,
            },
            "nano-banana": {
                "t2i": self._nano_banana_t2i_model,
                "i2i": self._nano_banana_i2i_model,
            },
            "nano-banana-pro": {
                "t2i": self._nano_banana_pro_t2i_model,
                "i2i": self._nano_banana_pro_i2i_model,
            },
            "gpt-image-1.5": {
                "t2i": self._gpt_image_1_5_t2i_model,
                "i2i": self._gpt_image_1_5_i2i_model,
            },
            "qwen": {
                "t2i": self._qwen_t2i_model,
                "i2i": self._qwen_i2i_model,
            },
        }

    def _response_from_result(self, result: dict[str, Any]) -> WavespeedResponse:
        data = result.get("data", {})
        return WavespeedResponse(
            code=int(result.get("code", 200)),
            message=str(result.get("message", "")),
            data=dict(data) if isinstance(data, dict) else {},
        )

    async def _submit_model(
        self,
        model: str,
        payload: dict[str, Any],
        enable_sync_mode: bool,
    ) -> WavespeedResponse:
        def _call() -> WavespeedResponse:
            request_id, sync_result = self._client._submit(
                model,
                payload,
                enable_sync_mode=enable_sync_mode,
                timeout=self._timeout_seconds,
            )
            if enable_sync_mode:
                return self._response_from_result(sync_result or {})
            return WavespeedResponse(
                code=200,
                message="success",
                data={"id": request_id},
            )

        return await asyncio.to_thread(_call)

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
        }
        if size:
            payload["size"] = size
        return await self._submit_model(
            self._seedream_v4_t2i_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

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
        }
        if size:
            payload["size"] = size
        return await self._submit_model(
            self._seedream_v4_i2i_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

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
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        return await self._submit_model(
            self._nano_banana_t2i_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

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
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        return await self._submit_model(
            self._nano_banana_i2i_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

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
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if resolution:
            payload["resolution"] = resolution
        return await self._submit_model(
            self._nano_banana_pro_t2i_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

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
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if resolution:
            payload["resolution"] = resolution
        return await self._submit_model(
            self._nano_banana_pro_i2i_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

    async def submit_gpt_image_1_5_t2i(
        self,
        prompt: str,
        size: str | None = None,
        quality: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = False,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "enable_base64_output": enable_base64_output,
        }
        if size:
            payload["size"] = size
        if quality:
            payload["quality"] = quality
        return await self._submit_model(
            self._gpt_image_1_5_t2i_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

    async def submit_gpt_image_1_5_i2i(
        self,
        prompt: str,
        images: list[str],
        size: str | None = None,
        quality: str | None = None,
        input_fidelity: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = False,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "images": images,
            "enable_base64_output": enable_base64_output,
        }
        if size:
            payload["size"] = size
        if quality:
            payload["quality"] = quality
        if input_fidelity:
            payload["input_fidelity"] = input_fidelity
        return await self._submit_model(
            self._gpt_image_1_5_i2i_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

    async def submit_qwen_t2i(
        self,
        prompt: str,
        size: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = False,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "enable_base64_output": enable_base64_output,
        }
        if size:
            payload["size"] = size
        return await self._submit_model(
            self._qwen_t2i_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

    async def submit_qwen_i2i(
        self,
        prompt: str,
        images: list[str],
        size: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = False,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "image": images[0] if images else "",
            "enable_base64_output": enable_base64_output,
        }
        if size:
            payload["size"] = size
        return await self._submit_model(
            self._qwen_i2i_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

    async def submit_watermark_remover(
        self,
        image: str,
        output_format: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = True,
    ) -> WavespeedResponse:
        payload: dict[str, Any] = {
            "image": image,
            "enable_base64_output": enable_base64_output,
        }
        if output_format:
            payload["output_format"] = output_format
        return await self._submit_model(
            self._watermark_remover_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

    async def submit_upscaler(
        self,
        image: str,
        target_resolution: str = "4k",
        output_format: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = True,
    ) -> WavespeedResponse:
        """Submit image to Ultimate Image Upscaler.
        
        Args:
            image: Image URL
            target_resolution: 2k, 4k, or 8k
            output_format: jpeg, png, or webp
        """
        payload: dict[str, Any] = {
            "image": image,
            "target_resolution": target_resolution,
            "enable_base64_output": enable_base64_output,
        }
        if output_format:
            payload["output_format"] = output_format
        return await self._submit_model(
            self._upscaler_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

    async def submit_denoise(
        self,
        image: str,
        model: str = "Normal",
        output_format: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = True,
    ) -> WavespeedResponse:
        """Submit image to Topaz Denoise.
        
        Args:
            image: Image URL
            model: Normal, Strong, or Extreme
            output_format: jpeg, jpg, or png
        """
        payload: dict[str, Any] = {
            "image": image,
            "model": model,
            "enable_base64_output": enable_base64_output,
        }
        if output_format:
            payload["output_format"] = output_format
        return await self._submit_model(
            self._denoise_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

    async def submit_restore(
        self,
        image: str,
        model: str = "Dust-Scratch",
        output_format: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = True,
    ) -> WavespeedResponse:
        """Submit image to Topaz Restore.
        
        Args:
            image: Image URL
            model: Dust-Scratch or Dust-Scratch V2
            output_format: jpeg, jpg, png, tiff, or tif
        """
        payload: dict[str, Any] = {
            "image": image,
            "model": model,
            "enable_base64_output": enable_base64_output,
        }
        if output_format:
            payload["output_format"] = output_format
        return await self._submit_model(
            self._restore_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

    async def submit_enhance(
        self,
        image: str,
        size: str = "1080*1080",
        model: str = "Standard V2",
        output_format: str | None = None,
        enable_base64_output: bool = False,
        enable_sync_mode: bool = True,
    ) -> WavespeedResponse:
        """Submit image to Topaz Enhance.
        
        Args:
            image: Image URL
            size: Output size (e.g., 1080*1080, up to 4096*4096)
            model: Standard V2, Low Resolution V2, CGI, High Fidelity V2, Text Refine
            output_format: jpeg, jpg, or png
        """
        payload: dict[str, Any] = {
            "image": image,
            "size": size,
            "model": model,
            "enable_base64_output": enable_base64_output,
        }
        if output_format:
            payload["output_format"] = output_format
        return await self._submit_model(
            self._enhance_model,
            payload,
            enable_sync_mode=enable_sync_mode,
        )

    def get_model_identifier(self, model_key: str, mode: str) -> str | None:
        mode_key = mode.lower()
        entry = self._model_map.get(model_key, {})
        return entry.get(mode_key)

    async def get_prediction_result(self, request_id: str) -> WavespeedResponse:
        def _call() -> WavespeedResponse:
            result = self._client._get_result(
                request_id,
                timeout=self._timeout_seconds,
            )
            return self._response_from_result(result)

        return await asyncio.to_thread(_call)

    async def get_balance(self) -> WavespeedResponse:
        def _call() -> WavespeedResponse:
            url = f"{self._client.base_url}/api/v3/balance"
            headers = self._client._get_headers()
            request_timeout = (
                min(self._client.connection_timeout, self._timeout_seconds),
                self._timeout_seconds,
            )
            response = requests.get(url, headers=headers, timeout=request_timeout)
            response.raise_for_status()
            return self._response_from_result(response.json())

        return await asyncio.to_thread(_call)

    async def get_model_info(self, model: str) -> WavespeedResponse:
        def _call() -> WavespeedResponse:
            from urllib.parse import quote

            base_url = self._client.base_url
            encoded = quote(model, safe="")
            urls = [f"{base_url}/api/v3/models/{encoded}"]
            if encoded != model:
                urls.append(f"{base_url}/api/v3/models/{model}")
            headers = self._client._get_headers()
            request_timeout = (
                min(self._client.connection_timeout, self._timeout_seconds),
                self._timeout_seconds,
            )
            last_error: Exception | None = None
            for url in urls:
                try:
                    response = requests.get(url, headers=headers, timeout=request_timeout)
                    response.raise_for_status()
                    return self._response_from_result(response.json())
                except Exception as exc:
                    last_error = exc
            if last_error:
                raise last_error
            raise RuntimeError("Wavespeed model info request failed")

        return await asyncio.to_thread(_call)

    async def upload_media_binary(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> WavespeedResponse:
        def _call() -> WavespeedResponse:
            file_obj = io.BytesIO(file_bytes)
            try:
                file_obj.name = filename
            except Exception:
                pass
            download_url = self._client.upload(
                file_obj,
                timeout=self._timeout_seconds,
            )
            return WavespeedResponse(
                code=200,
                message="success",
                data={
                    "download_url": download_url,
                    "filename": filename,
                    "size": len(file_bytes),
                },
            )

        return await asyncio.to_thread(_call)

    async def get_model_pricing(
        self,
        model_id: str,
        inputs: dict[str, Any] | None = None,
    ) -> WavespeedResponse:
        """Get pricing for a model with given inputs.
        
        Args:
            model_id: Full model identifier (e.g., "bytedance/seedream-v4")
            inputs: Optional input parameters (prompt, size, quality, etc.)
        
        Returns:
            WavespeedResponse with data containing:
                - model_id: str
                - unit_price: float (USD)
                - currency: str ("USD")
        """
        def _call() -> WavespeedResponse:
            url = f"{self._client.base_url}/api/v3/model/pricing"
            headers = self._client._get_headers()
            request_timeout = (
                min(self._client.connection_timeout, self._timeout_seconds),
                self._timeout_seconds,
            )
            payload = {
                "model_id": model_id,
                "inputs": inputs or {},
            }
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=request_timeout,
            )
            response.raise_for_status()
            return self._response_from_result(response.json())

        return await asyncio.to_thread(_call)

