# Model: Nano Banana

## Qisqacha

Nano Banana — tezkor va arzon generatsiya uchun model (MVP default sifatida ishlatilishi mumkin).

## Capability (draft)

- Text-to-image: yes
- Reference images: yes (1..N)
- Negative prompt: yes/optional
- Max outputs: 1..4
- Sizes: 1:1, 3:4, 4:3, 16:9, 9:16

## Adapter mapping (draft)

Env:
- `NANO_BANANA_API_BASE_URL`
- `NANO_BANANA_API_KEY`

Request:
- prompt
- size/aspect
- references (urls/base64) + weights

Response:
- images[] urls or base64 → storage upload

## Error mapping

- 401/403 → `provider_auth_error`
- 429 → `provider_rate_limited`
- 5xx/timeouts → `provider_unavailable`
- policy block → `content_blocked`

