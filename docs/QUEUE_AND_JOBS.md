# Queue & Generation Jobs (draft)

## 1) Nega queue kerak

Rasm generatsiya:
- sekin bo‘lishi mumkin (10–60s+)
- provider timeouts/rate limit bo‘ladi
Shuning uchun Telegram update handler bloklanmaydi; job queue orqali worker bajaradi.

## 2) Job lifecycle

Statuslar: `queued` → `running` → (`succeeded` | `failed` | `canceled`)

Maydonlar:
- `provider_job_id` (provider async bo‘lsa)
- `error_code`, `error_message` (safe)
- `completed_at`

## 3) Concurrency va locking

Worker jobni `running` ga o‘tkazayotganda:
- DB row lock / optimistic lock ishlatiladi
- har jobni faqat 1 worker bajaradi

## 4) Retry policy (draft)

Retry qilinadigan xatolar:
- timeout
- 5xx
- temporary rate limit (429) — backoff bilan

Retry qilinmaydigan xatolar:
- content policy block
- invalid input (prompt/ref image)
- insufficient balance (bu job yaratilishidan oldin tekshiriladi)

## 5) Cancellation

User “Cancel” bosishi mumkin:
- `queued` bo‘lsa: `canceled` + refund
- `running` bo‘lsa: provider cancel qo‘llasa — cancel request; bo‘lmasa “best-effort”

## 6) Storage va cleanup

- Reference rasmlar va generated rasmlar S3’da saqlanadi.
- Cleanup policy `docs/SECURITY.md` dagi retention bilan mos bo‘ladi.

