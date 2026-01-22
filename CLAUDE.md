# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram bot for AI image generation (text-to-image, image-to-image) using Wavespeed API. Microservices architecture with aiogram 3.x bot, FastAPI backend (Clean Architecture), Celery workers, PostgreSQL, and Redis.

## Commands

### Development
```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f bot
docker compose logs -f api
docker compose logs -f celery-worker

# Restart specific service
docker compose restart bot

# Stop all services
docker compose down
```

### Database Migrations
```bash
# Create new migration
docker compose exec api alembic -c /app/alembic.ini revision --autogenerate -m "description"

# Apply migrations
docker compose exec api alembic -c /app/alembic.ini upgrade head

# Rollback one migration
docker compose exec api alembic -c /app/alembic.ini downgrade -1
```

### Database Access
```bash
docker compose exec db psql -U bananapics -d bananapics
docker compose exec redis redis-cli
```

### Linting & Formatting
```bash
# Check code (ruff configured in ruff.toml, line length: 120)
ruff check bot/ api/

# Auto-fix issues
ruff check --fix bot/ api/

# Format code
ruff format bot/ api/
```

### Testing (API)
```bash
# Install test dependencies
pip install -r api/requirements-test.txt

# Run all tests
pytest api/

# Run single test file
pytest api/tests/unit/test_pricing.py

# Run with verbose output
pytest api/ -v
```

## Architecture

### Services (docker-compose.yml)
- **bot** (port: internal) - Telegram bot (aiogram 3.x)
- **api** (port: 9000) - FastAPI backend, runs migrations on startup
- **celery-worker** - Background task processor (concurrency: 4)
- **celery-beat** - Scheduled tasks
- **redis** (port: 6479) - Cache, FSM storage, Celery broker
- **db** (port: 5433) - PostgreSQL 16

### Bot Structure (`bot/`)
```
core/           # DI container, config, logging
handlers/       # Telegram handlers (commands/, callbacks/, messages/, payments/, admin/)
keyboards/      # Inline keyboard builders
middlewares/    # Error handling, i18n, throttling
services/       # Business logic layer
states/         # FSM states
locales/        # i18n translations (uz.py, ru.py, en.py, base.py)
infrastructure/ # API client, Redis, storage
```

### API Structure (`api/app/`)
```
domain/         # Entities and interfaces (Clean Architecture)
application/    # Use cases
infrastructure/ # Repositories, cache, logging
api/v1/         # FastAPI endpoints
worker/         # Celery tasks (celery.py)
core/           # Configuration
deps/           # FastAPI dependencies
db/             # SQLAlchemy models
schemas/        # Pydantic models
```
Migrations: `api/alembic/versions/`

## Critical Patterns

### Localization in Bot Handlers
Handlers MUST use `_` parameter from middleware, NEVER use `bot.get("_")` (returns None).

```python
# CORRECT
@router.message(Command("start"))
async def start_handler(message: Message, _) -> None:
    await message.answer(_(TranslationKey.WELCOME))

# WRONG - bot.get("_") returns None
_ = message.bot.get("_")
await message.answer(_(TranslationKey.WELCOME))
```

All user-facing text must use `TranslationKey` enum from `locales/base.py`.

### Adding Translations
1. Add key to `locales/base.py` TranslationKey enum
2. Add translations to `locales/uz.py`, `locales/ru.py`, `locales/en.py`
3. Use in handlers: `_(TranslationKey.YOUR_NEW_KEY)`

### Error Handling
- Use `ApiError` for API calls
- Use `TelegramBadRequest` for bot operations

### Ledger Balance System
User balance is calculated from ledger entries (`ledger_entries.amount` positive/negative).
Entry types: `deposit`, `generation`, `admin_adjustment`, `referral_bonus`, `refund`

### Caching Strategy
- L1 (Memory): 60s TTL, process-local
- L2 (Redis): 300s TTL, shared across processes
- User profiles: 5 min, Balances: 1 min, Model catalog: 10 min

### Celery Tasks (Async/Sync Boundary)
Celery tasks are synchronous. Use `run_async()` wrapper for async code:
```python
# In api/app/worker/tasks.py
@shared_task
def process_generation(request_id: str):
    run_async(_process_generation_async(request_id))
```
Tasks use `sync_session_factory` for database access. Rate limit: 20 Telegram messages/second.

### Repository Pattern (API)
All database operations go through repositories in `api/app/infrastructure/repositories/`:
- Base repository provides generic CRUD with async SQLAlchemy
- Specific repos: `user.py`, `generation.py`, `ledger.py`, `model.py`, `payment.py`
- Always use `AsyncSession` from dependency injection

## Key Entry Points
- `bot/main.py` - Bot entry point
- `bot/core/container.py` - Bot DI container
- `api/app/main.py` - FastAPI entry point
- `api/app/worker/celery.py` - Celery app and tasks

### Middleware Order (Bot)
Order matters (outer to inner): `LoggingMiddleware` → `ErrorHandlerMiddleware` → `I18nMiddleware` → `ThrottlingMiddleware` → `UserContextMiddleware`

## Environment
Required variables: `BOT_TOKEN`, `WAVESPEED_API_KEY`, `ADMIN_IDS`
Copy `.env.example` to `.env` before running.

## CI/CD
GitHub Actions workflow in `.github/workflows/ci.yml`. Deploys via SSH with `docker compose up`.

## Documentation
Keep `docs/` in sync with code changes:
- `docs/api.md` - API architecture and endpoints
- `docs/bot.md` - Bot architecture and flows
- `docs/functionality.md` - Feature documentation
- `docs/env.md` - Environment variables guide
