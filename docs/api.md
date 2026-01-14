# API tuzilmasi

## Qisqacha

- `app/main.py` - app factory va middleware/handlerlar ulash.
- `app/api/v1` - versiyalashgan routerlar.
- `app/core` - konfiguratsiya, logging, exception handlerlar.
- `app/middlewares` - request id va rate limit.
- `app/schemas` - umumiy response modellari.
- `app/deps` - dependency funksiyalar.
- `alembic/` - migratsiyalar (skelet).
  - Migratsiyalar uchun `alembic.ini` va `alembic/env.py` mavjud.

## Endpointlar

- `GET /` - root info.
- `GET /api/v1/health` - healthcheck (uptime, request id).
- `GET /api/v1/info` - API info.
- `POST /api/v1/users/sync` - Telegram userni yaratish/sync.
- `GET /api/v1/users/{telegram_id}/balance` - user balansi (ledger asosida).
- `GET /api/v1/users/{telegram_id}/trial` - trial holati.
- `GET /api/v1/models` - aktiv modellarning ro'yxati va narxlari (`model.options` bilan).
- `POST /api/v1/generations/submit` - generatsiyani boshlash (Wavespeed job).
- `GET /api/v1/generations/active?telegram_id=...` - userdagi aktiv generatsiya holati.
- `GET /api/v1/generations/{id}?telegram_id=...` - generatsiya holati (userga bog'langan).
- `POST /api/v1/generations/{id}/refresh` - Wavespeed natijasini yangilash (body: `telegram_id`).
- `GET /api/v1/generations/{id}/results?telegram_id=...` - natija URLlar ro'yxati.
- `GET /api/v1/sizes` - bot uchun tayyorlangan size variantlari.
- Active generatsiya bo'lsa `409` qaytadi (`active_request_id` bilan, Redis lock + DB advisory lock).
- `POST /api/v1/media/upload` - Wavespeed media upload (multipart file).
  - Form field: `file`
  - Javob: `download_url`
  - `WAVESPEED_API_KEY` bo'lmasa 400 qaytadi.

## Bot integratsiya

- Bot profile menyu uchun `users/sync`, `users/{telegram_id}/balance`, `users/{telegram_id}/trial` endpointlaridan foydalanadi.

## Rejalashtirilgan backend imkoniyatlar

- User balans va trial holatini saqlash.
- Generatsiya requestlarini (prompt, reference) saqlash.
- Model konfiguratsiyalari, narxlar va ruxsat etilgan parametrlar (aspect ratio, resolution, size).
- Queue/worker integratsiyasi (kelgusida).

## Ledger balans

- User balansi bitta ustun bilan emas, ledger yozuvlari orqali hisoblanadi.
- `ledger_entries.amount` musbat yoki manfiy bo'lishi mumkin.

## Ma'lumotlar modeli

- `model_catalog` - modellarning katalogi va qo'llab-quvvatlanadigan parametrlar.
- `model_prices` - model narxlari (credit asosida).
- `generation_requests` - prompt va tanlangan sozlamalar.
- `generation_references` - reference fayllar/linklar.
- `generation_results` - natijaviy rasm va meta.
- `generation_jobs` - provider bilan ishlash holati.
- `trial_uses` - trial ishlatilganligi.

## Model katalogi

- Hozircha `seedream-v4`, `nano-banana`, `nano-banana-pro` modellari mavjud.
- `aspect_ratio` `nano-banana` va `nano-banana-pro` uchun yoqilgan, `resolution` faqat `nano-banana-pro`, `size` faqat `seedream-v4`.
- `model.options` (GET `/api/v1/models`) ichida parametrlar va variantlar keladi: `supports_size`, `supports_aspect_ratio`, `supports_resolution`, `size_options`, `aspect_ratio_options`, `resolution_options`.
- Model parametr konfiguratsiyasi `api/app/core/model_options.py` da markazlashgan.
- Narx: barcha modellarda 1 credit / generatsiya.
- Provider: `wavespeed`.
- `seedream-v4`, `nano-banana`, `nano-banana-pro` text-to-image va image-to-image ni qo'llab-quvvatlaydi.

## Wavespeed integratsiya (Seedream v4)

Text-to-image (T2I):
- Endpoint: `POST https://api.wavespeed.ai/api/v3/bytedance/seedream-v4`
- Header: `Authorization: Bearer $WAVESPEED_API_KEY`
- Request:
  - `prompt` (string, required)
  - `size` (string, default `2048*2048`, 1024-4096 per dimension)
  - `enable_base64_output` (bool, default false)
  - `enable_sync_mode` (bool, default false, bizda true)
- Result: `GET https://api.wavespeed.ai/api/v3/predictions/{id}/result`

Image-to-image (I2I):
- Endpoint: `POST https://api.wavespeed.ai/api/v3/bytedance/seedream-v4/edit`
- Header: `Authorization: Bearer $WAVESPEED_API_KEY`
- Request:
  - `prompt` (string, required)
  - `images` (array, required, 1-10 items)
  - `size` (string, optional)
  - `enable_base64_output` (bool, default false)
  - `enable_sync_mode` (bool, default false, bizda true)
- Result: `GET https://api.wavespeed.ai/api/v3/predictions/{id}/result`
- `images` uchun Wavespeed media upload ishlatiladi: `POST /api/v3/media/upload/binary`, javobdagi `data.download_url`.
  - Bizda `enable_sync_mode` yoqilgan, shuning uchun natija tez qaytishi mumkin.

Nano Banana (T2I/I2I):
- T2I: `POST https://api.wavespeed.ai/api/v3/google/nano-banana/text-to-image`
- I2I: `POST https://api.wavespeed.ai/api/v3/google/nano-banana/edit`
- Parametrlar: `aspect_ratio` (ixtiyoriy).

Nano Banana Pro (T2I/I2I):
- T2I: `POST https://api.wavespeed.ai/api/v3/google/nano-banana-pro/text-to-image`
- I2I: `POST https://api.wavespeed.ai/api/v3/google/nano-banana-pro/edit`
- Parametrlar: `aspect_ratio` (ixtiyoriy), `resolution` (ixtiyoriy: `1k`, `2k`, `4k`).

## Generatsiya parametrlar

- `size` ixtiyoriy, faqat `seedream-v4` uchun. Kiritilmasa Wavespeed default ishlaydi (T2I default `2048*2048`).
- `size` variantlari `model.options.size_options` orqali beriladi (GET `/api/v1/models`), `GET /api/v1/sizes` esa seedream uchun umumiy ro'yxat.
- `aspect_ratio` ixtiyoriy, faqat `nano-banana` va `nano-banana-pro` uchun; variantlar `model.options.aspect_ratio_options` orqali keladi.
- `resolution` ixtiyoriy, faqat `nano-banana-pro` uchun; variantlar `model.options.resolution_options` orqali keladi.
- `reference_urls` bo'lsa image-to-image ishlaydi, bo'lmasa text-to-image.
- `reference_file_ids` ixtiyoriy, Telegram file_id lar (URLlar bilan bir xil tartibda saqlanadi).
- Har bir generatsiya `public_id` (UUID) bilan unique identifikatsiya qilinadi.
- So'rov parametrlari `input_params` maydonida saqlanadi.

## Middlewarelar

- `X-Request-ID` - request tracking.
- CORS - ruxsat etilgan originlar `.env` orqali.
- Rate limit - `RATE_LIMIT_*` sozlamalari bilan.

## Alembic

Ishga tushirish (API konteyneri ichida):

```
alembic -c /app/alembic.ini revision --autogenerate -m "init"
alembic -c /app/alembic.ini upgrade head
```

## Migratsiyalarni ishga tushirish

- API konteyner startida avtomatik `alembic upgrade head` ishlaydi.
- Agar kerak bo'lsa, `.env` yoki compose orqali `RUN_MIGRATIONS=false` qilib o'chirish mumkin.
