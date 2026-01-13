# Feature: Reference rasmlar (multi-reference)

## Maqsad

User 1 yoki bir nechta reference rasm yuborib, generatsiyani “yo‘naltiradi” (remix/style/pose/identity).

## UX

- User “Add reference images” bosadi.
- User rasm yuboradi (1..N).
- Bot qabul qiladi, “Done” bosilganda next step.

## Limitlar (config)

- `MAX_REFERENCE_IMAGES` (default: 4)
- `MAX_REFERENCE_BYTES_EACH` (default: 5–10MB)
- `ALLOWED_MIME_TYPES`: `image/jpeg`, `image/png`, `image/webp`

## Saqlash

- Telegram’dan file download → object storage’ga upload
- DB’da storage path + metadata (width/height/hash)

## Provider mapping

Har provider turlicha qabul qiladi:
- Base64 inline
- Signed URL
- Multipart upload

Core’da “normalized” format:
- `references[]`: `{storage_url, weight, mode}`

`mode` misol:
- `style`
- `composition`
- `identity`

## Xavfsizlik

- Virus scan (keyinroq) yoki kamida MIME/size/extension validation.
- EXIF tozalash (privacy).

