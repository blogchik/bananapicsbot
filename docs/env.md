# Env sozlamalari

- `BOT_TOKEN`: Telegram bot tokeni. `.env` ichida saqlanadi.
- `API_BASE_URL`: API bazaviy manzili (ko'rsatilmasa `http://api:8000`).
- `APP_NAME`: API nomi.
- `APP_VERSION`: API versiyasi.
- `API_PREFIX`: API prefiksi (default: `/api/v1`).
- `ENVIRONMENT`: Muhit nomi (masalan, `local`, `staging`, `prod`).
- `CORS_ORIGINS`: Ruxsat etilgan originlar (vergul bilan ajratilgan yoki JSON list).
- `RATE_LIMIT_ENABLED`: Rate limit yoqilgan/yoqilmagan.
- `RATE_LIMIT_RPS`: 1 soniyadagi ruxsat etilgan so'rovlar soni.
- `RATE_LIMIT_BURST`: Qisqa burst limiti.
- `RUN_MIGRATIONS`: API startida migratsiyalarni avtomatik ishga tushirish.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `POSTGRES_HOST`, `POSTGRES_PORT`

## Namuna

```
BOT_TOKEN=123456:ABCDEF
APP_NAME=Bananapics API
APP_VERSION=0.1.0
API_PREFIX=/api/v1
ENVIRONMENT=local
CORS_ORIGINS=
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RPS=5
RATE_LIMIT_BURST=10
RUN_MIGRATIONS=true
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
