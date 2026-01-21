import asyncio
import json
import re
from dataclasses import asdict
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.core.config import get_settings
from app.core.model_options import ModelParameterOptions, get_model_parameter_options
from app.deps.wavespeed import wavespeed_client
from app.infrastructure.logging import get_logger
from app.services.redis_client import get_redis

logger = get_logger(__name__)

MODEL_OPTIONS_CACHE_KEY = "wavespeed:model-options:v2:{model_id}"

MODEL_DOCS: dict[str, dict[str, dict[str, str]]] = {
    "seedream-v4": {
        "t2i": {
            "url": "https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v4",
            "model_uuid": "bytedance/seedream-v4",
        },
        "i2i": {
            "url": "https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v4-edit",
            "model_uuid": "bytedance/seedream-v4/edit",
        },
    },
    "nano-banana": {
        "t2i": {
            "url": "https://wavespeed.ai/docs/docs-api/google/google-nano-banana-text-to-image",
            "model_uuid": "google/nano-banana/text-to-image",
        },
        "i2i": {
            "url": "https://wavespeed.ai/docs/docs-api/google/google-nano-banana-edit",
            "model_uuid": "google/nano-banana/edit",
        },
    },
    "nano-banana-pro": {
        "t2i": {
            "url": "https://wavespeed.ai/docs/docs-api/google/google-nano-banana-pro-text-to-image",
            "model_uuid": "google/nano-banana-pro/text-to-image",
        },
        "i2i": {
            "url": "https://wavespeed.ai/docs/docs-api/google/google-nano-banana-pro-edit",
            "model_uuid": "google/nano-banana-pro/edit",
        },
    },
    "gpt-image-1.5": {
        "t2i": {
            "url": "https://wavespeed.ai/docs/docs-api/openai/openai-gpt-image-1.5-text-to-image",
            "model_uuid": "openai/gpt-image-1.5/text-to-image",
        },
        "i2i": {
            "url": "https://wavespeed.ai/docs/docs-api/openai/openai-gpt-image-1.5-edit",
            "model_uuid": "openai/gpt-image-1.5/edit",
        },
    },
    "qwen": {
        "t2i": {
            "url": "https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-text-to-image",
            "model_uuid": "wavespeed-ai/qwen-image/text-to-image",
        },
        "i2i": {
            "url": "https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-edit",
            "model_uuid": "wavespeed-ai/qwen-image/edit",
        },
    },
}


def _normalize_option_list(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, dict):
        values = values.get("options") or values.get("values") or values.get("enum")
    if not isinstance(values, list):
        return []
    normalized: list[str] = []
    for item in values:
        value = item
        if isinstance(item, dict):
            value = (
                item.get("value")
                or item.get("id")
                or item.get("key")
                or item.get("name")
            )
        if value is None:
            continue
        text = str(value).strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _extract_enum_values(schema: dict[str, Any] | None) -> list[str]:
    if not isinstance(schema, dict):
        return []
    values = _normalize_option_list(schema.get("enum"))
    if values:
        return values
    for key in ("oneOf", "anyOf"):
        candidates = schema.get(key)
        if not isinstance(candidates, list):
            continue
        options: list[str] = []
        for item in candidates:
            if not isinstance(item, dict):
                continue
            options.extend(_normalize_option_list(item.get("enum")))
            const_value = item.get("const")
            if const_value is not None:
                text = str(const_value).strip()
                if text and text not in options:
                    options.append(text)
        if options:
            return options
    return []


def _extract_from_schema(schema: dict[str, Any] | None, field: str) -> list[str]:
    if not isinstance(schema, dict):
        return []
    properties = schema.get("properties") or schema.get("fields") or {}
    if not isinstance(properties, dict):
        return []
    return _extract_enum_values(properties.get(field))


def _extract_from_inputs(inputs: Any, field: str) -> list[str]:
    if not isinstance(inputs, list):
        return []
    for item in inputs:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("key") or item.get("param")
        if name == field:
            return _normalize_option_list(
                item.get("options")
                or item.get("values")
                or item.get("enum")
                or item.get("choices")
            )
    return []


