# BananaPicsBot — Agent Instructions (Source of Truth)

This repository will contain a Telegram bot that generates images using multiple AI models (Nano Banana, Nano Banana Pro, SeeDream 4, GPT Image, and future providers). The bot supports reference images, user profiles, internal balance/tokens, Telegram Stars topups, referrals, admin full control, templates/trending, and a smooth inline-button UX.

## Non‑negotiable workflow rules (keep docs in sync)

1. **Docs are part of the product.** Any code change that alters behavior, UI, data, pricing, or config **must** update:
   - `AGENTS.md` (only if the “source of truth” changes)
   - The relevant file(s) in `docs/` (feature docs, model docs, DB/env docs, etc.)
2. **Env sync contract.** Any change to configuration must update **both**:
   - `.env.example` (safe sample values only)
   - `docs/ENV.md` (meaning, default, required/optional, examples)
3. **Schema sync contract.** Any DB/schema change must update:
   - `docs/DATABASE.md`
   - Migrations (when the codebase is added)
4. **Payments/referrals must be idempotent.** Any Stars payment handling or referral reward logic must be written so repeated webhook/events do not double-credit. Document the idempotency keys in the relevant docs.
5. **Safety & privacy.** Never commit secrets. Avoid logging prompts/images unless explicitly required and documented. Document data retention rules.

## Documentation map (what to update when)

- Product overview & flows: `docs/PRODUCT.md`
- System design & components: `docs/ARCHITECTURE.md`
- Tech stack decisions: `docs/TECH_STACK.md`
- Local setup/runbook: `docs/SETUP.md`
- Telegram UI (menus/buttons/state): `docs/TELEGRAM_BOT_UI.md`
- Features (per functional area): `docs/FEATURES/*.md`
- Model backends (per model/provider): `docs/MODELS/*.md`
- Database schema: `docs/DATABASE.md`
- Pricing/token costs: `docs/PRICING.md`
- Job queue & lifecycle: `docs/QUEUE_AND_JOBS.md`
- Environment variables: `docs/ENV.md`
- Security checklist: `docs/SECURITY.md`
- Logging/metrics: `docs/OBSERVABILITY.md`

## Expected repository shape (initial target; adjust only with documentation)

When implementation starts, prefer a clear separation:

- `apps/bot/` — Telegram bot (handlers, UI state machine, i18n, rate limits)
- `apps/api/` — HTTP API (admin endpoints, internal services)
- `apps/worker/` — background jobs (generation queue, callbacks, cleanup)
- `packages/core/` — shared domain: models, pricing, schemas, DB access
- `docs/` — documentation (this is mandatory)

If a different stack/layout is chosen, update `docs/TECH_STACK.md` and `docs/ARCHITECTURE.md` immediately.

## Core domain concepts (use consistent names)

- **User**: Telegram user + app profile (language, created_at, banned, roles)
- **Balance**: internal credits/tokens used for generations
- **Token**: internal unit for charging (not Telegram Stars). Mapping is configurable.
- **Transaction**: ledger entry (topup, spend, refund, referral reward, admin adjust)
- **Generation Job**: a requested generation with inputs, settings, status, outputs
- **Model Backend**: a provider adapter that accepts normalized inputs and returns outputs
- **Template Prompt**: reusable prompt + default settings
- **Trending**: curated templates or “quick picks” shown in a menu

## Quality bar (implementation phase)

When code is added:
- Use a **single source of truth** for pricing/token costs, model availability, and limits.
- Keep bot handlers thin; move business logic into services/domain modules.
- Add basic tests for critical logic: ledger accounting, payment fulfillment, referral payout, job state transitions.
- Ensure long-running generation runs asynchronously (queue/worker), not in the update handler.
