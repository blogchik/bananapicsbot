# Pricing & Tokens (draft)

## 1) Tushunchalar

- **Stars**: Telegram ichidagi to‘lov birligi (real topup).
- **Token**: bot ichidagi ichki kredit (generation uchun sarflanadi).

Stars → Token konversiya:
- MVP: paketlar orqali (`STARS_PACKAGES_JSON`)
- Keyinroq: DB’dan boshqariladigan paketlar

## 2) Token cost hisoblash (draft)

Token cost “estimate” va “final” bo‘lishi mumkin.

Draft formula:

`cost = base(model) * size_multiplier(size) * quality_multiplier(steps) * ref_multiplier(ref_count) * outputs`

Misol multipliers:
- `size_multiplier`: 1:1=1.0, 16:9=1.2, 9:16=1.2
- `quality_multiplier`: low=0.8, med=1.0, high=1.3
- `ref_multiplier`: 0 refs=1.0, 1 ref=1.1, 2-4 refs=1.25

Qoida:
- multipliers va base cost **admin config** orqali boshqariladi.

## 3) Hold/Finalize/Refund

MVP’da tavsiya:
- “Generate” bosilganda `spend_hold` yoziladi va balansdan yechiladi.
- Job `succeeded` bo‘lsa: `spend_finalize` yozish optional (audit uchun).
- Job `failed/canceled` bo‘lsa: `refund` yoziladi.

Idempotency:
- hold uchun `hold:<job_id>`
- refund uchun `refund:<job_id>`
- finalize uchun `finalize:<job_id>`

## 4) Admin adjustments

Admin user balansini o‘zgartirganda:
- `admin_adjust` ledger transaction
- `admin_actions` log

## 5) Free trial (optional, policy)

Agar qo‘shilsa:
- 1 marta `trial_grant` yoki `admin_adjust` bilan tokens beriladi
- abuse prevention: telegram_user_id unique + device heuristics (keyinroq)

