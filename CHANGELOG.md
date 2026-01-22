# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

### Changed
- Replaced global mutable dict with Redis for generation status tracking (improved concurrency and reliability)
- Updated localization files for improved clarity and consistency in image generation and watermark removal messages
- Code refactoring for improved readability and maintainability

### Fixed
- Added missing permissions for security job in CI/CD workflow
- Fixed generation status tracking race conditions with Redis-based solution
- Added `psycopg2-binary` dependency for entrypoint database wait script
- Added `start_period: 60s` to API health check to allow time for database migrations
- Increased health check retries from 5 to 10 for more stability during deployment

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

[Unreleased]: https://github.com/abduroziq/bananapicsbot/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/abduroziq/bananapicsbot/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/abduroziq/bananapicsbot/releases/tag/v0.1.0
