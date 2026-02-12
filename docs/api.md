# API tuzilmasi

## Telegram Mini App Authentication

Webapp va API o'rtasidagi xavfsiz autentifikatsiya Telegram initData orqali amalga oshiriladi.

### Qanday ishlaydi

1. **Webapp** Telegram orqali ochilganda `window.Telegram.WebApp.initData` mavjud bo'ladi
2. Barcha API so'rovlari `X-Telegram-Init-Data` headerini yuboradi
3. **API** initData imzosini HMAC-SHA256 bilan tekshiradi
4. Auth date freshness tekshiriladi (24 soat)
5. User ID mosligini tekshiradi (faqat o'z ma'lumotlariga kirish)

### Validatsiya algoritmi

```python
# 1. Query string parse
params = parse_qs(init_data)
hash_value = params.get("hash")

# 2. Data check string (hash'siz, alfabetik tartiblangan)
data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()) if k != "hash")

# 3. Secret key
secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

# 4. Hash hisoblash va solishtirish
calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
assert calculated_hash == hash_value
```

### FastAPI Dependency

```python
from app.deps.telegram_auth import TelegramUserDep

@router.get("/protected")
async def protected_endpoint(tg_user: TelegramUserDep):
    return {"user_id": tg_user.id}
```

### Error kodlari

| Status | Sabab |
|--------|-------|
| 401 Unauthorized | initData yo'q yoki imzo noto'g'ri |
| 403 Forbidden | Boshqa user ma'lumotlariga kirish |

### Protected endpointlar

Quyidagi endpointlar `X-Telegram-Init-Data` header talab qiladi:

- `/users/sync`, `/users/{id}/balance`, `/users/{id}/trial`
- `/generations/price`, `/generations/submit`, `/generations/active`
- `/generations/{id}`, `/generations/{id}/refresh`, `/generations/{id}/results`

---

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
- `app/deps` - dependency funksiyalar (db, redis, telegram_auth, wavespeed).
- `alembic/` - DB migratsiyalar.

## Admin Endpointlar

Barcha admin endpointlar (auth va health dan tashqari) `Authorization: Bearer <jwt>` header talab qiladi.

### Auth

- `POST /api/v1/admin/auth/login` - Telegram Login Widget orqali JWT token olish
- `GET /api/v1/admin/auth/me` - JWT tekshirish, admin info qaytarish

### Dashboard

- `GET /api/v1/admin/stats?days=30` - umumiy statistika (users, generations, revenue, payments)
- `GET /api/v1/admin/health` - admin API health check

### Chart Data

- `GET /api/v1/admin/charts/users-daily?days=30` - kunlik yangi foydalanuvchilar
- `GET /api/v1/admin/charts/generations-daily?days=30` - kunlik generatsiyalar (total/completed/failed)
- `GET /api/v1/admin/charts/revenue-daily?days=30` - kunlik daromad (stars)
- `GET /api/v1/admin/charts/models-breakdown?days=30` - model bo'yicha generatsiya/kredit

### User Management

- `GET /api/v1/admin/users?query=&offset=0&limit=50` - userlarni qidirish (telegram_id yoki referral_code)
- `GET /api/v1/admin/users/{telegram_id}` - user tafsilotlari
- `GET /api/v1/admin/users/count?filter_type=...` - filter bo'yicha user soni
- `POST /api/v1/admin/users/{telegram_id}/ban` - userni ban qilish
- `POST /api/v1/admin/users/{telegram_id}/unban` - userni unban qilish
- `GET /api/v1/admin/users/{telegram_id}/generations?limit=10` - user generatsiyalari
- `GET /api/v1/admin/users/{telegram_id}/payments?limit=10` - user to'lovlari

### Credits

- `POST /api/v1/admin/credits` - balansni o'zgartirish

### Refund

- `POST /api/v1/admin/generations/{id}/refund` - generatsiya uchun kredit qaytarish

### Broadcast

- `POST /api/v1/admin/broadcasts` - yangi broadcast yaratish
- `GET /api/v1/admin/broadcasts?limit=20&offset=0` - broadcast tarixini ko'rish
- `GET /api/v1/admin/broadcasts/{public_id}` - broadcast holati
- `POST /api/v1/admin/broadcasts/{public_id}/start` - broadcastni boshlash
- `POST /api/v1/admin/broadcasts/{public_id}/cancel` - broadcastni bekor qilish

### Model Management

- `GET /api/v1/admin/models` - barcha modellar (active + inactive) + narxlar + generation count
- `PATCH /api/v1/admin/models/{model_id}` - model yangilash (is_active, name)
- `PUT /api/v1/admin/models/{model_id}/price` - model narx yangilash

### Global Payments

- `GET /api/v1/admin/payments?offset=0&limit=50` - barcha to'lovlar ro'yxati
- `GET /api/v1/admin/payments/daily?days=30` - kunlik to'lov statistikasi

### Global Generations

- `GET /api/v1/admin/generations?offset=0&limit=50&status=failed` - barcha generatsiyalar (filter bilan)
- `GET /api/v1/admin/generations/queue` - active/queued/running/pending counts

### System Settings

