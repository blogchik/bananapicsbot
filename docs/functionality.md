# Bot funksionallari

## Hozirgi holat

- Faqat `/start` komandasi uchun welcome message yuboradi.
- Handlerlar alohida modulga ajratilgan (`bot/handlers`), kengaytirish oson.
- FastAPI asosidagi `api` servis mavjud.
- API `GET /` root info endpointiga ega.
- API `GET /api/v1/health` (uptime, request id) va `GET /api/v1/info` endpointlari mavjud.
- Versiyalash `/api/v1` orqali amalga oshiriladi.
- CORS, rate limit, global error handling qo'shilgan.
- Postgres servis va Alembic skeleti qo'shilgan.

## Maqsadli funksionallar (reja)

- Telegram bot orqali image generation (text-to-image va image-to-image).
- Model turlari: Seedream v4, nano banana, nano banana pro, gpt image va boshqalar.
- Har bir user uchun balans tizimi.
- Balans ledger yozuvlari orqali hisoblanadi (alohida column emas).
- Trial generatsiya: har bir yangi user uchun 1 ta prompt (istalgan model).
- Generatsiya narxi modelga qarab hisoblanadi va balansdan yechiladi.
- User bir vaqtda 5 tagacha generatsiyani ishga tushira oladi.
- Prompt va reference (rasmlar) asosida requestlar saqlanadi.
- Inline menyu: model, aspect ratio, style tanlash va narx ko'rsatilgan "Generate" tugmasi.
- Generatsiya yakunida userga rasm, prompt, sozlamalar, model va ishlash vaqti yuboriladi.

## Reja

- Qo'shimcha komandalar va media ishlovlari keyingi bosqichlarda qo'shiladi.
