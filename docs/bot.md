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
- Profile menyu: TG info + balans + trial holati, `Balans to'ldirish`, `Referral` va `Home` inline tugmalari bor.
  - Balans to'ldirish: Telegram Stars (min 70 ⭐), 6 ta preset va custom summa. Kurs ko'rsatiladi, preset tugmalarda Stars → credit ko'rinadi, to'lovdan keyin qabul qilingan Stars va qo'shilgan credit xabarda beriladi.
- Referral menyu: user uchun maxsus link (masalan `https://t.me/BananaPicBot?start=r_<code>`), referral soni va jami bonus ko'rsatiladi. Yangi referral bo'lganda referrerga xabar boradi. User faqat bitta referrerni oladi va o'ziga referal bo'la olmaydi. Referral faqat yangi userlar uchun ishlaydi.
- `/start` bosilganda oddiy reply keyboardlar tozalanadi.
- Admin buyruqlar: `/pay USER_ID CREDITS`, `/refund USER_ID STARS` (faqat `686980246`).

## Generatsiya flow

- User prompt yoki reference rasm yuboradi (rasmni foto yoki fayl ko'rinishida yuborish mumkin, faqat image; 1-10 ta reference; rasm doim prompt bilan birga yuboriladi).
- Reference rasm backend orqali Wavespeed media upload qiladi.
- Menu: Model tanlash (`seedream-v4`, `nano-banana`, `nano-banana-pro`), Seedream uchun `Size`, Nano Banana(lar) uchun `Aspect ratio`, faqat Nano Banana Pro uchun `Resolution`, Generate.
- Parametrlar ro'yxati `GET /api/v1/models` dagi `model.options` orqali keladi va bot shunga moslashadi.
- `Generate` bosilganda `/api/v1/generations/submit` ishlaydi.
- Status avtomatik yangilanadi (har 2 sekundda), faqat 3 holat: navbatda, jarayonda, tayyor.
- Natija tayyor bo'lsa file ko'rinishidagi natijaga caption biriktiriladi (model hashtag, prompt blockquote, vaqt, credit).
- Status xabari tayyor bo'lganda o'chiriladi, natija esa prompt xabariga reply bo'lib yuboriladi.
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
