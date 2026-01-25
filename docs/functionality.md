# Bot funksionallari

## Hozirgi holat

- **Bot:** /start welcome message, inline menyular, reply keyboard tozalanadi.
- **Profil:** TG ma'lumotlari, balans, trial holati API orqali ko'rsatiladi.
- **Balans to'ldirish:** Telegram Stars orqali (min 70 ⭐, 6 ta preset + custom). Kurs ko'rsatiladi, preset tugmalarda Stars → credit ko'rinadi, to'lovdan keyin qabul qilingan Stars va qo'shilgan credit xabarda beriladi. To'lovlar ledgerda saqlanadi.
- **Admin buyruqlar:** faqat admin user (`686980246`) uchun `/pay` bilan kredit qo'shish va `/refund` bilan Stars refund.
- **Stars Refund:** Admin user ID kiritadi, Telegram API dan unrefunded to'lovlar olinadi, har biri button sifatida ko'rsatiladi (sana, vaqt, summa), admin tanlangan to'lovni refund qiladi.
- **Referral:** har bir userda referral link bor. Yangi referral qo'shilganda referrerga darhol 20 credit beriladi. Referral orqali kelgan user to'lov qilsa 10% (round up) bonus referrerga darhol tushadi. Bitta user faqat bitta referrerni oladi va o'ziga referal bo'la olmaydi. Referral faqat yangi userlar uchun ishlaydi. User referral soni va jami bonusni ko'radi (kimlar ekanligi ko'rsatilmaydi). Yangi referral bo'lganda referrerga xabar boradi.
- **Generatsiya:** prompt va reference rasm(lar) bilan menyu ochiladi, reference rasm foto yoki fayl ko'rinishida yuborilishi mumkin (faqat image, 1-10 ta, doim prompt bilan birga), model/size/aspect ratio/resolution tanlanadi (size faqat `seedream-v4` va `qwen`, aspect ratio `nano-banana` va `nano-banana-pro`, resolution faqat `nano-banana-pro`), status backend Celery poller orqali kuzatilib, tayyor bo'lganda status xabari o'chadi va natija prompt xabariga reply bo'ladi.
- **Parallel limit:** bitta user uchun bir paytda maksimal `MAX_PARALLEL_GENERATIONS_PER_USER` ta generatsiya ruxsat etiladi (default: `2`).
- **Natija caption:** model hashtag, prompt blockquote va sarflangan credit ko'rsatiladi (file ko'rinishidagi natijada).
- **Natija:** prompt va model nomi bilan xabar yuboriladi, rasmlar faqat file ko'rinishida jo'natiladi (asl format saqlanadi).
- **Cheklov:** user bir vaqtda faqat 1 ta generatsiya boshlaydi (Redis lock + DB advisory lock).
- **Aktiv holat:** aktiv generatsiya bor paytda yangi so'rov yuborilsa, bot kutishni so'raydi va oldingi generatsiya davom etadi.
- **Backend va saqlash:** FastAPI /api/v1, Postgres + Alembic, CORS, rate limit, request id, global error handling; requestlar `public_id` bilan unique, prompt/size/reference URL + telegram file id, input params, natijalar va joblar saqlanadi.
- **Model:** `seedream-v4`, `nano-banana`, `nano-banana-pro`, `gpt-image-1.5`, `qwen`. Barcha modellar uchun narxlar dinamik ravishda API (`/api/v1/generations/price`) orqali olinadi. Wavespeed API real-time narxlariga asoslanadi. `gpt-image-1.5` narxi quality va size parametrlariga qarab o'zgaradi. `qwen` size parametri mavjud.
- **Narx qo'shimchasi:** Admin `.env` faylida `GENERATION_PRICE_MARKUP` parametri orqali barcha model narxlariga qo'shiladigan qo'shimcha miqdorni belgilaydi (creditlarda). Masalan, Wavespeed 240 credit ko'rsatsa va markup 40 bo'lsa, user 280 credit to'laydi. Bu backend tomonida avtomatik qo'shiladi va barcha narxlar bu qo'shimcha bilan saqlanadi.
- **Caching:** Bot tarafida narxlar (model va parametrlar bo'yicha) 5 daqiqa davomida Redis da cache qilinadi. Bu API so'rovlarini kamaytiradi va narx barqarorligini ta'minlaydi. Cache qilingan narxlar allaqachon markup bilan birga saqlanadi.
- **Model parametrlari:** `seedream-v4` (size), `nano-banana`, `nano-banana-pro` (aspect_ratio, resolution: `4k` uchun qimmatroq), `gpt-image-1.5` (size, quality, input_fidelity), `qwen` (size).
- **Model konfiguratsiya:** parametrlar va variantlar `/api/v1/models` javobidagi `model.options` orqali keladi, bot shunga moslashadi.
- **Broadcast:** Admin broadcast menyusidan yangi broadcast yaratadi, xabar yuboradi (text/photo/video/audio/sticker), filter tanlaydi (all/active_7d/active_30d/with_balance/paid_users/new_users), ixtiyoriy inline button qo'shadi, preview ko'radi va tasdiqlaydi. Celery worker rate limit bilan yuboradi (20 msg/sec). Progress va statistika real-time ko'rinadi (sent/failed/blocked). Broadcast bekor qilish mumkin.

### Image Tools

User rasm yuborib, unga turli xil ishlov berish toollarni tanlay oladi:

- **Watermark Remover** (12 credit) — rasmdan watermark olib tashlaydi
- **Upscale 4K** (60 credit) — rasmni 2K/4K/8K gacha kattalashtiradi (Ultimate Image Upscaler)
- **Denoise** (20 credit) — rasmdan shovqin olib tashlaydi (Topaz AI, Normal/Strong/Extreme)
- **Restore** (20 credit) — eski rasmlarni tiklaydi, chang va tirnalishlarni olib tashlaydi (Topaz AI)
- **Enhance** (30 credit) — rasmni yaxshilaydi, keskinlashtiradi va upscale qiladi (Topaz AI)

## Telegram Mini App (Webapp)

BananaPics Telegram Mini App - mobil-first interfeys:

### Asosiy xususiyatlar

- **Generation feed** - barcha generatsiyalar ro'yxati
- **Composer bar** - prompt kiritish va reference rasm qo'shish
- **Fullscreen viewer** - rasmlarni to'liq ekranda ko'rish
- **Toast notifications** - status xabarlari

### Xavfsizlik

- **initData validatsiya** - faqat Telegram orqali ochish mumkin
- **TelegramGate** - browser orqali ochilsa bloklangan ekran
- **API authentication** - barcha so'rovlar initData bilan himoyalangan

### Cheklovlar

- Maximum 3 ta reference rasm
- 20MB maksimal fayl hajmi
- JPG, PNG, WebP, GIF, BMP, TIFF formatlar

Batafsil: [webapp.md](webapp.md)

## Reja

- Qo'shimcha modellar va narxlar boshqaruvi.
- Queue/worker integratsiyasi va batch ishga tushirish.
- Admin balans boshqaruvi va to'lov integratsiyasi.
- Generatsiya tarixini ko'rish va qayta yuborish.
