# Model: GPT Image (OpenAI)

## Qisqacha

GPT Image — OpenAI’ning rasm generatsiya imkoniyati. (API o‘zgarishi mumkin; adapter izolyatsiya qiladi.)

## Capability (draft)

- Text-to-image: yes
- Reference images: OpenAI API qo‘llab-quvvatlashiga qarab (image input bo‘lsa adapter orqali)
- Safety policy: kuchli

## Env

- `OPENAI_API_KEY`
- `OPENAI_API_BASE_URL` (optional)
- `OPENAI_ORG_ID` (optional)

## Adapter mapping (draft)

Normalized request → OpenAI images endpoint:
- prompt/negative prompt mapping (agar negative alohida bo‘lmasa promptga qo‘shib yuborish qoidasi hujjatlashtiriladi)
- size mapping
- n outputs mapping

## Error mapping

- invalid_request → `invalid_input`
- content_policy_violation → `content_blocked`
- rate_limit → `provider_rate_limited`

