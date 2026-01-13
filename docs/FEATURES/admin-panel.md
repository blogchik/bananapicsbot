# Feature: Admin panel (full control)

## MVP: bot ichida admin menyu

Admin panel bo‘limlari:

### Users
- search by telegram id/username
- ban/unban
- adjust balance (ledger orqali)
- view user history (jobs, transactions)

### Pricing / Packages
- model pricing (token cost, multipliers)
- Stars paketlari (stars → tokens)
- free trial (optional)

### Models / Providers
- model enable/disable
- provider keys status (only “set/not set”, key’ni ko‘rsatmaslik)
- rate limits per model

### Templates / Trending
- CRUD templates
- set trending list/order/time window

### Referrals
- percent
- apply_to policy
- thresholds

### Transactions
- search, audit
- manual refund/compensation

## Permissions

Minimal:
- `admin`: full
- `support`: users + view-only transactions (keyinroq)

## Audit

Har admin action `admin_actions` jadvaliga yoziladi.

