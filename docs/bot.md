# Telegram bot ishga tushirish

## Talablar

- Docker va Docker Compose o'rnatilgan bo'lishi kerak.

## Ishga tushirish

1. `.env.example` faylini `.env` ga ko'chiring.
2. `.env` faylida `BOT_TOKEN` ni to'ldiring.
3. Quyidagini ishga tushiring:

```
docker compose up -d --build
```

## To'xtatish

```
docker compose down
```

## Loglar

```
docker compose logs -f bot
```
