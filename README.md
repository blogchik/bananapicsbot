# Bananapics Bot 🍌🎨

A professional Telegram bot for AI-powered image generation with integrated payment system, referral program, and admin panel.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-blue.svg)](https://docs.aiogram.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)

## 📖 Overview

Bananapics Bot is a production-ready Telegram bot that provides AI image generation services powered by Wavespeed API. Built with a clean architecture approach, it features a scalable multi-instance deployment, comprehensive payment system with Telegram Stars, and full internationalization support.

### Key Features

- 🎨 **AI Image Generation** - Text-to-image and image-to-image generation with multiple models
- 📱 **Telegram Mini App** - Modern React-based webapp with native mobile experience
- 💰 **Payment System** - Integrated Telegram Stars payments with dynamic exchange rates
- 👥 **Referral Program** - Automatic bonus system for referred users
- 🌍 **Multi-language Support** - Uzbek, Russian, and English localization
- 📊 **Admin Panel** - Comprehensive admin dashboard with statistics and user management
- 📢 **Broadcast System** - Targeted message broadcasting with progress tracking
- 🔒 **Security** - Rate limiting, input validation, and secure payment handling
- 📈 **Scalability** - Multi-instance bot support with Redis FSM storage
- 🛠️ **Professional Architecture** - Clean architecture with DDD principles

### Project Policies

- Code of Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Security Policy: [SECURITY.md](SECURITY.md)
- Legal: [legal/README.md](legal/README.md)

## 🏗️ Architecture

The project is built with a microservices architecture:

```
┌─────────────┐   ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
│ Telegram    │──▶│  FastAPI    │◀──│  Mini App    │   │ Admin Panel  │
│ Bot         │◀──│  API        │   │ (React)      │   │ (React)      │
│ (aiogram)   │   │ (Clean)     │   │              │   │              │
└─────────────┘   └─────────────┘   └──────────────┘   └──────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐    ┌──────▼──────┐   ┌────▼────┐
   │  Redis  │    │  PostgreSQL │   │ Celery  │
   │ (Cache) │    │   (Data)    │   │ Workers │
   └─────────┘    └─────────────┘   └─────────┘
```

### Services

- **bot** - Telegram bot interface (aiogram 3.x)
- **api** - FastAPI backend with Clean Architecture
- **webapp** - Telegram Mini App (React 18 + TypeScript + Vite)
- **admin-panel** - Web Admin Dashboard (React 18 + TypeScript + Vite)
- **celery-worker** - Background task processor for generations and broadcasts
- **celery-beat** - Scheduled tasks (cleanup, monitoring)
- **redis** - Caching, FSM storage, rate limiting, Celery broker
- **db** - PostgreSQL database with Alembic migrations

### Project Structure

```
bananapicsbot/
├── bot/                    # Telegram bot application
│   ├── core/              # DI container, config, logging
│   ├── handlers/          # Request handlers (commands, callbacks, messages)
│   ├── keyboards/         # Inline keyboard builders
│   ├── middlewares/       # Error handling, i18n, throttling
│   ├── services/          # Business logic layer
│   ├── states/            # FSM states
│   ├── locales/           # i18n translations (uz, ru, en)
│   └── infrastructure/    # API client, Redis, storage
│
├── api/                   # FastAPI application
│   ├── app/
│   │   ├── domain/        # Entities and interfaces
│   │   ├── application/   # Use cases
│   │   ├── infrastructure/# Repositories, cache, logging
│   │   ├── api/v1/        # FastAPI endpoints
│   │   ├── worker/        # Celery tasks
│   │   ├── core/          # Configuration
│   │   ├── deps/          # FastAPI dependencies
│   │   ├── db/            # SQLAlchemy models
│   │   └── schemas/       # Pydantic models
│   └── alembic/           # Database migrations
│
├── webapp/                # Telegram Mini App
│   ├── src/
│   │   ├── components/   # React UI components
│   │   ├── hooks/        # Custom React hooks (useTelegram)
│   │   ├── services/     # API client
│   │   ├── store/        # Zustand state management
│   │   └── types/        # TypeScript definitions
│   ├── Dockerfile        # Production build
│   └── vite.config.ts    # Vite configuration
│
├── admin-panel/           # Web Admin Dashboard
│   ├── src/
│   │   ├── components/   # React UI components
│   │   ├── pages/        # Page components
│   │   ├── api/          # API client
│   │   ├── stores/       # Zustand state management
│   │   └── lib/          # Utilities
│   ├── Dockerfile        # Production build
│   └── vite.config.ts    # Vite configuration
│
├── docs/                  # Project documentation
│   ├── api.md            # API architecture details
│   ├── bot.md            # Bot architecture details
│   ├── webapp.md         # Mini App documentation
│   ├── admin_panel.md    # Admin Panel documentation
│   ├── functionality.md  # Feature documentation
│   └── env.md            # Environment variables guide
│
├── docker-compose.yml    # Service orchestration
├── .env.example         # Environment template
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Wavespeed API Key (from [Wavespeed](https://wavespeed.ai))

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/blogchik/bananapicsbot.git
cd bananapicsbot
```

2. **Configure environment**

```bash
cp .env.example .env
```

Edit `.env` and set required variables:

```env
# Required
BOT_TOKEN=your_telegram_bot_token_here
WAVESPEED_API_KEY=your_wavespeed_api_key_here

# Admin (comma-separated Telegram user IDs)
ADMIN_IDS=123456789

# Optional but recommended
SENTRY_DSN=your_sentry_dsn
```

3. **Start services**

```bash
docker compose up -d --build
```

#### Local development compose (recommended)

This repository also includes a local compose file ([docker-compose.local.yml](docker-compose.local.yml)) that uses a separate env file.

```bash
cp .env.example .env.local
docker compose -f docker-compose.local.yml up -d --build
```

Make sure `.env.local` matches what the compose file expects (at minimum set `POSTGRES_*` and `REDIS_PASSWORD`, and update `REDIS_URL` if you use a Redis password).

4. **Check status**

```bash
docker compose ps
docker compose logs -f bot
```

5. **Access the bot**

Open Telegram and send `/start` to your bot.

### Accessing Services

- **Bot**: Your Telegram bot
- **Mini App (Webapp)**: http://localhost:3033 (Telegram required)
- **Admin Panel**: http://localhost:3034 (Telegram Login Widget)
- **API**: http://localhost:9000/api/v1/health
- **API docs**: http://localhost:9000/docs
- **Redis**: localhost:6479
- **PostgreSQL**: localhost:5433

## ⚙️ Configuration

### Core Configuration

| Variable            | Description                      | Default | Required |
| ------------------- | -------------------------------- | ------- | -------- |
| `BOT_TOKEN`         | Telegram bot token               | -       | ✅       |
| `WAVESPEED_API_KEY` | Wavespeed API key                | -       | ✅       |
| `ADMIN_IDS`         | Admin user IDs (comma-separated) | -       | ✅       |
| `DEFAULT_LANGUAGE`  | Default language (uz/ru/en)      | `uz`    | ❌       |

### Bot Configuration

| Variable               | Description                | Default                |
| ---------------------- | -------------------------- | ---------------------- |
| `BOT_MODE`             | Bot mode (polling/webhook) | `polling`              |
| `REDIS_URL`            | Redis connection URL       | `redis://redis:6379/0` |
| `API_BASE_URL`         | API base URL               | `http://api:9000`      |
| `RATE_LIMIT_MESSAGES`  | Messages per minute limit  | `30`                   |
| `RATE_LIMIT_CALLBACKS` | Callbacks per minute limit | `60`                   |

If you set a Redis password (`REDIS_PASSWORD`), make sure `REDIS_URL` includes it (example: `redis://:yourpass@redis:6379/0`).

### API Configuration

| Variable                            | Description                      | Default   |
| ----------------------------------- | -------------------------------- | --------- |
| `API_PREFIX`                        | API prefix path                  | `/api/v1` |
| `ENVIRONMENT`                       | Environment (local/staging/prod) | `local`   |
| `RATE_LIMIT_RPS`                    | Requests per second              | `5`       |
| `MAX_PARALLEL_GENERATIONS_PER_USER` | Max parallel generations         | `2`       |

### Payment Configuration

| Variable                     | Description                       | Default                   |
| ---------------------------- | --------------------------------- | ------------------------- |
| `STARS_ENABLED`              | Enable Stars payments             | `true`                    |
| `STARS_MIN_AMOUNT`           | Minimum Stars amount              | `70`                      |
| `STARS_PRESETS`              | Payment presets (comma-separated) | `70,140,210,350,700,1400` |
| `STARS_EXCHANGE_NUMERATOR`   | Exchange rate numerator           | `1000`                    |
| `STARS_EXCHANGE_DENOMINATOR` | Exchange rate denominator         | `70`                      |
| `REFERRAL_BONUS_PERCENT`     | Referral bonus percentage         | `10`                      |
| `REFERRAL_JOIN_BONUS`        | Bonus credits when referral joins | `20`                      |
| `GENERATION_PRICE_MARKUP`    | Admin markup added to base prices | `40`                      |

See [docs/env.md](docs/env.md) for complete configuration reference.

## 🎯 Features

### Image Generation

**Supported Models:**

- **seedream-v4** - 27 credits (size parameter)
- **nano-banana** - 38 credits (aspect ratio)
- **nano-banana-pro** - 140-240 credits (aspect ratio, resolution)
- **gpt-image-1.5** - Dynamic pricing (quality, input fidelity)
- **qwen** - 20 credits (size parameter, bilingual text rendering)

**Generation Types:**

- 📝 **Text-to-Image** - Generate images from text prompts
- 🖼️ **Image-to-Image** - Generate variations of existing images
- 🎨 **Watermark Removal** - Remove watermarks (12 credits)

**Features:**

- Multiple image inputs (1-10 images)
- Model-specific parameters (size, aspect ratio, resolution, quality)
- Real-time generation status tracking
- Automatic retry on failure with credit refund
- 5-minute timeout protection
- Results delivered as files (preserves original format)

### Payment System

- 💳 **Telegram Stars Integration** - Native in-app payments
- 📊 **Dynamic Exchange Rates** - Configurable Stars to credits conversion
- 🎁 **Preset Amounts** - Quick payment options
- 💰 **Custom Amounts** - Flexible payment amounts
- 📜 **Payment History** - Complete ledger tracking
- 💸 **Refund System** - Admin-controlled refunds for both Stars and credits

### Referral Program

- 🔗 **Unique Referral Links** - Each user gets a personal link
- 🎁 **Join Bonus** - 20 credits awarded immediately when someone joins via referral
- 💰 **Payment Commission** - 10% bonus on all referral payments (rounded up)
- 📊 **Statistics** - Track referral count and total bonuses
- 🔔 **Notifications** - Real-time alerts for new referrals
- 🛡️ **Fraud Prevention** - One-time referral binding, self-referral protection

### Admin Panel

Two ways to access admin features:

#### 1. Telegram Bot `/admin` Command
Quick access via bot for admin users:
- View statistics overview
- User management shortcuts
- Broadcast creation
- Quick actions

#### 2. Web Admin Dashboard
Full-featured web interface at http://localhost:3034 (or your domain):

**🔐 Authentication**
- Telegram Login Widget integration
- JWT-based authentication
- Admin-only access (based on ADMIN_IDS)
- Secure session management

**📊 Dashboard & Analytics**
- Real-time statistics with interactive charts
- User growth trends (daily, weekly, monthly)
- Generation analytics by model
- Revenue tracking and breakdowns
- Success rate monitoring
- Active users metrics (7d/30d)

**👥 User Management**
- Advanced search (by ID, username, name)
- Detailed user profiles
- Balance and transaction history
- Generation history
- Payment history
- Ban/unban users
- Credit adjustment with reason tracking
- Referral information

**💰 Credit Management**
- Add/remove credits from user balance
- View complete credit transaction ledger
- Track admin adjustments with reasons
- Generation refunds

**📢 Broadcast System**
- Create rich broadcasts (text, photo, video, audio, sticker)
- Advanced recipient filtering:
  - All users
  - Active users (7d/30d)
  - Users with balance
  - Paid users only
  - New users (last 7d)
- Custom inline buttons (text + URL)
- Real-time progress tracking
- Start, pause, cancel broadcasts
- Broadcast history and statistics
- Delivery metrics (sent, failed, blocked)

**💳 Payment Management**
- Global payment history
- Filter by status and date
- Payment analytics
- Stars refund system (via Telegram API)

**🖼️ Generation Management**
- Global generation history
- Filter by status (completed, failed, processing)
- View generation details
- Refund failed generations
- Queue status monitoring

**🎨 Model Management**
- View all available models
- Toggle model availability
- Update model names
- Adjust pricing
- Generation count by model

**⚙️ System Settings**
- Configure system parameters
- Update pricing markup
- Adjust referral bonuses
- Payment presets
- Real-time updates without restart

**📈 Charts & Visualizations**
- Daily user registration trends
- Generation volume over time
- Revenue trends
- Model usage breakdown
- Interactive Recharts visualizations

See [docs/admin_panel.md](docs/admin_panel.md) for detailed documentation.

### Internationalization

**Supported Languages:**

- 🇺🇿 Uzbek (uz)
- 🇷🇺 Russian (ru)
- 🇬🇧 English (en)

**Features:**

- Auto-detection from Telegram language settings
- User-configurable language in settings
- Consistent UI across all languages
- Translation system for all user-facing text

## 📚 API Documentation

### REST API

The API is available at `http://localhost:9000/api/v1`

**Health & Info:**

- `GET /health` - Health check
- `GET /info` - API information

**Users:**

- `POST /users/sync` - Sync user from Telegram
- `GET /users/{telegram_id}/balance` - Get user balance
- `GET /users/{telegram_id}/trial` - Get trial status

**Generations:**

- `POST /generations/submit` - Start generation
- `GET /generations/active` - Get active generation
- `GET /generations/{id}` - Get generation status
- `GET /generations/{id}/results` - Get generation results

**Payments:**

- `GET /payments/stars/options` - Get payment options
- `POST /payments/stars/confirm` - Confirm payment

**Admin:**

- `GET /admin/stats` - Get statistics
- `GET /admin/users` - List users
- `POST /admin/credits` - Adjust credits
- `POST /admin/broadcasts` - Create broadcast
- `POST /admin/broadcasts/{id}/start` - Start broadcast
- `POST /admin/broadcasts/{id}/cancel` - Cancel broadcast

See [docs/api.md](docs/api.md) for detailed API documentation.

## 🛠️ Development

### Running Locally

```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f bot
docker compose logs -f api
docker compose logs -f celery-worker

# Stop services
docker compose down

# Restart a service
docker compose restart bot
```

### Database Migrations

```bash
# Create a new migration
docker compose exec api alembic -c /app/alembic.ini revision --autogenerate -m "description"

# Apply migrations
docker compose exec api alembic -c /app/alembic.ini upgrade head

# Rollback
docker compose exec api alembic -c /app/alembic.ini downgrade -1
```

### Debugging

**Bot Logs:**

```bash
docker compose logs -f bot
```

**API Logs:**

```bash
docker compose logs -f api
```

**Celery Logs:**

```bash
docker compose logs -f celery-worker
docker compose logs -f celery-beat
```

**Database Access:**

```bash
docker compose exec db psql -U bananapics -d bananapics
```

**Redis CLI:**

```bash
docker compose exec redis redis-cli
```

## 🔒 Security

- ✅ Rate limiting on bot and API levels
- ✅ Input validation and sanitization
- ✅ Secure payment handling
- ✅ Environment-based secrets management
- ✅ No hardcoded credentials
- ✅ Docker network isolation
- ✅ Request ID tracking for audit
- ✅ Structured logging with Sentry integration

**Best Practices:**

- Never commit `.env` file
- Rotate tokens regularly
- Use strong database passwords
- Enable Sentry for production
- Monitor rate limit violations
- Review admin actions regularly

## 📊 Monitoring

### Health Checks

```bash
# Bot health (check logs)
docker compose logs --tail=50 bot

# API health
curl http://localhost:9000/api/v1/health

# Database health
docker compose exec db pg_isready -U bananapics

# Redis health
docker compose exec redis redis-cli ping
```

### Metrics

The system tracks:

- User activity (registrations, active users)
- Generation statistics (success rate, model usage)
- Payment metrics (revenue, average transaction)
- Error rates and types
- API response times

### Alerts

Configure Sentry for:

- Uncaught exceptions
- Payment failures
- API errors
- Generation failures
- Timeout errors

## 🚀 Deployment

### CI/CD (GitHub Actions)

This repo uses a GitHub Actions workflow ([.github/workflows/ci.yml](.github/workflows/ci.yml)) that:

- Runs `ruff` lint + format checks
- Runs API tests with Postgres + Redis services
- Runs a Trivy security scan
- Builds and pushes `api` and `bot` images to GHCR
- Deploys to production from `main` via SSH + `docker compose`

Notes:

- The Trivy SARIF upload requires GitHub Code Scanning to be enabled in the repo settings.
- Images are tagged using `docker/metadata-action` (including `sha-<shortsha>` tags). The production deploy uses `IMAGE_TAG=sha-<shortsha>`.

### Production deploy via GitHub Actions

The workflow deploy step connects to your server via SSH, writes the production `.env` from a secret, pulls the tagged images from GHCR, and runs `docker compose up -d`.

Required repository secrets (names used by the workflow):

- `SSH_KEY` (private key)
- `SSH_HOST` (server host/IP)
- `SSH_USERNAME` (SSH user)
- `PROD_ENV_FILE` (full `.env` file contents for production)

Server prerequisites:

- Docker + Docker Compose plugin installed
- Repo directory exists on server: `~/bananapicsbot/`
- GHCR pull access (the workflow logs in on the server before pulling)

### Production Checklist

- [ ] Set strong database password in `.env`
- [ ] Configure Sentry DSN
- [ ] Set appropriate rate limits
- [ ] Configure webhook mode (recommended for production)
- [ ] Set up domain and SSL certificate
- [ ] Configure CORS origins
- [ ] Set up backup strategy for PostgreSQL
- [ ] Enable Redis persistence
- [ ] Set up log aggregation
- [ ] Configure monitoring and alerting
- [ ] Test payment flow thoroughly
- [ ] Test admin panel functionality
- [ ] Test broadcast system with small audience first

### Webhook Mode

For production, webhook mode is recommended:

```env
BOT_MODE=webhook
WEBHOOK_URL=https://yourdomain.com/webhook
WEBHOOK_SECRET=your_random_secret
```

### Scaling

**Horizontal Scaling:**

- Run multiple bot instances (Redis FSM allows this)
- Scale Celery workers based on load
- Use Redis Cluster for high availability
- Use PostgreSQL replication

**Vertical Scaling:**

- Increase Celery worker concurrency
- Adjust rate limits
- Optimize database queries
- Add caching layers

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes following the code style
4. Ensure all tests pass (when available)
5. Update documentation if needed
6. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
7. Push to the branch (`git push origin feature/AmazingFeature`)
8. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints
- Write clear commit messages
- Add docstrings to functions/classes
- Keep functions small and focused
- Use dependency injection
- Follow Clean Architecture principles

### Documentation

- Update relevant documentation in `docs/`
- Keep README.md in sync with changes
- Document all environment variables
- Provide examples for new features

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright 2026 Jabborov Abduroziq

## 🙏 Acknowledgments

- [aiogram](https://docs.aiogram.dev/) - Modern Telegram Bot framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Wavespeed](https://wavespeed.ai/) - Image generation API
- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM

## 📞 Support

For questions or issues:

- Create an issue in this repository
- Check documentation in `docs/` folder
- Review existing issues and discussions

## 📋 Project Status

**Current Version:** 0.1.5

**Status:** Production Ready ✅

**Roadmap:**

- [ ] Additional payment methods
- [ ] More image generation models
- [ ] Generation history and favorites
- [ ] Batch generation support
- [ ] Advanced admin analytics
- [ ] API rate limiting by user
- [ ] Automated testing suite
- [ ] Performance optimization
- [x] Telegram Mini App (webapp)

---

Made with ❤️ for the AI art community
