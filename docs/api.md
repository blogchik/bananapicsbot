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
- `POST /api/v1/users/sync` - Telegram userni yaratish/sync.
- `GET /api/v1/users/{telegram_id}/balance` - user balansi (ledger asosida).
- `GET /api/v1/users/{telegram_id}/trial` - trial holati.
- `GET /api/v1/models` - aktiv modellarning ro'yxati va narxlari.

## Bot integratsiya

- Bot profile menyu uchun `users/sync`, `users/{telegram_id}/balance`, `users/{telegram_id}/trial` endpointlaridan foydalanadi.

## Rejalashtirilgan backend imkoniyatlar

- User balans va trial holatini saqlash.
- Generatsiya requestlarini (prompt, reference) saqlash.
- Model konfiguratsiyalari, narxlar va ruxsat etilgan parametrlar (aspect ratio, style).
- Queue/worker integratsiyasi (kelgusida).

## Ledger balans

- User balansi bitta ustun bilan emas, ledger yozuvlari orqali hisoblanadi.
- `ledger_entries.amount` musbat yoki manfiy bo'lishi mumkin.

## Ma'lumotlar modeli

- `model_catalog` - modellarning katalogi va qo'llab-quvvatlanadigan parametrlar.
- `model_prices` - model narxlari (credit asosida).
- `generation_requests` - prompt va tanlangan sozlamalar.
- `generation_references` - reference fayllar/linklar.
- `generation_results` - natijaviy rasm va meta.
- `generation_jobs` - provider bilan ishlash holati.
- `trial_uses` - trial ishlatilganligi.

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

## Migratsiyalarni ishga tushirish

- API konteyner startida avtomatik `alembic upgrade head` ishlaydi.
- Agar kerak bo'lsa, `.env` yoki compose orqali `RUN_MIGRATIONS=false` qilib o'chirish mumkin.
