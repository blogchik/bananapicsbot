# Local Setup

Minimal ishga tushirish skeletoni qo`shildi. Quyida real dev buyruqlari.

## Prerequisites (tavsiya)

- Python 3.12+
- PostgreSQL 15+ (keyinroq kerak bo`ladi)
- Redis 6+ (queue uchun)
- S3-compatible storage (MinIO dev uchun qulay)

## O`rnatish

1) `python -m venv .venv`
2) Windows: `.\.venv\Scripts\Activate.ps1` yoki macOS/Linux: `source .venv/bin/activate`
3) `pip install -U pip`
4) `pip install -e .[bot,api,worker]`

## Konfiguratsiya

1) `.env.example` ni `.env` ga ko`chiring va qiymatlarni to`ldiring.
2) `docs/ENV.md` dagi izohlar bo`yicha provider key'larni kiriting.

## Dev run

- Bot (polling): `python -m apps.bot`
- API (health check): `uvicorn apps.api.main:app --reload`
- Worker (placeholder loop): `python -m apps.worker`

## Database migrations

1) `DATABASE_URL` ni `.env` ichida sozlang.
2) `alembic upgrade head`

## Telegram Stars testing

Stars checkout flow'ni test qilish uchun:
- test bot
- Telegram test environment/policy
kerak bo`ladi. MVP'da idempotency va ledger correctness lokal unit testlar bilan tekshiriladi.
