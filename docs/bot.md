# Telegram bot ishga tushirish

## Talablar

- Docker va Docker Compose o'rnatilgan bo'lishi kerak.

## Ishga tushirish

1. `.env.example` faylini `.env` ga ko'chiring.
2. `.env` faylida `BOT_TOKEN` ni to'ldiring.
3. Quyidagini ishga tushiring:

```
docker compose up -d --build
```

## API servis

- API `http://localhost:8000` manzilda ishlaydi.
- Root info: `GET /`
- Healthcheck: `GET /api/v1/health`
- API info: `GET /api/v1/info`

## Postgres

- DB `localhost:5432` portda ishlaydi.

## Keyingi flow (reja)

- User `/start` bosadi va trial generatsiyadan foydalanadi.
- Balans to'ldiriladi va keyingi generatsiyalar balansdan yechiladi.
- Prompt + reference(lar) yuborilgach inline menyu ochiladi:
  - model, aspect ratio, style tanlash
  - generatsiya narxi ko'rsatilgan "Generate" tugmasi
- User bir vaqtda 5 tagacha generatsiya qila oladi.

## Bot menyulari

- Barcha tugmalar inline.
- Home menyu welcome message bilan chiqadi, faqat `Profile` inline tugmasi bor.
- Profile menyu: TG info + balans + trial holati, `Home` inline tugmasi bor.
- `/start` bosilganda oddiy reply keyboardlar tozalanadi.

## To'xtatish

```
docker compose down
```

## Loglar

```
docker compose logs -f bot
```
