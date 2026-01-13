# BananaPicsBot — Product Spec

## 1) Maqsad

Telegram bot orqali foydalanuvchi AI yordamida rasm generatsiya qiladi:
- matn promptdan (text-to-image)
- 1+ ta reference rasm bilan (image guidance / remix)
- turli modellar orasidan tanlab: Nano Banana, Nano Banana Pro, SeeDream 4, GPT Image

Bot ichida:
- profil va balans/tokenlar
- Telegram Stars orqali topup
- referal tizim (foizli cashback)
- admin panel (full control)
- advanced settings
- template prompts va trending
- inline buttonlar bilan qulay navigatsiya

## 2) Rollar

- **User**: rasm generatsiya, topup, tarix, sozlamalar.
- **Admin**: pricing, users, transactions, templates/trending, model availability, referral %, ban/unban, manual adjustments.
- (Ixtiyoriy) **Support/Moderator**: cheklangan admin huquqlari (keyinroq).

## 3) Asosiy user flow’lar

### 3.1 Rasm generatsiya
1) User `/start` → “Generate” tugmasi
2) Model tanlash (default: admin belgilaydi)
3) Prompt kiritish (yoki template tanlash)
4) Reference rasm(lar) qo‘shish (optional)
5) Advanced settings (optional)
6) “Generate” → token yechiladi → job queue → natija rasm(lar)

### 3.2 Topup (Telegram Stars)
1) User “Balance” → “Top up”
2) Paket tanlash (Stars miqdori)
3) Bot invoice yuboradi (Stars)
4) Telegram `pre_checkout_query` → tasdiq
5) `successful_payment` → ledgerga topup yoziladi → token balans oshadi

### 3.3 Referral
1) User referral link oladi (`?start=ref_<code>`)
2) Yangi user start qiladi → referrer biriktiriladi (faqat 1 marta)
3) Referred user topup qilsa → referrerga admin belgilagan % bo‘yicha token/bonus beriladi

### 3.4 Admin panel
Inline admin menyu:
- Users: search, ban/unban, role
- Pricing: token cost per model, paketlar
- Referrals: % va qoidalar
- Templates/Trending: CRUD
- Transactions: audit, refund, adjust
- System: provider keys status, feature toggles, rate limits

## 4) Biznes qoidalar (MVP)

- Har bir generation uchun token cost: **model + settings** ga bog‘liq.
- Token yechish “reservation” (hold) sifatida yoziladi; job muvaffaqiyatsiz bo‘lsa refund.
- Topup faqat Telegram Stars (hozircha).
- Referral reward: default “topupdan %”, admin sozlaydi (har topup/first topup).
- Har bir payment event idempotent bo‘lishi shart.

## 5) NFR (non-functional requirements)

- Tezkor UI: inline buttonlar, minimal chat spam.
- Asinxron generation: update handlerda bloklamaslik.
- Audit: transactions ledger va admin actions log.
- Xavfsizlik: tokenlar, admin access, PII minimal.
- Skalalanish: worker queue, object storage, caching.

