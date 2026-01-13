# Model: SeeDream 4

## Qisqacha

SeeDream 4 — “artistic/style” natijalar uchun (trending template’larda ko‘p ishlatilishi mumkin).

## Capability (draft)

- Text-to-image: yes
- Reference images: modelga bog‘liq (adapter capability orqali)
- Style presets: strong

Env:
- `SEEDREAM4_API_BASE_URL`
- `SEEDREAM4_API_KEY`

Integration notes (draft)

- Agar provider async job qaytarsa: `provider_job_id` saqlanadi, worker polling/callback qiladi.
- Agar sync bo‘lsa: worker bir martada natija oladi.

