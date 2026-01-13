# Telegram Bot UI / Navigation Spec

Maqsad: inline buttonlar bilan “app-like” navigatsiya, chatni iflos qilmaslik.

## 1) Global prinsiplar

- Har bir “screen” bitta message sifatida yuritiladi (edit message + inline keyboard).
- Uzoq jarayonlar (generation) uchun status message: “Queued / Running / Done”.
- Har action `callback_data` orqali state’ga boradi, kerak bo‘lsa `FSM` ishlatiladi.
- “Back” doim ishlasin; “Home” tez qaytarsin.

## 2) Asosiy menyu (Home)

Inline tugmalar (misol):
- Generate
- Templates
- Trending
- Profile
- Balance / Top up
- Help

Admin bo‘lsa qo‘shimcha:
- Admin Panel

## 3) Generate flow screens

### 3.1 Model select
- Nano Banana
- Nano Banana Pro
- SeeDream 4
- GPT Image
- Back

### 3.2 Prompt input
Bot userdan prompt so‘raydi:
- “Prompt kiriting” (text)
Inline:
- Add reference images
- Advanced settings
- Use template
- Generate
- Back

### 3.3 Reference images
User 1..N ta rasm yuboradi (album yoki ketma-ket).
Inline:
- Done
- Clear
- Back

### 3.4 Advanced settings
Inline toggles/select:
- Aspect ratio / size
- Style preset
- Seed (random / custom)
- Steps/quality
- Guidance/CFG
- Safety level
- Outputs count
- Reference strength / weights
- Back / Save

### 3.5 Confirmation
Ko‘rsatish:
- model, prompt, ref count, cost
Inline:
- Generate
- Edit prompt
- Settings
- Back

## 4) Profile / Balance

Profile:
- username/id
- referral link
- language
- history shortcut

Balance:
- token balance
- last transactions
- top up

## 5) Templates / Trending

Templates: kategoriyalar → template list → preview → “Use”.
Trending: admin belgilagan “quick picks” → “Use”.

## 6) Callback data (konvensiya)

`cb:<scope>:<action>:<id?>`

Misol:
- `cb:home:open`
- `cb:gen:model:nano_banana`
- `cb:tpl:use:123`

## 7) Rate limiting UX

Agar user tez-tez bosib yuborsa:
- qisqa “Please wait…” toast (answerCallbackQuery)
- yoki “Cooldown: 10s”

