# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.5] - 2026-02-12

### Added
- **Web Admin Panel** - Full-featured React-based admin dashboard
  - 🔐 Telegram Login Widget authentication with JWT
  - 📊 Dashboard with real-time statistics and charts
  - 👥 User management (search, view, ban/unban)
  - 💰 Credit adjustment system
  - 📢 Broadcast management
  - 💳 Payment history
  - 🖼️ Generation history
  - ⚙️ System settings management
  - 🎨 Model configuration
- Admin panel service added to docker-compose.yml (port 3034)
- Vite build arguments for environment variables (VITE_BOT_USERNAME, VITE_API_URL)
- CI/CD workflow support for building admin panel and webapp with Vite env vars

### Fixed
- **Critical**: Admin login authentication flow - aligned response schema with frontend expectations
  - Changed `token` field to `access_token` (OAuth2 standard)
  - Added `token_type` field to login response
  - Fixed infinite login redirect loop after successful authentication
- **Critical**: Vite environment variables not available at build time in CI/CD
  - Added build arguments to Dockerfiles (admin-panel, webapp)
  - Updated docker-compose.yml to pass build args
  - Updated GitHub Actions workflow to provide build args during image build
  - Fixed "Bot username not configured" error in admin panel

### Technical
- **Admin Panel Tech Stack**: React 18, TypeScript, Vite, Zustand, TanStack Query, Recharts, TailwindCSS
- **Build**: Multi-stage Docker build with Nginx for production
- **Security**: Telegram Login Widget HMAC verification, JWT authentication, admin-only access
- **API**: New admin endpoints for auth, stats, users, broadcasts, payments, generations, settings

## [0.1.4] - 2026-01-25

### Added
- **Telegram Mini App (Webapp)** - Full-featured React-based web application for AI image generation
  - Telegram WebApp SDK integration with initData authentication
  - Mobile-first responsive design with dark theme
  - Generation feed with real-time status updates
  - Composer bar with prompt input and image attachments (up to 3 images, 20MB max)
  - Fullscreen image viewer with swipe-to-close gesture
  - Bottom sheet action menu (copy, download, regenerate, delete)
  - Toast notification system
  - Safe area handling for iOS notch and Android navigation
  - Haptic feedback integration
  - TelegramGate security screen for non-Telegram access attempts
- Webapp service added to docker-compose.yml (port 3033)
- Comprehensive webapp documentation in `docs/webapp.md`
- Webapp code review report with 23 identified issues (`webapp/CODE_REVIEW_ISSUES.md`)

### Changed
- Updated README.md architecture diagram to include webapp service
- Enhanced API documentation with Telegram Mini App authentication details
- Updated functionality documentation with webapp features

### Technical
- **Webapp Tech Stack**: React 18, TypeScript, Vite, Zustand, Framer Motion, TailwindCSS
- **Build**: Multi-stage Docker build with Nginx for production
- **Security**: HMAC-SHA256 initData validation, 24h auth freshness check

## [0.1.3] - 2026-01-22

### Security
- **CVE-2024-53981**: Updated `python-multipart` from 0.0.9 to 0.0.18 to fix DoS vulnerability via malformed `multipart/form-data` boundary
- Updated `sentry-sdk` to version 2.19.2 for latest security patches

### Added
- Image processing tools with 5 new features:
  - Watermark remover (12 credits) - removes watermarks from images
  - Upscale 4K (60 credits) - upscales images to 2K/4K/8K using Ultimate Image Upscaler
  - Denoise (20 credits) - removes noise from images with Topaz AI (Normal/Strong/Extreme modes)
  - Restore (20 credits) - restores old photos, removes dust and scratches with Topaz AI
  - Enhance (30 credits) - enhances, sharpens and upscales images with Topaz AI
- QWEN model support with size parameter for text-to-image and image-to-image generation
- QWEN model emoji representation in generation callbacks
- Comprehensive project documentation in CLAUDE.md with architecture patterns, linting, and testing guidelines
- Legal documents: Privacy Policy, Terms of Service, and User Agreement
- Code of Conduct and Security Policy documents
- Cleanup tools for standardizing package naming format

### Changed
- Replaced global mutable dict with Redis for generation status tracking (improved concurrency and reliability)
- Updated localization files for improved clarity and consistency in image generation and watermark removal messages
- Code refactoring for improved readability and maintainability
- Improved README documentation to reflect current development and deployment setup

### Fixed
- Added missing permissions for security job in CI/CD workflow
- Fixed generation status tracking race conditions with Redis-based solution
- Added `psycopg2-binary` dependency for entrypoint database wait script
- Added `start_period: 60s` to API health check to allow time for database migrations
- Increased health check retries from 5 to 10 for more stability during deployment
- Resolved CI/CD deployment and annotation issues
- Organized imports in keyboard modules to pass ruff lint
- Formatted worker tasks with ruff for code consistency

### Improved
- CI/CD workflow now includes:
  - Security scanning with Trivy
  - Test coverage reporting with Codecov
  - Improved test requirements with coverage support

### Removed
- Removed unused dependencies from API requirements:
  - `python-jose[cryptography]` - was not used in codebase
  - `passlib[bcrypt]` - was not used in codebase
  - `psycopg2-binary` - replaced by asyncpg
  - `greenlet` - not needed with async SQLAlchemy
- Cleaned up unused code from worker tasks

## [0.1.1] - 2026-01-19

### Added
- Dynamic pricing system with real-time Wavespeed API integration
- Admin markup configuration via `GENERATION_PRICE_MARKUP` environment variable
- Price caching for 5 minutes in Redis to reduce API calls
- Prompt flow improvements with better user experience

### Changed
- Generation pricing now fetched dynamically from backend API
- Updated project version to 0.1.2 in codebase

## [0.1.0] - 2026-01-19

### Added
- Initial production release
- Telegram bot with aiogram 3.x
- FastAPI backend with Clean Architecture
- Multi-language support (Uzbek, Russian, English)
- User management and profile system
- Balance system with ledger entries
- Telegram Stars payment integration
- Referral system with 20 credit welcome bonus and 10% payment bonuses
- Image generation with multiple models:
  - seedream-v4
  - nano-banana
  - nano-banana-pro
  - gpt-image-1.5
- Celery background task processing
- Redis caching and FSM storage
- PostgreSQL database with Alembic migrations
- Docker Compose deployment setup
- CI/CD pipeline with GitHub Actions
- Comprehensive documentation

[Unreleased]: https://github.com/blogchik/bananapicsbot/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/blogchik/bananapicsbot/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/blogchik/bananapicsbot/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/blogchik/bananapicsbot/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/blogchik/bananapicsbot/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/blogchik/bananapicsbot/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/blogchik/bananapicsbot/releases/tag/v0.1.0
