# Env sozlamalari

- `BOT_TOKEN`: Telegram bot tokeni. `.env` ichida saqlanadi.

## Namuna

```
BOT_TOKEN=123456:ABCDEF
```

## Tayyorlash

1. `.env.example` faylini `.env` ga ko'chiring.
2. `BOT_TOKEN` ni real token bilan to'ldiring.

## Eslatma

- Tokenni ommaga oshkor qilmang.
- Token yangilansa, `docker compose up -d --build` bilan qayta ishga tushiring.
