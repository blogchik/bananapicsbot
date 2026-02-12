# Env sozlamalari

## Bot Configuration

- `BOT_TOKEN`: Telegram bot tokeni (majburiy).
- `BOT_MODE`: Bot ishlash rejimi (`polling` yoki `webhook`, default: `polling`).
- `REDIS_URL`: Redis ulanish URL (default: `redis://redis:6379/0`).
- `API_BASE_URL`: API bazaviy manzili (default: `http://api:9000`).
- `API_TIMEOUT_SECONDS`: API chaqiruv timeouti sekund (default: `180`).
- `PAYMENT_PROVIDER_TOKEN`: Telegram payment provider token (Stars uchun bo'sh bo'lishi mumkin).
- `ADMIN_IDS`: Admin Telegram ID lari, vergul bilan ajratilgan (masalan: `686980246,123456789`).
- `DEFAULT_LANGUAGE`: Default til kodi (default: `uz`).

### Rate Limiting (Bot)

- `RATE_LIMIT_MESSAGES`: Daqiqada ruxsat etilgan xabarlar soni (default: `30`).
- `RATE_LIMIT_CALLBACKS`: Daqiqada ruxsat etilgan callback soni (default: `60`).

### Webhook Mode

- `WEBHOOK_URL`: Webhook uchun tashqi URL.
- `WEBHOOK_SECRET`: Webhook secret token (optional).
- `WEBHOOK_HOST`: Webhook server host (default: `0.0.0.0`).
- `WEBHOOK_PORT`: Webhook server port (default: `8443`).

### Logging & Monitoring

- `LOG_LEVEL`: Log darajasi (`DEBUG`, `INFO`, `WARNING`, `ERROR`, default: `INFO`).
- `SENTRY_DSN`: Sentry DSN error tracking uchun.

## API Configuration

- `APP_NAME`: API nomi.
- `APP_VERSION`: API versiyasi.
- `API_PREFIX`: API prefiksi (default: `/api/v1`).
- `ENVIRONMENT`: Muhit nomi (masalan, `local`, `staging`, `prod`).
- `CORS_ORIGINS`: Ruxsat etilgan originlar (vergul bilan ajratilgan yoki JSON list).
- `RATE_LIMIT_ENABLED`: Rate limit yoqilgan/yoqilmagan.
- `RATE_LIMIT_RPS`: 1 soniyadagi ruxsat etilgan so'rovlar soni.
- `RATE_LIMIT_BURST`: Qisqa burst limiti.
- `RUN_MIGRATIONS`: API startida migratsiyalarni avtomatik ishga tushirish.
- `BOT_TOKEN`: Bot tokeni (Celery broadcast tasklari uchun - API tomonida).
- `ADMIN_TELEGRAM_IDS`: Admin Telegram ID lari, vergul bilan ajratilgan (API uchun, kunlik hisobotlar uchun).
- `MAX_PARALLEL_GENERATIONS_PER_USER`: Bitta user uchun parallel generatsiyalar limiti (default: `2`).

## Wavespeed Provider

- `WAVESPEED_API_BASE_URL`: Wavespeed provider API bazaviy manzili (`https://api.wavespeed.ai`).
- `WAVESPEED_API_KEY`: Wavespeed API kaliti.
- `WAVESPEED_TIMEOUT_SECONDS`: Wavespeed HTTP timeout (sekund).
- `WAVESPEED_MIN_BALANCE`: Generatsiyalarni to'xtatish uchun minimal Wavespeed balans threshold.
- `WAVESPEED_BALANCE_CACHE_TTL_SECONDS`: Wavespeed balance cache TTL (sekund).
- `WAVESPEED_BALANCE_ALERT_TTL_SECONDS`: Admin alert throttle TTL (sekund).
- `WAVESPEED_MODEL_OPTIONS_CACHE_TTL_SECONDS`: Wavespeed model options cache TTL (sekund).

## Payments

- `STARS_ENABLED`: Telegram Stars orqali to'lovlar yoqilgan/yoqilmagan.
- `STARS_MIN_AMOUNT`: Minimal Stars miqdori.
- `STARS_PRESETS`: Stars uchun presetlar (vergul bilan).
- `STARS_EXCHANGE_NUMERATOR`: Kredit kursi numerator.
- `STARS_EXCHANGE_DENOMINATOR`: Kredit kursi denominator.
- `REFERRAL_BONUS_PERCENT`: Referral bonus foizi (round up).
- `REFERRAL_JOIN_BONUS`: Yangi referral qo'shilganda beriluvchi credit bonus.
- `GENERATION_PRICE_MARKUP`: Admin tomonidan belgilanadigan narx qo'shimchasi (creditlarda). Wavespeed narxiga qo'shiladi.

## Redis

