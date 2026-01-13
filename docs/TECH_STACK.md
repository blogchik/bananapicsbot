# Tech Stack (recommended)

Bu hujjat implementatsiya boshlanishida “qarorlar log’i” vazifasini bajaradi. Agar stack o‘zgarsa, shu fayl yangilanadi.

## MVP tavsiya

- **Language**: Python 3.12+
- **Telegram**: `aiogram` v3 (async)
- **API (optional)**: FastAPI (admin endpoints / internal)
- **DB**: PostgreSQL
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Queue/Cache**: Redis (RQ/Arq/Celery/Taskiq — bittasi tanlanadi)
- **Object Storage**: S3-compatible (AWS S3 / Cloudflare R2 / MinIO)
- **Observability**: structured logging (JSON), Sentry (optional)

## Nega shu stack

- Telegram bot uchun async event loop + worker parallelizm qulay.
- DB ledger va idempotency uchun Postgres kuchli.
- Redis — rate limiting va queue uchun oddiy.

## Alternativlar (keyinroq)

- Node.js (Telegraf + BullMQ)
- Go (tgbotapi + asynq)
- Web admin: Next.js + API gateway

## Folder layout (target)

- `apps/bot/`
- `apps/api/`
- `apps/worker/`
- `packages/core/`
- `docs/`
