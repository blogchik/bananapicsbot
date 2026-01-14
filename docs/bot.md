# Telegram bot ishga tushirish

## Talablar

Docker va Docker Compose o'rnatilgan bo'lishi kerak.

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

## Bot menyulari

- Barcha tugmalar inline.
- Home menyu welcome message bilan chiqadi, faqat `Profile` inline tugmasi bor.
- Profile menyu: TG info + balans + trial holati, `Home` inline tugmasi bor.
- `/start` bosilganda oddiy reply keyboardlar tozalanadi.

## Generatsiya flow

- User prompt yoki reference rasm yuboradi.
- Reference rasm backend orqali Wavespeed media upload qiladi.
- Menu: Model tanlash (`seedream-v4`, `nano-banana`, `nano-banana-pro`), Seedream uchun `Size`, Nano Banana(lar) uchun `Aspect ratio`, faqat Nano Banana Pro uchun `Resolution`, Generate.
- Parametrlar ro'yxati `GET /api/v1/models` dagi `model.options` orqali keladi va bot shunga moslashadi.
- `Generate` bosilganda `/api/v1/generations/submit` ishlaydi.
- Status avtomatik yangilanadi (refresh tugmasi yo'q).
- Natija tayyor bo'lsa prompt va model nomi bilan xabar yuboriladi.
- Natijalar oddiy rasm va fayl ko'rinishida yuboriladi.
- User bir vaqtning o'zida faqat 1 ta generatsiya boshlaydi.
- Aktiv generatsiya mavjud bo'lsa, yangi so'rovda bot kutishni so'raydi.

## To'xtatish

```
docker compose down
```

## Loglar

```
docker compose logs -f bot
```
