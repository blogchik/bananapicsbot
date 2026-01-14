# API tuzilmasi

## Qisqacha

- `app/main.py` - app factory va middleware/handlerlar ulash.
- `app/api/v1` - versiyalashgan routerlar.
- `app/core` - konfiguratsiya, logging, exception handlerlar.
- `app/middlewares` - request id va rate limit.
- `app/schemas` - umumiy response modellari.
- `app/deps` - dependency funksiyalar.
- `alembic/` - migratsiyalar (skelet).
  - Migratsiyalar uchun `alembic.ini` va `alembic/env.py` mavjud.

## Endpointlar

- `GET /` - root info.
- `GET /api/v1/health` - healthcheck (uptime, request id).
- `GET /api/v1/info` - API info.

## Middlewarelar

- `X-Request-ID` - request tracking.
- CORS - ruxsat etilgan originlar `.env` orqali.
- Rate limit - `RATE_LIMIT_*` sozlamalari bilan.

## Alembic

Ishga tushirish (API konteyneri ichida):

```
alembic -c /app/alembic.ini revision --autogenerate -m "init"
alembic -c /app/alembic.ini upgrade head
```
