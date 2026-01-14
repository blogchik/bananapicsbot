# Env sozlamalari

- `BOT_TOKEN`: Telegram bot tokeni. `.env` ichida saqlanadi.
- `API_BASE_URL`: API bazaviy manzili (ko'rsatilmasa `http://api:8000`).
- `API_TIMEOUT_SECONDS`: Botning API chaqiruv timeouti (sekund).
- `APP_NAME`: API nomi.
- `APP_VERSION`: API versiyasi.
- `API_PREFIX`: API prefiksi (default: `/api/v1`).
- `ENVIRONMENT`: Muhit nomi (masalan, `local`, `staging`, `prod`).
- `CORS_ORIGINS`: Ruxsat etilgan originlar (vergul bilan ajratilgan yoki JSON list).
- `RATE_LIMIT_ENABLED`: Rate limit yoqilgan/yoqilmagan.
- `RATE_LIMIT_RPS`: 1 soniyadagi ruxsat etilgan so'rovlar soni.
- `RATE_LIMIT_BURST`: Qisqa burst limiti.
- `RUN_MIGRATIONS`: API startida migratsiyalarni avtomatik ishga tushirish.
- `WAVESPEED_API_BASE_URL`: Wavespeed provider API bazaviy manzili.
- `WAVESPEED_API_KEY`: Wavespeed API kaliti.
- `WAVESPEED_SEEDREAM_V4_T2I_URL`: Seedream v4 text-to-image endpoint.
- `WAVESPEED_SEEDREAM_V4_I2I_URL`: Seedream v4 image-to-image endpoint.
- `WAVESPEED_NANO_BANANA_T2I_URL`: Nano Banana text-to-image endpoint.
- `WAVESPEED_NANO_BANANA_I2I_URL`: Nano Banana image-to-image endpoint.
- `WAVESPEED_NANO_BANANA_PRO_T2I_URL`: Nano Banana Pro text-to-image endpoint.
- `WAVESPEED_NANO_BANANA_PRO_I2I_URL`: Nano Banana Pro image-to-image endpoint.
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`: Redis ulanish sozlamalari.
- `REDIS_ACTIVE_GENERATION_TTL_SECONDS`: Active generatsiya lock TTL.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `POSTGRES_HOST`, `POSTGRES_PORT`

## Namuna

```
BOT_TOKEN=123456:ABCDEF
API_BASE_URL=http://api:8000
API_TIMEOUT_SECONDS=60
APP_NAME=Bananapics API
APP_VERSION=0.1.0
API_PREFIX=/api/v1
ENVIRONMENT=local
CORS_ORIGINS=
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RPS=5
RATE_LIMIT_BURST=10
RUN_MIGRATIONS=true
WAVESPEED_API_BASE_URL=https://api.wavespeed.ai/api/v3
WAVESPEED_API_KEY=
WAVESPEED_SEEDREAM_V4_T2I_URL=https://api.wavespeed.ai/api/v3/bytedance/seedream-v4
WAVESPEED_SEEDREAM_V4_I2I_URL=https://api.wavespeed.ai/api/v3/bytedance/seedream-v4/edit
WAVESPEED_NANO_BANANA_T2I_URL=https://api.wavespeed.ai/api/v3/google/nano-banana/text-to-image
WAVESPEED_NANO_BANANA_I2I_URL=https://api.wavespeed.ai/api/v3/google/nano-banana/edit
WAVESPEED_NANO_BANANA_PRO_T2I_URL=https://api.wavespeed.ai/api/v3/google/nano-banana-pro/text-to-image
WAVESPEED_NANO_BANANA_PRO_I2I_URL=https://api.wavespeed.ai/api/v3/google/nano-banana-pro/edit
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_ACTIVE_GENERATION_TTL_SECONDS=900
POSTGRES_USER=bananapics
POSTGRES_PASSWORD=bananapics
POSTGRES_DB=bananapics
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

## Tayyorlash

1. `.env.example` faylini `.env` ga ko'chiring.
2. `BOT_TOKEN` ni real token bilan to'ldiring.

## Eslatma

- Tokenni ommaga oshkor qilmang.
- Token yangilansa, `docker compose up -d --build` bilan qayta ishga tushiring.
