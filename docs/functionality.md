# Bot funksionallari

## Hozirgi holat

- **Bot:** /start welcome message, inline menyular, reply keyboard tozalanadi.
- **Profil:** TG ma'lumotlari, balans, trial holati API orqali ko'rsatiladi.
- **Generatsiya:** prompt va reference rasm(lar) bilan menyu ochiladi, model/size/aspect ratio/resolution tanlanadi (size faqat `seedream-v4`, aspect ratio `nano-banana` va `nano-banana-pro`, resolution faqat `nano-banana-pro`), status avtomatik yangilanadi, natija yuboriladi.
- **Natija:** prompt va model nomi bilan xabar yuboriladi, rasmlar photo va file ko'rinishida jo'natiladi.
- **Cheklov:** user bir vaqtda faqat 1 ta generatsiya boshlaydi (Redis lock + DB advisory lock).
- **Aktiv holat:** aktiv generatsiya bor paytda yangi so'rov yuborilsa, bot kutishni so'raydi va oldingi generatsiya davom etadi.
- **Backend va saqlash:** FastAPI /api/v1, Postgres + Alembic, CORS, rate limit, request id, global error handling; requestlar `public_id` bilan unique, prompt/size/reference URL + telegram file id, input params, natijalar va joblar saqlanadi.
- **Model:** `seedream-v4`, `nano-banana`, `nano-banana-pro` (1 credit), text-to-image va image-to-image; `aspect_ratio` nano modellarda yoqilgan, `resolution` faqat `nano-banana-pro`, `size` faqat `seedream-v4`.
- **Model konfiguratsiya:** parametrlar va variantlar `/api/v1/models` javobidagi `model.options` orqali keladi, bot shunga moslashadi.

## Reja

- Qo'shimcha modellar va narxlar boshqaruvi.
- Queue/worker integratsiyasi va batch ishga tushirish.
- Admin balans boshqaruvi va to'lov integratsiyasi.
- Generatsiya tarixini ko'rish va qayta yuborish.
