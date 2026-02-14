# Wavespeed Admin Dashboard - Implementation Plan

## Overview
Admin panelga yangi "Wavespeed" sahifasi qo'shiladi. Bu sahifada:
- Wavespeed API balansini real-time ko'rish
- So'nggi generatsiyalar va ularning statuslari
- Model bo'yicha analitika (success rate, cost, usage)
- Queue holati (pending/running generations)
- Provider health status

## Architecture Flow
```
Bot Handler → AdminService → ApiClient → FastAPI Endpoint → WavespeedClient + DB
```

## Implementation Steps

### 1. API Backend - New Wavespeed Endpoint
**File: `api/app/api/v1/endpoints/admin.py`**
- `GET /admin/wavespeed/status` endpoint qo'shish:
  - `WavespeedClient.get_balance()` orqali real balansni olish
  - DB dan so'nggi generatsiyalar statistikasini olish (last 24h, 7d)
  - Generation queue statusini olish (pending/running count)
  - Model bo'yicha breakdown (har bir model uchun count, success rate, avg cost)
  - Response format:
    ```json
    {
      "balance": {"amount": 125.50, "currency": "USD"},
      "provider_status": "online|offline|degraded",
      "generations_24h": {"total": 150, "completed": 140, "failed": 10, "success_rate": 93.3},
      "generations_7d": {"total": 950, "completed": 900, "failed": 50, "success_rate": 94.7},
      "queue": {"pending": 3, "running": 2},
      "cost_24h": 2.50,
      "cost_7d": 15.80,
      "models": [
        {"name": "seedream-v4", "count_24h": 50, "count_7d": 300, "success_rate": 95.0, "avg_cost": 0.02},
        ...
      ],
      "recent_generations": [
        {"id": "...", "model": "seedream-v4", "status": "completed", "created_at": "...", "cost": 0.02},
        ...
      ]
    }
    ```

### 2. API Service - Admin Service Extension
**File: `api/app/services/admin_service.py`**
- `get_wavespeed_status()` method qo'shish:
  - WavespeedClient dependency inject qilish
  - Balance + generation stats + queue status ni bir joyga to'plash

### 3. Bot API Client - New Method
**File: `bot/infrastructure/api_client.py`**
- `get_wavespeed_status()` method qo'shish → `GET /api/v1/admin/wavespeed/status`

### 4. Bot Service - AdminService Extension
**File: `bot/services/admin.py`**
- `get_wavespeed_status()` static method qo'shish

### 5. Bot Callbacks - New Constants
**File: `bot/keyboards/builders.py`**
- `AdminCallback` klassiga qo'shish:
  - `WAVESPEED = "admin:wavespeed"`
  - `WAVESPEED_REFRESH = "admin:wavespeed:refresh"`
  - `WAVESPEED_RECENT = "admin:wavespeed:recent"`

### 6. Bot Keyboards - Admin Menu Update + New Keyboards
**File: `bot/keyboards/inline/admin.py`**
- `AdminKeyboard.main()` ga "Wavespeed" tugmasini qo'shish
- `AdminKeyboard.wavespeed_menu()` - Wavespeed submenu (Refresh, Recent Generations, Back)
- `AdminKeyboard.wavespeed_back()` - Back to wavespeed menu

### 7. Bot Handler - New Wavespeed Handler
**File: `bot/handlers/admin/wavespeed.py` (NEW)**
- `admin_wavespeed_menu()` - Asosiy Wavespeed sahifasi:
  - Balance ko'rsatish (USD)
  - Provider status (online/offline)
  - 24h va 7d statistika
  - Queue holati
  - Model breakdown
- `admin_wavespeed_refresh()` - Ma'lumotlarni yangilash
- `admin_wavespeed_recent()` - So'nggi 10 ta generatsiya batafsil ko'rsatish

### 8. Bot Router Registration
**File: `bot/handlers/admin/__init__.py`**
- `wavespeed_router` ni import qilish va `admin_router.include_router()` ga qo'shish

### 9. Translation Keys
**File: `bot/locales/base.py`**
- Yangi TranslationKey lar:
  - `ADMIN_WAVESPEED` - Menu button text
  - `ADMIN_WAVESPEED_TITLE` - Page title
  - `ADMIN_WAVESPEED_BALANCE` - Balance label
  - `ADMIN_WAVESPEED_STATUS` - Provider status
  - `ADMIN_WAVESPEED_STATS_24H` - 24h stats header
  - `ADMIN_WAVESPEED_STATS_7D` - 7d stats header
  - `ADMIN_WAVESPEED_QUEUE` - Queue status
  - `ADMIN_WAVESPEED_MODELS` - Models breakdown header
  - `ADMIN_WAVESPEED_RECENT` - Recent generations header
  - `ADMIN_WAVESPEED_REFRESH` - Refresh button
  - `ADMIN_WAVESPEED_ERROR` - Error message

### 10. Translations
**Files: `bot/locales/en.py`, `bot/locales/ru.py`, `bot/locales/uz.py`**
- Har bir tilga tegishli tarjimalarni qo'shish

## File Changes Summary
| File | Action | Description |
|------|--------|-------------|
| `api/app/api/v1/endpoints/admin.py` | EDIT | Add wavespeed status endpoint |
| `api/app/services/admin_service.py` | EDIT | Add wavespeed status method |
| `bot/infrastructure/api_client.py` | EDIT | Add get_wavespeed_status() |
| `bot/services/admin.py` | EDIT | Add get_wavespeed_status() |
| `bot/keyboards/builders.py` | EDIT | Add wavespeed callbacks |
| `bot/keyboards/inline/admin.py` | EDIT | Add wavespeed button & keyboards |
| `bot/handlers/admin/wavespeed.py` | NEW | Wavespeed handler |
| `bot/handlers/admin/__init__.py` | EDIT | Register wavespeed router |
| `bot/handlers/admin/panel.py` | EDIT | Add wavespeed menu callback |
| `bot/locales/base.py` | EDIT | Add translation keys |
| `bot/locales/en.py` | EDIT | Add English translations |
| `bot/locales/ru.py` | EDIT | Add Russian translations |
| `bot/locales/uz.py` | EDIT | Add Uzbek translations |
