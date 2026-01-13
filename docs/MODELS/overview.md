# Models & Provider Adapters — Overview

## 1) Nega adapter kerak

Har model/provayderning API’i turlicha. Biz esa bot ichida yagona “generation request” formatini saqlaymiz.

Adapter vazifasi:
- normalized request → provider request mapping
- auth (API keys)
- response parsing → normalized result
- error mapping (timeout/policy/invalid)
- capabilities (supported sizes/settings)

## 2) Normalized request (draft)

Fields:
- `model_key`
- `prompt`
- `negative_prompt` (optional)
- `n_outputs`
- `size` yoki `aspect_ratio`
- `seed` (optional)
- `steps` (optional)
- `cfg/guidance` (optional)
- `style_preset` (optional)
- `references[]` (optional): `{url, weight, mode}`

## 3) Normalized result (draft)

- `images[]`: `{url, width, height, mime_type, bytes?}`
- `provider_job_id`
- `usage`: `{provider_cost?, tokens_charged}`
- `metadata`

## 4) Capabilities

Har adapter quyidagilarni e’lon qiladi:
- supported aspect/size list
- max outputs
- supports reference images?
- supports negative prompt?
- supports seed?

UI va pricing shu capability’lardan foydalanadi.

