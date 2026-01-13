# Feature: Template Prompts

## Maqsad

User tayyor promptlarni tez ishlatadi. Admin template yaratadi va kategoriyalaydi.

## Template strukturasi

- title
- description
- prompt (placeholders bo‘lishi mumkin, masalan `{subject}`)
- default settings (aspect, style, model)
- category
- is_active

## UX

1) Templates → Category
2) Template → Preview
3) “Use” → prompt inputga template prompt qo‘yiladi (placeholders bo‘lsa userdan so‘raladi)

## Admin tools

- CRUD
- import/export (JSON) (keyinroq)

