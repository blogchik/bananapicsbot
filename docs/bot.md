# Telegram bot

Professional image generation bot with multi-instance scaling, Redis FSM storage, and internationalization.

## Architecture

```
bot/
├── main.py              # Entry point (polling/webhook)
├── core/                # Configuration, logging, DI container
├── infrastructure/      # API client, Redis client, FSM storage
├── locales/            # Internationalization (uz, ru, en)
├── middlewares/        # Logging, error handling, i18n, throttling
├── keyboards/          # Inline keyboard builders
├── states/             # FSM states
├── filters/            # Admin and chat type filters
├── services/           # Business logic layer
├── handlers/           # Request handlers
│   ├── commands/       # /start, /profile, /settings, /help
│   ├── callbacks/      # Inline button callbacks
│   ├── messages/       # Prompt and media handlers
│   ├── payments/       # Stars payment handlers
│   └── admin/          # Admin panel handlers
└── utils/              # Formatters, validators, helpers
```

## Features

- **Multi-instance scaling**: Redis FSM storage allows running multiple bot instances
- **Internationalization**: Supports Uzbek, Russian, and English languages with auto-detection from Telegram
  - All user-facing texts use translation keys defined in `locales/uz.py`, `locales/ru.py`, `locales/en.py`
  - I18n middleware injects `_` (LocalizationFunction) into handler data dict
  - Handlers must use `_` parameter from middleware, NOT `bot.get("_")`
- **Structured logging**: JSON logs with structlog, Sentry integration
- **Rate limiting**: Redis-based sliding window throttling
- **DI Container**: Singleton pattern for shared resources
- **Professional error handling**: Centralized error middleware with user-friendly messages
- **Admin panel**: Full-featured admin with stats, user management, credits, broadcast, refund
- **Generation timeout**: 5-minute timeout protection with automatic cleanup
- **Translation system**: All user-facing text uses translation keys for full localization

## Talablar

Docker va Docker Compose o'rnatilgan bo'lishi kerak.

## Environment Variables

```env
# Required
BOT_TOKEN=your_telegram_bot_token

# Optional
REDIS_URL=redis://redis:6379/0
API_BASE_URL=http://api:9000
ADMIN_IDS=686980246
USE_WEBHOOK=false
WEBHOOK_BASE_URL=https://your-domain.com
WEBHOOK_PATH=/webhook
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8080
RATE_LIMIT_MESSAGES=20
RATE_LIMIT_PERIOD=60
SENTRY_DSN=your_sentry_dsn
DEFAULT_LANGUAGE=uz
```

## Ishga tushirish

1. `.env.example` faylini `.env` ga ko'chiring.
2. `.env` faylida kerakli parametrlarni to'ldiring.
3. Quyidagini ishga tushiring:

```bash
docker compose up -d --build
```

## Modes

### Polling (default)

```env
USE_WEBHOOK=false
```

### Webhook

```env
USE_WEBHOOK=true
WEBHOOK_BASE_URL=https://your-domain.com
WEBHOOK_PATH=/webhook
```

## Bot menyulari

- Barcha tugmalar inline.
- Home menyu welcome message bilan chiqadi.
- Home menyu: `Rasm generatsiya qilish`, `Watermark olib tashlash`, `Profile` tugmalari.
- Profile menyu: ID + balans + taxminiy generatsiyalar.
- Referral menyu: maxsus link, referral soni va jami bonus.
- Admin panel: `/admin` (faqat admin_ids uchun).
- Topup menyu: kurs ko'rsatiladi.

## Buyruqlar

- `/start` - Home
- `/profile` - Profile
- `/topup` - Topup
- `/referral` - Referral

## Admin Panel

Admin panel inline buttons orqali ishlaydi:

- **📊 Statistics**: Overview, users, generations, revenue stats
- **👥 Users**: Search, list, view profile, ban/unban
- **💰 Add Credits**: Add or remove credits from user
- **📢 Broadcast**: Send message to filtered users with progress tracking
- **💸 Refund**: Two types of refunds:
  - **🎨 Credit Refund**: Refund credits used for generation (select generation to refund)
  - **⭐ Stars Refund**: Refund Telegram Stars payment via Telegram API and deduct credits from balance

### Broadcast Flow

1. Admin selects "📢 Broadcast" → "📤 New Broadcast"
2. Admin sends message (text/photo/video/audio/sticker)
3. Message preview shown
4. Admin selects user filter:
   - 👥 All Users
   - 🔥 Active (7 days)
   - 📊 Active (30 days)
   - 💰 With Balance
   - 💳 Paid Users
   - 🆕 New Users (7 days)