def _extract_options_map(data: dict[str, Any]) -> dict[str, list[str]]:
    options_map = {
        "size": [],
        "aspect_ratio": [],
        "resolution": [],
        "quality": [],
        "input_fidelity": [],
    }
    if not isinstance(data, dict):
        return options_map

    for key in ("input_schema", "schema", "input"):
        options_map["size"] = options_map["size"] or _extract_from_schema(data.get(key), "size")
        options_map["aspect_ratio"] = options_map["aspect_ratio"] or _extract_from_schema(
            data.get(key), "aspect_ratio"
        )
        options_map["resolution"] = options_map["resolution"] or _extract_from_schema(
            data.get(key), "resolution"
        )
        options_map["quality"] = options_map["quality"] or _extract_from_schema(
            data.get(key), "quality"
        )
        options_map["input_fidelity"] = options_map["input_fidelity"] or _extract_from_schema(
            data.get(key), "input_fidelity"
        )

    inputs = data.get("inputs") or data.get("parameters") or data.get("params")
    options_map["size"] = options_map["size"] or _extract_from_inputs(inputs, "size")
    options_map["aspect_ratio"] = options_map["aspect_ratio"] or _extract_from_inputs(
        inputs, "aspect_ratio"
    )
    options_map["resolution"] = options_map["resolution"] or _extract_from_inputs(
        inputs, "resolution"
    )
    options_map["quality"] = options_map["quality"] or _extract_from_inputs(
        inputs, "quality"
    )
    options_map["input_fidelity"] = options_map["input_fidelity"] or _extract_from_inputs(
        inputs, "input_fidelity"
    )

    options_map["size"] = options_map["size"] or _normalize_option_list(
        data.get("sizes") or data.get("size_options")
    )
    options_map["aspect_ratio"] = options_map["aspect_ratio"] or _normalize_option_list(
        data.get("aspect_ratio_options")
    )
    options_map["resolution"] = options_map["resolution"] or _normalize_option_list(
        data.get("resolution_options")
    )
    options_map["quality"] = options_map["quality"] or _normalize_option_list(
        data.get("quality_options")
    )
    options_map["input_fidelity"] = options_map["input_fidelity"] or _normalize_option_list(
        data.get("input_fidelity_options")
    )

    return options_map


def _merge_options(
    base: ModelParameterOptions,
    options_map: dict[str, list[str]],
) -> ModelParameterOptions:
    size_options = options_map.get("size") or []
    aspect_ratio_options = options_map.get("aspect_ratio") or []
    resolution_options = options_map.get("resolution") or []
    quality_options = options_map.get("quality") or []
    input_fidelity_options = options_map.get("input_fidelity") or []
    return ModelParameterOptions(
        supports_size=bool(size_options) or base.supports_size,
        supports_aspect_ratio=bool(aspect_ratio_options) or base.supports_aspect_ratio,
        supports_resolution=bool(resolution_options) or base.supports_resolution,
        supports_quality=bool(quality_options) or base.supports_quality,
        supports_input_fidelity=bool(input_fidelity_options) or base.supports_input_fidelity,
        quality_stars=base.quality_stars,
        avg_duration_seconds_min=base.avg_duration_seconds_min,
        avg_duration_seconds_max=base.avg_duration_seconds_max,
        avg_duration_text=base.avg_duration_text,
        size_options=size_options or base.size_options,
        aspect_ratio_options=aspect_ratio_options or base.aspect_ratio_options,
        resolution_options=resolution_options or base.resolution_options,
        quality_options=quality_options or base.quality_options,
        input_fidelity_options=input_fidelity_options or base.input_fidelity_options,
    )