- `REDIS_URL`: Redis connection URL (bot uchun).
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`: Redis ulanish sozlamalari (API uchun).
- `REDIS_ACTIVE_GENERATION_TTL_SECONDS`: Active generatsiya lock TTL.

## PostgreSQL

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `POSTGRES_HOST`, `POSTGRES_PORT`

## Webapp

- `WEBAPP_URL`: Webapp tashqi URL (CORS uchun). Masalan: `https://webapp.bananapics.com`
- `VITE_API_URL`: API bazaviy URL (webapp build uchun, default: `/api/v1`)
- `VITE_BOT_USERNAME`: Telegram bot username (@ belgisisiz, default: `BananaPicsBot`)

### initData Validatsiya

- `BOT_TOKEN`: Bot tokeni - initData imzosini tekshirish uchun (API uchun majburiy)
- initData freshness: 24 soat (hardcoded)

## Admin Panel

- `ADMIN_JWT_SECRET`: Admin panel JWT token uchun maxfiy kalit (majburiy, production'da kuchli random string ishlatish kerak).
- `ADMIN_PANEL_URL`: Admin panel tashqi URL (CORS uchun). Masalan: `https://admin.bananapics.com`
- `VITE_BOT_USERNAME`: Telegram bot username — Telegram Login Widget uchun (@ belgisisiz). Admin panel build paytida ishlatiladi.
- `VITE_API_URL`: API bazaviy URL (admin-panel build uchun, default: `/api/v1`, nginx orqali proxy qilinadi).

### Admin Auth

- Telegram Login Widget orqali HMAC-SHA256 tekshiruvi
- JWT token 24 soat amal qiladi
- Faqat `ADMIN_TELEGRAM_IDS` ro'yxatidagi userlar kirishi mumkin

## Namuna

```env
# ===================
# Bot Configuration
# ===================
BOT_TOKEN=123456:ABCDEF
BOT_MODE=polling
REDIS_URL=redis://redis:6379/0
API_BASE_URL=http://api:9000
API_TIMEOUT_SECONDS=180
PAYMENT_PROVIDER_TOKEN=

# Admin (comma-separated Telegram user IDs)
ADMIN_IDS=686980246

# Localization
DEFAULT_LANGUAGE=uz

# Rate Limiting (bot level)
RATE_LIMIT_MESSAGES=30
RATE_LIMIT_CALLBACKS=60

# Webhook (optional, for webhook mode)
WEBHOOK_URL=
WEBHOOK_SECRET=
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8443

# Logging & Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=

# ===================
# API Configuration
# ===================
APP_NAME=Bananapics API
APP_VERSION=0.1.2
API_PREFIX=/api/v1
ENVIRONMENT=local
CORS_ORIGINS=
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RPS=5
RATE_LIMIT_BURST=10
RUN_MIGRATIONS=true
ADMIN_TELEGRAM_IDS=686980246
MAX_PARALLEL_GENERATIONS_PER_USER=2

# ===================
# Wavespeed Provider
# ===================
WAVESPEED_API_BASE_URL=https://api.wavespeed.ai
WAVESPEED_API_KEY=
WAVESPEED_TIMEOUT_SECONDS=180
WAVESPEED_MIN_BALANCE=1.0
WAVESPEED_BALANCE_CACHE_TTL_SECONDS=60
WAVESPEED_BALANCE_ALERT_TTL_SECONDS=600
WAVESPEED_MODEL_OPTIONS_CACHE_TTL_SECONDS=600

# ===================
# Payments
# ===================
STARS_ENABLED=true
STARS_MIN_AMOUNT=70
STARS_PRESETS=70,140,210,350,700,1400
STARS_EXCHANGE_NUMERATOR=1000
STARS_EXCHANGE_DENOMINATOR=70
REFERRAL_BONUS_PERCENT=10
REFERRAL_JOIN_BONUS=20

# Generation pricing markup (in credits)
# This amount is added to the base Wavespeed price for each generation
# Example: If Wavespeed price is 240 credits and markup is 40, user pays 280 credits
GENERATION_PRICE_MARKUP=40

# ===================
# Redis (API)
# ===================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_ACTIVE_GENERATION_TTL_SECONDS=900

# ===================
# PostgreSQL
# ===================
POSTGRES_USER=bananapics
POSTGRES_PASSWORD=bananapics
POSTGRES_DB=bananapics
POSTGRES_HOST=db
POSTGRES_PORT=5432

# ===================
# Webapp
# ===================
WEBAPP_URL=https://webapp.bananapics.com
# VITE_API_URL=/api/v1  # Build time env (webapp)
# VITE_BOT_USERNAME=BananaPicsBot  # Build time env (webapp)

# ===================
# Admin Panel
# ===================
ADMIN_JWT_SECRET=change-this-to-a-secure-random-string
ADMIN_PANEL_URL=http://localhost:3034
VITE_BOT_USERNAME=BananaPicsBot
```

## Tayyorlash

1. `.env.example` faylini `.env` ga ko'chiring.
2. `BOT_TOKEN` ni real token bilan to'ldiring.
3. Kerakli boshqa parametrlarni sozlang.

## Eslatma

- Tokenni ommaga oshkor qilmang.
- Token yangilansa, `docker compose up -d --build` bilan qayta ishga tushiring.
