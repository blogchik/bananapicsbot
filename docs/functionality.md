# Bot funksionallari

## Hozirgi holat

- Faqat `/start` komandasi uchun welcome message yuboradi.
- Handlerlar alohida modulga ajratilgan (`bot/handlers`), kengaytirish oson.
- FastAPI asosidagi `api` servis mavjud.
- API `GET /` root info endpointiga ega.
- API `GET /api/v1/health` va `GET /api/v1/info` endpointlari mavjud.
- Versiyalash `/api/v1` orqali amalga oshiriladi.
- CORS, rate limit, global error handling qo'shilgan.
- Postgres servis va Alembic skeleti qo'shilgan.

## Reja

- Qo'shimcha komandalar va media ishlovlari keyingi bosqichlarda qo'shiladi.