- `GET /api/v1/admin/settings` - barcha tizim sozlamalari
- `PATCH /api/v1/admin/settings` - sozlamalarni yangilash `{key: value, ...}`

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

- `GET /api/v1/models` - aktiv modellar ro'yxati, narxlari va parametr/metadata (quality, avg duration). Model options (size/aspect_ratio/resolution) Wavespeed docs sahifalaridan olinadi va cache qilinadi (parallel fetch).
- `GET /api/v1/sizes` - size variantlari

### Tools (Image Processing)

- `POST /api/v1/tools/watermark-remove` - watermark remover (12 credit), input: `telegram_id`, `image_url`, optional `output_format`
- `POST /api/v1/tools/upscale` - image upscaler (60 credit), input: `telegram_id`, `image_url`, optional `target_resolution` (2k/4k/8k), `output_format`
- `POST /api/v1/tools/denoise` - noise removal (20 credit), input: `telegram_id`, `image_url`, optional `model` (Normal/Strong/Extreme), `output_format`
- `POST /api/v1/tools/restore` - old photo restoration (20 credit), input: `telegram_id`, `image_url`, optional `model` (Dust-Scratch/Dust-Scratch V2), `output_format`
- `POST /api/v1/tools/enhance` - image enhancement (30 credit), input: `telegram_id`, `image_url`, optional `size`, `model` (Standard V2/Low Resolution V2/CGI/High Fidelity V2/Text Refine), `output_format`

### Payments

- `GET /api/v1/payments/stars/options` - Stars to'lov variantlari
- `POST /api/v1/payments/stars/confirm` - Stars to'lovini tasdiqlash

### Generations

- `POST /api/v1/generations/price` - generatsiya narxini hisoblash. Wavespeed API orqali real-time va bot-side caching (5 daqiqa) bilan ishlaydi. Input: model_id, size, quality, resolution, etc. Rate limit: user boshiga 60 req/min.
- `POST /api/v1/generations/submit` - generatsiyani boshlash (backend Celery polling + Telegram push)
- `GET /api/v1/generations/active?telegram_id=...` - aktiv generatsiya
- `GET /api/v1/generations/{id}?telegram_id=...` - generatsiya holati
- `POST /api/v1/generations/{id}/refresh` - natijani yangilash
- `GET /api/v1/generations/{id}/results?telegram_id=...` - natija URLlar

**Eslatma:** `generations/submit` payloadida `chat_id`, `message_id`, `prompt_message_id` berilsa, natija botga backend orqali push qilinadi. `language` (uz/ru/en) yuborilsa, natija captionlari lokalizatsiya qilinadi. Wavespeed balansi yetarli bo'lmasa, API 503 qaytaradi va generatsiya vaqtincha to'xtatiladi.
`gpt-image-1.5` uchun `quality` (low/medium/high) va `input_fidelity` (low/high, edit uchun) optional.

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
- Wavespeed balance: 60s

## Background Tasks (Celery)

Workers:

- `celery-worker` - task execution
- `celery-beat` - scheduled tasks

Tasks:

- `process_generation` - Wavespeed API polling va natijani Telegramga push qilish
- `send_broadcast_message` - individual broadcast messages
- `process_broadcast` - broadcast orchestration
- `cleanup_expired_generations` - hourly cleanup
- `send_daily_report` - daily admin statistics report (24 soatda bir marta)

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
- `payment_ledger` - to'lovlar (Stars, provider, refund holati)
- `broadcasts` - broadcast xabarlari (content, filter, status, counters)
- `broadcast_recipients` - har bir user uchun yuborish holati
- `system_settings` - tizim sozlamalari (key/value, admin panel orqali boshqariladi)

## Model katalogi

Mavjud modellar:

- `seedream-v4` - 27 credit (size parametri)
- `nano-banana` - 38 credit (aspect_ratio)
- `nano-banana-pro` - 140 credit (1k/2k), 240 credit (4k) (aspect_ratio, resolution)
- `gpt-image-1.5` - size/quality bo'yicha dinamik narx:
  - t2i: low 0.009/0.013, medium 0.034/0.051, high 0.133/0.200 (1024*1024 / 1024*1536,1536\*1024)
  - i2i: low 0.009/0.034/0.013 (1024*1024 / 1024*1536 / 1536\*1024), medium 0.034/0.051, high 0.133/0.200
- `qwen` - 20 credit (size parametri, t2i va i2i qo'llaydi)

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
  api: # FastAPI application (port 9000)
  bot: # Telegram bot
  celery-worker: # Background task worker
  celery-beat: # Scheduled tasks
  webapp: # Telegram Mini App (port 3033)
  admin-panel: # Web admin panel (port 3034)
  redis: # Cache, Celery broker (port 6479)
  db: # PostgreSQL (port 5433)
```

Barcha servislar `app_net` nomli bitta Docker networkda ishlaydi.

## Alembic

```bash
# Yangi migratsiya
alembic -c /app/alembic.ini revision --autogenerate -m "description"

# Migratsiyalarni ishga tushirish
alembic -c /app/alembic.ini upgrade heads
```

API konteyner startida avtomatik `alembic upgrade head` ishlaydi.
Multiple head holati paydo bo'lsa, merge migratsiya qo'shiladi (masalan, `0014_merge_heads`).
