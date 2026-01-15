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
- **Internationalization**: Supports Uzbek, Russian, and English languages
- **Structured logging**: JSON logs with structlog, Sentry integration
- **Rate limiting**: Redis-based sliding window throttling
- **DI Container**: Singleton pattern for shared resources
- **Professional error handling**: Centralized error middleware with user-friendly messages
- **Admin panel**: Full-featured admin with stats, user management, credits, broadcast, refund

## Talablar

Docker va Docker Compose o'rnatilgan bo'lishi kerak.

## Environment Variables

```env
# Required
BOT_TOKEN=your_telegram_bot_token

# Optional
REDIS_URL=redis://redis:6379/0
API_BASE_URL=http://api:8000
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
- Profile menyu: TG info + balans + trial holati.
- Settings menyu: Til tanlash (uz/ru/en).
- Referral menyu: maxsus link, referral soni va jami bonus.
- Admin panel: `/admin` (faqat admin_ids uchun).

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
2. Bot menu ko'rsatadi: model, size/aspect_ratio/resolution tanlash
3. Generate bosilganda so'rov yuboriladi
4. Status avtomatik yangilanadi (polling)
5. Natija tayyor bo'lsa rasm va file yuboriladi

## API servis

- API `http://localhost:8000` manzilda ishlaydi.
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
