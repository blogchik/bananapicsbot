# AGENTS

Ushbu loyiha uchun AI agentlar ishlash yo'riqnomasi.

## Loyihaning qisqa tavsifi

- Python + aiogram asosidagi Telegram bot.
- Docker Compose orqali ishga tushiriladi.
- Hozircha minimal: `/start` komandasi uchun welcome message yuboradi.
- Maqsad: Telegram orqali image generation (text-to-image, image-to-image) va balans/trial tizimi.

## Repo strukturasi

- `bot/` - bot kodi va Dockerfile
- `docs/` - hujjatlar
- `docker-compose.yml` - xizmatni ishga tushirish
- `.env` - konfiguratsiya (token)
- `.env.example` - env namunasi
- `api/` - FastAPI backend servis

## Asosiy fayllar

- `bot/app.py` - botning kirish nuqtasi
- `bot/config.py` - env konfiguratsiyasi
- `bot/routers.py` - router yig'uvchi
- `bot/handlers/start.py` - `/start` handler
- `bot/requirements.txt` - Python paketlar
- `bot/Dockerfile` - bot image build
- `api/app/main.py` - FastAPI kirish nuqtasi
- `api/app/api/v1` - versiyalashgan routerlar
- `api/app/core` - config, logging, exception handlerlar
- `api/app/middlewares` - request id va rate limit
- `api/alembic` - migratsiyalar
- `api/alembic.ini` - Alembic konfiguratsiya
- `api/app/db` - SQLAlchemy bazasi, session va modellari
- `api/app/schemas` - Pydantic schemalar
- `api/requirements.txt` - API paketlar
- `api/Dockerfile` - API image build
- `docs/env.md` - env sozlamalar
- `docs/bot.md` - ishga tushirish yo'riqnomasi
- `docs/functionality.md` - funksionallari
- `docs/api.md` - API tuzilmasi va endpointlar

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
