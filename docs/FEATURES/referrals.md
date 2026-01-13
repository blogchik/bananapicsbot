# Feature: Referral system

## Maqsad

User do‘stini chaqiradi. Do‘st topup qilsa, referrer admin belgilagan % bo‘yicha bonus oladi.

## Referral link

- Format: `https://t.me/<bot>?start=ref_<code>`
- `code` — user uchun stable (masalan, base62(user_id) yoki random).

## Qoidalar (default)

- Referrer faqat bir marta biriktiriladi (birinchi start’da).
- Self-ref taqiqlanadi.
- Reward faqat topup bo‘lganda.
- Reward policy admin config:
  - `%` (0..100)
  - `apply_to`: `first_topup_only` yoki `all_topups`
  - minimal topup threshold (optional)

## Abuse prevention

- Bir xil device/account farm’ni kamaytirish uchun:
  - referal faqat “paid topup” bo‘lsa
  - admin review tools
  - suspicious activity flag (keyinroq)

## Hisoblash

Reward = `tokens_granted * percent / 100`

Ledger yozuvi:
- type=`referral_reward`
- `external_ref` = `payment:<payment_id>`
- `idempotency_key` = `ref_reward:<payment_id>`
