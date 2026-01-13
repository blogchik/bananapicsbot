# Feature: Topup - Telegram Stars

## Maqsad

User bot ichida Stars orqali token sotib oladi. Hozircha boshqa to`lov yo`q, lekin keyin qo`shilishi mumkin.

## Telegram flow (high-level)

1) User paket tanlaydi
2) Bot `sendInvoice` yuboradi (Stars)
3) Telegram `pre_checkout_query` -> bot `answerPreCheckoutQuery(ok=true)`
4) Telegram `successful_payment` -> bot DB transaction:
   - `payments` yozuvi (unique `telegram_charge_id`)
   - `ledger_transactions` topup (idempotency key)
   - `balances` update

## Paketlar (config-driven)

Admin boshqaradi:
- `stars_amount` -> `tokens_granted`
- minimal/maximal

## Idempotency

Quyidagilar unique bo`lishi shart:
- `telegram_charge_id`
- invoice `payload` (bot yaratgan unique string)

Ledger idempotency key:
- `payment:<telegram_charge_id>`

## Refund policy (draft)

MVP: refunds admin-only (manual). Keyinroq Telegram policy'ga moslashtiriladi.
