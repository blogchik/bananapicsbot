import json
import re
from dataclasses import asdict
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.model_options import ModelParameterOptions, get_model_parameter_options
from app.deps.wavespeed import wavespeed_client
from app.infrastructure.logging import get_logger
from app.services.redis_client import get_redis

logger = get_logger(__name__)

MODEL_OPTIONS_CACHE_KEY = "wavespeed:model-options:{model_id}"

GPT_IMAGE_DOCS: dict[str, dict[str, str]] = {
    "t2i": {
        "url": "https://wavespeed.ai/docs/docs-api/openai/openai-gpt-image-1.5-text-to-image",
        "model_uuid": "openai/gpt-image-1.5/text-to-image",
    },
    "i2i": {
        "url": "https://wavespeed.ai/docs/docs-api/openai/openai-gpt-image-1.5-edit",
        "model_uuid": "openai/gpt-image-1.5/edit",
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
    options_map = {"size": [], "aspect_ratio": [], "resolution": []}
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

    inputs = data.get("inputs") or data.get("parameters") or data.get("params")
    options_map["size"] = options_map["size"] or _extract_from_inputs(inputs, "size")
    options_map["aspect_ratio"] = options_map["aspect_ratio"] or _extract_from_inputs(
        inputs, "aspect_ratio"
    )
    options_map["resolution"] = options_map["resolution"] or _extract_from_inputs(
        inputs, "resolution"
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

    return options_map


def _merge_options(
    base: ModelParameterOptions,
    options_map: dict[str, list[str]],
) -> ModelParameterOptions:
    size_options = options_map.get("size") or []
    aspect_ratio_options = options_map.get("aspect_ratio") or []
    resolution_options = options_map.get("resolution") or []
    return ModelParameterOptions(
        supports_size=bool(size_options) or base.supports_size,
        supports_aspect_ratio=bool(aspect_ratio_options) or base.supports_aspect_ratio,
        supports_resolution=bool(resolution_options) or base.supports_resolution,
        quality_stars=base.quality_stars,
        avg_duration_seconds_min=base.avg_duration_seconds_min,
        avg_duration_seconds_max=base.avg_duration_seconds_max,
        avg_duration_text=base.avg_duration_text,
        size_options=size_options or base.size_options,
        aspect_ratio_options=aspect_ratio_options or base.aspect_ratio_options,
        resolution_options=resolution_options or base.resolution_options,
    )


def _merge_option_maps(primary: dict[str, list[str]], secondary: dict[str, list[str]]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for key in {"size", "aspect_ratio", "resolution"}:
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
        script_url = next(
            (src for src in scripts if "openai-gpt-image-1.5" in src),
            None,
        )
        if not script_url:
            return None
        if script_url.startswith("/"):
            script_url = f"https://wavespeed.ai{script_url}"
        js_response = await client.get(script_url)
        js_response.raise_for_status()
        payloads = re.findall(r"JSON.parse\\('([^']+)'\\)", js_response.text)
        for raw in payloads:
            raw_unescaped = raw.encode("utf-8").decode("unicode_escape")
            try:
                data = json.loads(raw_unescaped)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("model_uuid") == model_uuid:
                return data
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

    if model_key == "gpt-image-1.5":
        options_map: dict[str, list[str]] = {"size": [], "aspect_ratio": [], "resolution": []}
        try:
            t2i_payload = await _fetch_doc_model_payload(
                GPT_IMAGE_DOCS["t2i"]["url"],
                GPT_IMAGE_DOCS["t2i"]["model_uuid"],
            )
            if t2i_payload:
                options_map = _merge_option_maps(
                    options_map,
                    _extract_options_map(t2i_payload.get("input") or t2i_payload),
                )
            i2i_payload = await _fetch_doc_model_payload(
                GPT_IMAGE_DOCS["i2i"]["url"],
                GPT_IMAGE_DOCS["i2i"]["model_uuid"],
            )
            if i2i_payload:
                options_map = _merge_option_maps(
                    options_map,
                    _extract_options_map(i2i_payload.get("input") or i2i_payload),
                )
        except Exception as exc:
            logger.warning("Wavespeed doc options request failed", error=str(exc))
            return base_options
    else:
        return base_options

    merged = _merge_options(base_options, options_map)
    if model_key == "seedream-v4" and merged.size_options and not merged.resolution_options:
        merged = ModelParameterOptions(
            supports_size=False,
            supports_aspect_ratio=merged.supports_aspect_ratio,
            supports_resolution=True,
            quality_stars=merged.quality_stars,
            avg_duration_seconds_min=merged.avg_duration_seconds_min,
            avg_duration_seconds_max=merged.avg_duration_seconds_max,
            avg_duration_text=merged.avg_duration_text,
            size_options=[],
            aspect_ratio_options=merged.aspect_ratio_options,
            resolution_options=merged.size_options,
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
