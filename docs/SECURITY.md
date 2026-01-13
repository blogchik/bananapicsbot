# Security

## 1) Secrets

- Hech qachon `.env` commit qilinmaydi.
- API key/tokenlar faqat env orqali.
- Prod’da secret manager tavsiya: Doppler/1Password/AWS Secrets Manager.

## 2) Admin access

- Adminlar ro‘yxati env/config orqali seed qilinadi va DB’da role sifatida saqlanadi.
- Har admin action `admin_actions` ga yoziladi.

## 3) Payments (Telegram Stars)

- Payment eventlar **idempotent**: unique `telegram_charge_id` va `payload` bilan.
- Double-credit’ni DB constraint + transaction bilan to‘xtatish.

## 4) Abuse prevention

- Per-user rate limit (generate, topup, template spam).
- Prompt validation: max length, disallowed content.
- Reference images: file size/type limit (jpg/png/webp).

## 5) Data retention

MVP default:
- Generated images: 30–90 kun (config).
- Reference images: 7–30 kun (config).
- Prompts: saqlash/savodsiz loglash bo‘yicha admin policy (config).

## 6) PII minimalizm

Telegram user_id va username yetarli; telefon/email yig‘ilmaydi.

