# AGENTS

Ushbu loyiha uchun AI agentlar ishlash yo'riqnomasi.

## Loyihaning qisqa tavsifi

- Python + aiogram asosidagi Telegram bot (professional grade).
- FastAPI backend Clean Architecture (Domain-driven Design).
- Docker Compose orqali ishga tushiriladi (6 servis).
- Image generation (text-to-image, image-to-image) Wavespeed API.
- Balans/trial tizimi, referral system, Stars to'lovlar.

## Repo strukturasi

- `bot/` - Telegram bot (aiogram 3.x, professional structure)
- `api/` - FastAPI backend (Clean Architecture)
- `docs/` - hujjatlar
- `docker-compose.yml` - 6 servis (bot, api, celery-worker, celery-beat, redis, db)
- `.env` - konfiguratsiya
- `.env.example` - env namunasi

## Bot Arxitekturasi

```
bot/
├── core/           # DI container, config, logging
├── handlers/       # Telegram handlers (start, generation, payments, etc.)
├── keyboards/      # Inline va reply keyboards
├── middlewares/    # Error handling, i18n, throttling
├── services/       # Business logic
├── states/         # FSM states
├── locales/        # i18n (uz, ru, en)
└── infrastructure/ # API client, Redis, storage
```

## API Arxitekturasi

```
api/app/
├── domain/         # Entities va interfaces
├── application/    # Use cases
├── infrastructure/ # Repositories, cache, logging
├── api/v1/        # FastAPI endpoints
├── worker/        # Celery tasks
├── core/          # Config
├── deps/          # Dependencies
├── db/            # SQLAlchemy models
└── schemas/       # Pydantic models
```

## Asosiy fayllar

- `bot/main.py` - bot kirish nuqtasi
- `bot/core/container.py` - DI container
- `api/app/main.py` - FastAPI kirish nuqtasi
- `api/app/worker/celery.py` - Celery app
- `api/app/services/admin_service.py` - Admin operations
- `api/alembic/versions/` - DB migratsiyalar
- `docs/api.md` - API tuzilmasi
- `docs/bot.md` - Bot tuzilmasi

## Ishlash qoidalari

- Har bir o'zgarishdan keyin `docs/` ichidagi tegishli hujjatlarni sinxron yangilang.
- `BOT_TOKEN` faqat `.env` ichida saqlansin, kodga yozilmasin.
- `.env` repoga qo'shilmasin, `.env.example` bilan ishlang.
- Minimal dizayn va xavfsiz defaults (no hardcoded secrets).

## Tezkor ishga tushirish

```
docker compose up -d --build
```

## Testlash

- Hozircha avtomatik testlar yo'q.
- O'zgarishdan keyin bot loglarini tekshiring:

```
docker compose logs -f bot
```
