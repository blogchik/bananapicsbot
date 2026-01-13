# Feature: Advanced settings (generation paytida)

## Maqsad

User “pro” sozlamalar bilan natijani boshqaradi, lekin UI sodda qoladi.

## Sozlamalar ro‘yxati (draft)

Common:
- `aspect_ratio` / `size` (1:1, 3:4, 4:3, 9:16, 16:9)
- `style_preset` (none, cinematic, anime, photoreal, illustration, etc.)
- `seed` (random/custom)
- `steps` (quality/speed)
- `cfg` / guidance
- `n_outputs`
- `safety_level`

Reference-specific:
- `reference_strength` (0..1)
- `reference_weights[]`

## Storage

- Per-user default settings (profil)
- Per-job overrides (job settings_json)

## Validation

Har model uchun supported ranges turlicha:
- adapter “capabilities” qaytaradi
- UI faqat valid optionlarni ko‘rsatadi