def _merge_option_maps(primary: dict[str, list[str]], secondary: dict[str, list[str]]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for key in {"size", "aspect_ratio", "resolution", "quality", "input_fidelity"}:
        values = list(primary.get(key) or [])
        for item in secondary.get(key) or []:
            if item not in values:
                values.append(item)
        merged[key] = values
    return merged


async def _fetch_doc_model_payload(url: str, model_uuid: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        scripts = re.findall(r'<script src="([^"]+)"', response.text)
        path = urlsplit(url).path
        if "/docs/" in path:
            page_path = path.split("/docs/", 1)[1].strip("/")
        else:
            page_path = path.strip("/")
        target = f"pages/{page_path}"
        script_url = next(
            (src for src in scripts if target in src),
            None,
        ) or next((src for src in scripts if page_path in src), None)
        if not script_url:
            return None
        if script_url.startswith("/"):
            script_url = f"https://wavespeed.ai{script_url}"
        js_response = await client.get(script_url)
        js_response.raise_for_status()
        payloads = re.findall(r"JSON.parse\\('((?:\\'|[^'])+)'\\)", js_response.text)
        for raw in payloads:
            raw_unescaped = raw.encode("utf-8").decode("unicode_escape")
            raw_unescaped = raw_unescaped.replace("\\'", "'")
            try:
                data = json.loads(raw_unescaped)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("model_uuid") == model_uuid:
                return data
    return None


async def get_wavespeed_doc_payload(
    model_key: str | None,
    mode: str,
) -> dict[str, Any] | None:
    if not model_key:
        return None
    docs = MODEL_DOCS.get(model_key)
    if not docs:
        return None
    entry = docs.get(mode)
    if not entry:
        return None
    try:
        return await _fetch_doc_model_payload(entry["url"], entry["model_uuid"])
    except Exception as exc:
        logger.warning(
            "Wavespeed doc payload fetch failed",
            model_key=model_key,
            mode=mode,
            error=str(exc),
        )
        return None


async def get_model_parameter_options_from_wavespeed(
    model_key: str | None,
) -> ModelParameterOptions:
    base_options = get_model_parameter_options(model_key)
    if not model_key:
        return base_options

    settings = get_settings()
    client = wavespeed_client()
    model_id = client.get_model_identifier(model_key, "t2i") or model_key

    cache_key = MODEL_OPTIONS_CACHE_KEY.format(model_id=model_id)
    redis = get_redis()
    try:
        cached = await redis.get(cache_key)
        if cached:
            payload = json.loads(cached)
            return ModelParameterOptions(**payload)
    except Exception as exc:
        logger.warning("Model options cache read failed", error=str(exc))

    docs = MODEL_DOCS.get(model_key)
    if not docs:
        return base_options

    options_map: dict[str, list[str]] = {
        "size": [],
        "aspect_ratio": [],
        "resolution": [],
        "quality": [],
        "input_fidelity": [],
    }
    try:
        t2i = docs.get("t2i")
        i2i = docs.get("i2i")
        tasks = []
        if t2i:
            tasks.append(_fetch_doc_model_payload(t2i["url"], t2i["model_uuid"]))
        if i2i:
            tasks.append(_fetch_doc_model_payload(i2i["url"], i2i["model_uuid"]))
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception) or not result:
                    continue
                options_map = _merge_option_maps(
                    options_map,
                    _extract_options_map(result.get("input") or result),
                )
    except Exception as exc:
        logger.warning("Wavespeed doc options request failed", error=str(exc))
        return base_options

    merged = _merge_options(base_options, options_map)
    if model_key == "seedream-v4" and merged.size_options and not merged.resolution_options:
        merged = ModelParameterOptions(
            supports_size=False,
            supports_aspect_ratio=merged.supports_aspect_ratio,
            supports_resolution=True,
            supports_quality=merged.supports_quality,
            supports_input_fidelity=merged.supports_input_fidelity,
            quality_stars=merged.quality_stars,
            avg_duration_seconds_min=merged.avg_duration_seconds_min,
            avg_duration_seconds_max=merged.avg_duration_seconds_max,
            avg_duration_text=merged.avg_duration_text,
            size_options=[],
            aspect_ratio_options=merged.aspect_ratio_options,
            resolution_options=merged.size_options,
            quality_options=merged.quality_options,
            input_fidelity_options=merged.input_fidelity_options,
        )
    try:
        await redis.set(
            cache_key,
            json.dumps(asdict(merged)),
            ex=settings.wavespeed_model_options_cache_ttl_seconds,
        )
    except Exception as exc:
        logger.warning("Model options cache write failed", error=str(exc))
    return merged
