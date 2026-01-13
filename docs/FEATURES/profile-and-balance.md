# Feature: Profil, balans va tokenlar

## Profil

Ko`rsatish:
- user info (username, id)
- referral link
- language
- settings shortcut

## Balans

- `token_balance` (internal)
- "Transaction history" (last N)
- "Top up" (Stars)

## Ledger qoidalari

Balans "transactional" bo`lishi kerak:
- `topup` -> +tokens
- `spend_hold` -> -tokens (reserved)
- `spend_finalize` -> 0 yoki final delta (agar hold finalize alohida yuritilsa)
- `refund` -> +tokens
- `admin_adjust` -> +/-tokens
- `referral_reward` -> +tokens

MVP'da soddaroq: hold ham real yechish bo`lishi mumkin, finalize faqat metadata.

## Balance update (implementatsiya eslatmasi)

- Balans faqat ledger orqali o`zgaradi.
- Har yozuvda `balances` jadvali row-level lock bilan yangilanadi.
- Idempotency key qayta tushsa, yangi ledger yozilmaydi.
