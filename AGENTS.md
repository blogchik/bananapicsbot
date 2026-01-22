# AGENTS

Ushbu loyiha uchun AI agentlar ishlash yo'riqnomasi.

## Loyihaning qisqa tavsifi

- Python 3.11 + aiogram asosidagi Telegram bot (professional grade).
- FastAPI backend Clean Architecture (Domain-driven Design).
- Docker Compose orqali ishga tushiriladi (bot, api, celery-worker, celery-beat, webapp, redis, db).
- Image generation (text-to-image, image-to-image) Wavespeed API.
- Balans/trial tizimi, referral system, Stars to'lovlar.

## Repo strukturasi

- `bot/` - Telegram bot (aiogram 3.x, professional structure)
- `api/` - FastAPI backend (Clean Architecture)
- `webapp/` - Web UI image preview
- `docs/` - hujjatlar
- `docker-compose.yml` - asosiy servislar
- `docker-compose.local.yml` - local override
- `.env` - konfiguratsiya (repoda yo'q)
- `.env.example` - env namunasi

## Bot arxitekturasi

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

## API arxitekturasi

```
api/app/
├── domain/         # Entities va interfaces
├── application/    # Use cases
├── infrastructure/ # Repositories, cache, logging
├── api/v1/         # FastAPI endpoints
├── worker/         # Celery tasks
├── core/           # Config
├── deps/           # Dependencies
├── db/             # SQLAlchemy models
└── schemas/        # Pydantic models
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
- **Localization**: Handlers must use `_` parameter from middleware, NEVER use `bot.get("_")` (it returns None).
- **Translation Keys**: All user-facing text must use `TranslationKey` enum from `bot/locales/base.py`.
- **Error Handling**: Use ApiError for API calls, TelegramBadRequest for bot operations.

## Build/lint/test commands

- Local run (all services): `docker compose up -d --build`
- Bot logs: `docker compose logs -f bot`
- API logs: `docker compose logs -f api`
- Stop services: `docker compose down`

### Lint/format (ruff)

- Lint (repo root): `ruff check bot/ api/`
- Format check: `ruff format --check bot/ api/`
- Auto-format: `ruff format bot/ api/`
- Ruff config: `ruff.toml` (line length 120, E/F/I/W)

### Tests (pytest)

- API test run: `cd api && pytest`
- Single file: `cd api && pytest tests/unit/test_pricing.py`
- Single test: `cd api && pytest tests/unit/test_pricing.py::test_credits_from_usd`
- Name filter: `cd api && pytest -k "pricing"`
- Async tests enabled via `api/pytest.ini` (`asyncio_mode = auto`)

### Migrations (alembic)

- Upgrade: `cd api && alembic upgrade head`
- New migration: `cd api && alembic revision -m "short_message"`
- Config: `api/alembic.ini`, auto-run in `api/entrypoint.sh` when `RUN_MIGRATIONS=true`

## Code style guidelines

### Imports

- Order: stdlib -> third-party -> local modules.
- Prefer explicit imports for clarity (avoid star imports).
- Use absolute imports within each service (e.g., `from app.core.config import get_settings`).

### Formatting

- Ruff formatter is the source of truth.
- Line length target: 120.
- Use trailing commas in multi-line collections and function signatures.

### Types

- Prefer modern type syntax: `list[str]`, `dict[str, Any]`, `X | None`.
- Use precise types for injected translators: `Callable[[TranslationKey, dict | None], str]`.
- Async code should return `Awaitable` or `AsyncIterator` where appropriate.

### Naming conventions

- snake_case for functions/variables/modules.
- PascalCase for classes and Pydantic models.
- UPPER_SNAKE_CASE for constants and env vars.
- Use descriptive names for handlers (`start_handler`, `payments_handler`).

### Error handling

- Bot: wrap API calls with `ApiError`, handle `TelegramBadRequest` for bot operations.
- API: use centralized exception handlers in `api/app/core/exceptions.py`.
- Raise `HTTPException` for client-visible errors; keep internal errors generic.

### Logging

- Use `get_logger(__name__)` and `structlog` for structured logs.
- Avoid printing; use the configured logger.
- Include request IDs in API logs via middleware.

### Internationalization

- All user-facing text must use `TranslationKey` enum.
- Use middleware-injected `_` function for translations.
- Never call `bot.get("_")` inside handlers.

## Architecture rules

- Bot: handlers should be thin; move business logic to `services/`.
- API: follow Clean Architecture boundaries (domain -> application -> infrastructure -> api).
- Use DI container patterns in `bot/core/container.py` for shared resources.
- Keep API schemas in `api/app/schemas` and return Pydantic models from endpoints.

## CI/CD rules

- CI uses ruff lint/format checks and pytest (see `.github/workflows/ci.yml`).
- Keep new changes passing: ruff + pytest (API).

## Cursor/Copilot rules

- No `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` found.