5. Admin optionally adds inline button (text + URL)
6. Preview shown with recipient count
7. Admin confirms → broadcast starts via Celery workers
8. Progress shown with real-time updates:
   - Sent count
   - Failed count
   - Blocked count (users who blocked the bot)
   - Progress bar with percentage
9. Admin can cancel running broadcast

### Stars Refund Flow

1. Admin selects "⭐ Stars Refund"
2. Admin enters user Telegram ID
3. System shows user balance and recent payments
4. Admin enters Stars amount to refund
5. System checks if balance >= credits equivalent
6. If valid, shows confirmation with: Stars amount, credits to deduct, new balance
7. On confirm: Calls Telegram refundStarPayment API, deducts credits via API
8. Shows success/error message

### Stars Refund Error Cases

Admin will see specific error messages for these cases:

- **User never paid with Stars**: "Bu foydalanuvchi hech qachon Stars bilan to'lov qilmagan"
- **All payments already refunded**: "Barcha to'lovlar allaqachon qaytarilgan"
- **Telegram refuses refund**: Shows specific Telegram API errors (chargeback, time limit, etc.)
- **Partial success**: If Stars refunded but credits deduction fails, shows warning to manually deduct

## Generatsiya flow

1. User prompt yoki reference rasm yuboradi
2. Bot menu ko'rsatadi: text-to-image yoki image-to-image sarlavhasi + model, size/aspect_ratio/resolution/quality/input_fidelity tanlash (modelga qarab)
   - Prompt blockquote formatda ko'rsatiladi
   - Promptsiz rasm yuborilsa, watermark remover taklif qilinadi (caption’da sarflangan kredit ko’rsatiladi)
3. Generate bosilganda so'rov yuboriladi
4. Status backend Celery poller orqali kuzatilib, natija tayyor bo'lganda botga push qilinadi:
   - "? Holat: Navbatda" (queue)
   - "? Natija tayyor" (completed) + faqat file yuboriladi (asl format saqlanadi)
   - Xatolik bo'lsa, sabab ko'rsatiladi va "Retry" tugmasi chiqadi
   - Xatolikda kredit/ trial avtomatik qaytariladi
5. Timeout: 5 minut (300 soniya)

## Localization

Bot supports 3 languages: Uzbek (uz), Russian (ru), English (en).

### Language Detection Flow

1. **Telegram language_code** - First check user's Telegram language
2. **Redis explicit setting** - If user changed language in settings
3. **DEFAULT_LANGUAGE** env variable - Fallback (default: `uz`)

### Translation System

- **Translation Keys**: Defined in `locales/base.py` as `TranslationKey` enum
- **Translation Dictionaries**: Stored in `locales/uz.py`, `locales/ru.py`, `locales/en.py`
- **Middleware**: `I18nMiddleware` detects language and injects `_` (LocalizationFunction) into handler data dict
- **Usage in Handlers**: Handlers MUST use `_` parameter from middleware, NOT `bot.get("_")`
- **Generation UI**: Model/size/aspect/resolution buttons use translation keys (incl. default label)
- **Stars Payments**: Invoice title/description and validation messages use translation keys

### Correct Handler Pattern

```python
@router.message(Command("start"))
async def start_handler(message: Message, _) -> None:
    # ✅ CORRECT: Use _ parameter from middleware
    await message.answer(_(TranslationKey.WELCOME))

@router.callback_query(F.data == "menu:profile")
async def profile_callback(call: CallbackQuery, _) -> None:
    # ✅ CORRECT: Use _ parameter
    await call.message.edit_text(_(TranslationKey.PROFILE_TITLE))
```

### Incorrect Pattern (NEVER USE)

```python
# ❌ WRONG: bot.get("_") returns None
_ = message.bot.get("_")
await message.answer(_(TranslationKey.WELCOME))

# ❌ WRONG: call.message.bot.get("_") returns None
_ = call.message.bot.get("_")
await call.message.edit_text(_(TranslationKey.PROFILE_TITLE))
```

### Why `bot.get("_")` Doesn't Work

- Middleware sets `data["_"]` in handler data dict
- Middleware does NOT set `bot["_"]` on bot object
- Calling `bot.get("_")` returns `None`
- Translation system falls back to default language (Uzbek) when translator is `None`

### Adding New Translations

1. Add key to `locales/base.py` TranslationKey enum
2. Add translations to `locales/uz.py`, `locales/ru.py`, `locales/en.py`
3. Use in handlers: `await message.answer(_(TranslationKey.YOUR_NEW_KEY))`

## API servis

- API `http://localhost:9000` manzilda ishlaydi.
- Healthcheck: `GET /api/v1/health`
- API info: `GET /api/v1/info`

## Loglar

```bash
docker compose logs -f bot
```

## To'xtatish

```bash
docker compose down
```
