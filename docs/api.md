# API tuzilmasi

## Arxitektura

API **Clean Architecture** (Domain-driven Design) asosida qurilgan:

```
app/
├── domain/              # Domain layer - business logic
│   ├── entities/        # Data classes (User, Generation, etc.)
│   └── interfaces/      # Repository va service interfeyslari
├── application/         # Application layer - use cases
│   └── use_cases/       # Business logic orchestration
├── infrastructure/      # Infrastructure layer
│   ├── database/        # SQLAlchemy models va session
│   ├── repositories/    # Repository implementations
│   ├── cache/          # Redis + Memory multi-layer cache
│   └── logging.py      # Structlog + Sentry
├── api/v1/             # API layer - FastAPI endpoints
├── worker/             # Celery background tasks
├── core/               # Configuration
├── deps/               # FastAPI dependencies
└── schemas/            # Pydantic request/response models
```

## Texnologiyalar

- **FastAPI** - async web framework
- **SQLAlchemy 2.0** - async ORM (asyncpg driver)
- **Redis** - caching, rate limiting, Celery broker
- **Celery** - background tasks (generations, broadcasts)
- **structlog** - structured logging
- **Sentry** - error tracking
- **dependency-injector** - DI container

## Qisqacha

- `app/main.py` - app factory, lifespan, middleware/handlerlar.
- `app/api/v1` - versiyalashgan routerlar.
- `app/core` - konfiguratsiya, constants.
- `app/middlewares` - request id va rate limit.
- `app/schemas` - Pydantic modellari.
- `app/deps` - dependency funksiyalar.
- `alembic/` - DB migratsiyalar.

## Admin Endpointlar

### Dashboard
- `GET /api/v1/admin/stats` - umumiy statistika (users, generations, revenue)
- `GET /api/v1/admin/health` - admin API health check

### User Management
- `GET /api/v1/admin/users` - userlarni qidirish (query, pagination)
- `GET /api/v1/admin/users/{telegram_id}` - user tafsilotlari

### Credits
- `POST /api/v1/admin/credits` - balansni o'zgartirish

## Asosiy Endpointlar

### Health & Info
- `GET /` - root info
- `GET /api/v1/health` - healthcheck (uptime, request id)
- `GET /api/v1/info` - API info

### Users
- `POST /api/v1/users/sync` - Telegram userni yaratish/sync
- `GET /api/v1/users/{telegram_id}/balance` - user balansi
- `GET /api/v1/users/{telegram_id}/trial` - trial holati

### Referrals
- `GET /api/v1/referrals/{telegram_id}` - referral ma'lumotlari

### Models
- `GET /api/v1/models` - aktiv modellar ro'yxati va narxlari
- `GET /api/v1/sizes` - size variantlari

### Payments
- `GET /api/v1/payments/stars/options` - Stars to'lov variantlari
- `POST /api/v1/payments/stars/confirm` - Stars to'lovini tasdiqlash

### Generations
- `POST /api/v1/generations/submit` - generatsiyani boshlash
- `GET /api/v1/generations/active?telegram_id=...` - aktiv generatsiya
- `GET /api/v1/generations/{id}?telegram_id=...` - generatsiya holati
- `POST /api/v1/generations/{id}/refresh` - natijani yangilash
- `GET /api/v1/generations/{id}/results?telegram_id=...` - natija URLlar

### Media
- `POST /api/v1/media/upload` - Wavespeed media upload

## Caching Strategy

Multi-layer cache:
- **L1 (Memory)**: 60s TTL, tez access, process-local
- **L2 (Redis)**: 300s TTL, shared across processes

Cache patterns:
- User profiles: 5 min
- Balances: 1 min
- Admin stats: 1 min
- Model catalog: 10 min

## Background Tasks (Celery)

Workers:
- `celery-worker` - task execution
- `celery-beat` - scheduled tasks

Tasks:
- `process_generation` - Wavespeed API polling
- `send_broadcast_message` - individual broadcast messages
- `process_broadcast` - broadcast orchestration
- `cleanup_expired_generations` - hourly cleanup

## Ledger balans

- User balansi ledger yozuvlari orqali hisoblanadi
- `ledger_entries.amount` musbat yoki manfiy
- Entry types: `deposit`, `generation`, `admin_adjustment`, `referral_bonus`, `refund`

## Telegram Stars to'lovlari

- Kurs: 70 ⭐ = 1000 credit (env orqali o'zgartiriladi)
- Referral bonus: 10% (round up)

## Ma'lumotlar modeli

- `users` - foydalanuvchilar (telegram_id, referral info)
- `ledger_entries` - balans harakatlari
- `model_catalog` - model katalogi
- `model_prices` - model narxlari
- `generations` - generatsiya so'rovlari
- `generation_jobs` - Wavespeed job holatlari
- `generation_results` - natija URLlar
- `trial_uses` - trial ishlatilganligi
- `payments` - to'lovlar
- `broadcasts` - broadcast xabarlari

## Model katalogi

Mavjud modellar:
- `seedream-v4` - 27 credit (size parametri)
- `nano-banana` - 38 credit (aspect_ratio)
- `nano-banana-pro` - 140 credit (aspect_ratio, resolution)

## Middlewarelar

- `X-Request-ID` - request tracking
- CORS - ruxsat etilgan originlar
- Rate limit - RPS va burst limitleri

## Logging

Structured logging (structlog):
- JSON format production uchun
- Console format development uchun
- Sentry integratsiya errors uchun

## Docker Compose Services

```yaml
services:
  api:          # FastAPI application
  celery-worker: # Background task worker
  celery-beat:   # Scheduled tasks
  redis:         # Cache, Celery broker
  db:            # PostgreSQL
  bot:           # Telegram bot
```

## Alembic

```bash
# Yangi migratsiya
alembic -c /app/alembic.ini revision --autogenerate -m "description"

# Migratsiyalarni ishga tushirish
alembic -c /app/alembic.ini upgrade head
```

API konteyner startida avtomatik `alembic upgrade head` ishlaydi.
