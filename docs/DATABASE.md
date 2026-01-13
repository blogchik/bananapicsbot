# Database Schema (draft)

Bu schema MVP uchun “target”. Implementatsiyada migrations bilan sinxron yuritiladi.

## 1) Asosiy tamoyillar

- **Ledger-first**: balansni “hisoblab” emas, transaction ledger orqali yuritish.
- **Idempotency**: payment/referral/admin adjustments uchun unique keys.
- **Audit**: admin actionlar alohida loglanadi.

## 2) Jadvallar

### `users`
- `id` (pk)
- `telegram_user_id` (unique)
- `username`, `first_name`, `last_name`
- `language` (default: `uz`)
- `role` (`user`/`admin`/`support`)
- `is_banned` (bool)
- `referrer_user_id` (fk -> users.id, nullable)
- `created_at`, `updated_at`

### `balances`
- `user_id` (pk, fk -> users.id)
- `token_balance` (numeric/int)
- `updated_at`

### `ledger_transactions`
Har bir pul/token harakati.
- `id` (pk)
- `user_id` (fk)
- `type` (`topup`, `spend_hold`, `spend_finalize`, `refund`, `referral_reward`, `admin_adjust`)
- `amount_tokens` (+/-)
- `currency` (nullable; Stars uchun `XTR` yoki internal)
- `external_ref` (nullable; masalan `payment:<id>`)
- `idempotency_key` (unique, nullable)
- `metadata_json`
- `created_at`

### `payments`
Telegram Stars invoice fulfillment.
- `id` (pk)
- `user_id` (fk)
- `provider` (`telegram_stars`)
- `telegram_charge_id` (unique)
- `payload` (invoice payload, unique)
- `stars_amount`
- `tokens_granted`
- `status` (`pending`, `paid`, `refunded`, `failed`)
- `created_at`, `paid_at`

### `generation_jobs`
- `id` (pk)
- `user_id` (fk)
- `model_key` (e.g. `nano_banana`, `gpt_image`)
- `prompt`, `negative_prompt`
- `settings_json` (aspect, steps, cfg, seed, style, etc.)
- `reference_images_json` (paths/urls + weights)
- `status` (`queued`, `running`, `succeeded`, `failed`, `canceled`)
- `token_cost_estimated`
- `ledger_hold_tx_id` (fk -> ledger_transactions.id)
- `provider_job_id` (nullable)
- `error_code`, `error_message`
- `created_at`, `updated_at`, `completed_at`

### `generated_images`
- `id` (pk)
- `job_id` (fk -> generation_jobs.id)
- `storage_url` (or path)
- `width`, `height`, `mime_type`, `bytes`
- `metadata_json`
- `created_at`

### `template_prompts`
- `id` (pk)
- `title`, `description`
- `prompt`
- `default_settings_json`
- `category`
- `is_active`
- `created_by_admin_id` (fk -> users.id)
- `created_at`, `updated_at`

### `trending_items`
- `id` (pk)
- `title`
- `template_prompt_id` (nullable)
- `prompt_override` (nullable)
- `settings_override_json` (nullable)
- `order_index`
- `is_active`
- `starts_at`, `ends_at` (nullable)

### `admin_actions`
- `id` (pk)
- `admin_user_id` (fk -> users.id)
- `action` (string)
- `target_type`, `target_id`
- `details_json`
- `created_at`

## 3) Muhim index/constraintlar

- `users.telegram_user_id` unique
- `payments.telegram_charge_id` unique
- `payments.payload` unique (invoice payload idempotency)
- `ledger_transactions.idempotency_key` unique
- `generation_jobs.status` index (worker fetch)

## 4) Balans hisoblash qoidasi

`balances.token_balance` — kesh/denormalization bo‘lishi mumkin.
Source of truth: `ledger_transactions` yig‘indisi. Har ledger yozilganda balans update qilinadi.

