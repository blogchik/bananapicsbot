# Observability

## 1) Logging

- JSON structured logs.
- Har request/update uchun `correlation_id`:
  - Telegram update_id + user_id
  - generation job id

Log fields (minimum):
- `level`, `ts`, `service` (`bot`/`worker`/`api`)
- `user_id`, `job_id`, `payment_id`
- `event` (short key)
- `duration_ms` (if applicable)
- `error_code`, `error_message` (safe)

## 2) Metrics (key)

- `gen_jobs_queued/running/succeeded/failed`
- provider latency
- token spend / topup volume
- payment success rate
- referral payouts

## 3) Tracing (optional)

OpenTelemetry keyinroq qo‘shilishi mumkin (API + worker).

