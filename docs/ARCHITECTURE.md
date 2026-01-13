# Architecture

## 1) High-level komponentlar

Minimal, skalalanadigan arxitektura:

- **Telegram Bot App**: update handling, UI state, komandalari, invoice (Stars).
- **Core/Domain**: pricing, ledger, referral rules, job state machine.
- **Generation Orchestrator**: job yaratish, provider tanlash, retry, timeout.
- **Provider Adapters**: Nano Banana / Nano Banana Pro / SeeDream 4 / GPT Image integratsiyasi.
- **Worker**: queue’dan job olib rasm generatsiya qiladi, natijani storage’ga joylaydi, userga yuboradi.
- **DB (Postgres)**: users, balances, ledger, jobs, templates, admin actions.
- **Cache/Queue (Redis)**: job queue, rate limiting, temporary state.
- **Object Storage (S3-compatible)**: reference uploads, generated images.
- (Ixtiyoriy) **Admin Web**: katta admin panel (keyinroq); MVP’da bot ichida ham bo‘ladi.

## 2) Data flow

### 2.1 Generation (async)
1) Bot: user request → `generation_jobs` yoziladi (status=`queued`)
2) Ledger: token hold (spend reservation) yaratiladi
3) Worker: job oladi → provider adapterga normalized request yuboradi
4) Provider: image(s) qaytaradi → storage’ga upload → job `succeeded`
5) Ledger: hold finalize (spend) yoki fail bo‘lsa refund
6) Bot: userga media group / single image yuboradi + “Regenerate/Variations” tugmalari

### 2.2 Stars topup (idempotent)
1) Bot invoice → Telegram checkout
2) `successful_payment` → `payments` jadvaliga unique `telegram_charge_id` bilan yozish
3) Ledger: topup transaction yaratish (once)
4) Balance: token qo‘shish

### 2.3 Referral reward
1) Payment processed → “eligible?” tekshiruv (referrer bor, self-ref emas, qoidalar)
2) Ledger: referral reward transaction (once, idempotent by payment_id)

## 3) State machine (generation_jobs)

- `queued` → `running` → (`succeeded` | `failed` | `canceled`)

Qoidalar:
- `running` statusga o‘tishda lease/lock (worker crash bo‘lsa retry).
- `failed` bo‘lsa: refund + error reason + retry policy.

## 4) Multi-model abstraction

Provider adapterlar bitta interface orqali:

- Input: `prompt`, `negative_prompt`, `size/aspect`, `seed`, `steps`, `cfg`, `style`, `references[]`, `safety_level`, `n_outputs`
- Output: `images[]` (url/path), `provider_job_id`, `metadata`, `usage` (cost/tokens)

## 5) Key risklar va mitigatsiya

- **Double credit** (payment/referral): DB unique constraints + idempotency.
- **Prompt abuse**: content policy + blocklist + per-user rate limit.
- **Large images**: upload limit + compression + storage lifecycle.
- **Provider outage**: fallback model, retry with backoff, status page.

