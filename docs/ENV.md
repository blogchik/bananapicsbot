# Environment Variables

Bu hujjat `.env.example` bilan **sinxron** yuritiladi (qarang `AGENTS.md`).

## Format

- Dev’da: `.env` (gitignore qilingan)
- Prod’da: secret manager yoki deployment env vars

## General

- `APP_ENV` — `dev|staging|prod`. Default: `dev`.
- `LOG_LEVEL` — `DEBUG|INFO|WARNING|ERROR`. Default: `INFO`.

## Telegram

- `TELEGRAM_BOT_TOKEN` — bot token (BotFather). **Required**.
- `TELEGRAM_ADMIN_IDS` — admin Telegram user_id’lari (comma-separated). **Required**.

## Bot runtime

- `TELEGRAM_USE_WEBHOOK` — `true|false`. Default: `false` (polling).
- `TELEGRAM_WEBHOOK_URL` — webhook base URL (agar webhook ishlatilsa). Optional.

## Database / Cache

- `DATABASE_URL` — Postgres connection string. **Required**.
- `REDIS_URL` — Redis connection string (queue/rate limit). **Required** (MVP).

## Object storage (S3-compatible)

Generated images va reference’lar saqlanadi.

- `S3_ENDPOINT_URL` — MinIO/R2/S3 endpoint. **Required**.
- `S3_ACCESS_KEY_ID` — access key. **Required**.
- `S3_SECRET_ACCESS_KEY` — secret. **Required**.
- `S3_BUCKET` — bucket nomi. **Required**.
- `S3_REGION` — region (provider’ga bog‘liq). Optional.
- `S3_PUBLIC_BASE_URL` — public CDN/base url (agar linklar public bo‘lsa). Optional.
- `S3_USE_PATH_STYLE` — `true|false` (MinIO’da ko‘p kerak). Default: `true`.

## Limits / pricing (draft)

- `MAX_PROMPT_CHARS` — prompt max uzunligi. Default: `2000`.
- `MAX_REFERENCE_IMAGES` — max reference rasm soni. Default: `4`.
- `MAX_OUTPUTS` — max chiqadigan rasm soni. Default: `4`.

## Referral policy (draft)

- `REFERRAL_PERCENT` — 0..100. Default: `10`.
- `REFERRAL_APPLY_TO` — `first_topup_only|all_topups`. Default: `all_topups`.

## Telegram Stars packages (draft)

- `STARS_PACKAGES_JSON` — JSON array: `[{stars: number, tokens: number}, ...]`
  - Admin panel keyinroq DB’dan boshqarishi mumkin, lekin MVP’da env/config bo‘lishi mumkin.

Misol:

```json
[{"stars":50,"tokens":500},{"stars":100,"tokens":1100}]
```

## Providers

Nano Banana:
- `NANO_BANANA_API_BASE_URL`
- `NANO_BANANA_API_KEY`

Nano Banana Pro:
- `NANO_BANANA_PRO_API_BASE_URL`
- `NANO_BANANA_PRO_API_KEY`

SeeDream 4:
- `SEEDREAM4_API_BASE_URL`
- `SEEDREAM4_API_KEY`

OpenAI (GPT Image):
- `OPENAI_API_KEY`
- `OPENAI_API_BASE_URL` (optional)
- `OPENAI_ORG_ID` (optional)

