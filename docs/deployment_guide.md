# Deployni Sozlash Bo'yicha Qo'llanma

Loyihani serverga avtomatik deploy qilish uchun quyidagi qadamlarni bajaring.

## 1. GitHub Secrets Sozlamalari

GitHub repozitoriysiga kiring: **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
Quyidagi 4 ta maxfiy o'zgaruvchini yarating:

| Secret Nomi         | Qiymati (Nimani yozish kerak)                                                                                                                                                                   |
| :------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`SSH_HOST`**      | Serveringizning IP manzili (masalan: `123.45.67.89`).                                                                                                                                           |
| **`SSH_USERNAME`**  | Serverga kirish uchun foydalanuvchi nomi (masalan: `root` yoki `ubuntu`).                                                                                                                       |
| **`SSH_KEY`**       | Serverga kirish uchun ishlatiladigan **Private Key** (SSH kalitining mazmuni).<br>Bu odatda `-----BEGIN OPENSSH PRIVATE KEY-----` bilan boshlanadi.<br>_Muhim: Kalitni to'liq ko'chirib oling._ |
| **`PROD_ENV_FILE`** | Serverda ishlatiladigan `.env` faylning **to'liq ichidagi ma'lumotlari**.<br>Database URL, Tokenlar, Redis URL va boshqa barcha sozlamalar shu yerda bo'lishi kerak.                            |

---

## 2. Serverni Tayyorlash

Serveringizga SSH orqali kiring va loyiha uchun papka yarating (agar yo'q bo'lsa):

```bash
# Serverga kirish
ssh username@ip_address

# Papka yaratish (CI faylida shu papka ko'rsatilgan: ~/bananapicsbot)
mkdir -p ~/bananapicsbot
```

_Eslatma: Agar papka nomini o'zgartirsangiz, `.github/workflows/ci.yml` faylidagi `deploy` qismida ham yo'lni o'zgartirish kerak bo'ladi._

---

## 3. Deployni Boshlash

Barcha sozlamalar tayyor bo'lgach, o'zgarishlarni GitHub ga yuboring:

```bash
git add .
git commit -m "feat: Add CI/CD deployment workflow"
git push origin main
```

**Nima sodir bo'ladi?**

1.  GitHub Actions da **CI/CD** workflow ishga tushadi.
2.  **Test**: Kod testdan o'tkaziladi.
3.  **Build**: Docker imajlar yasaladi va GitHub Container Registry (GHCR) ga yuklanadi.
4.  **Deploy**:
    - GitHub Actions serverga ulanadi.
    - `PROD_ENV_FILE` dan `.env` faylni yaratadi.
    - Yangi `docker-compose.yml` ni yuklaydi.
    - Eski konteynerlarni o'chirib, yangilarini (`docker compose up -d`) ishga tushiradi.

---

## Muammolar yuzaga kelsa (Troubleshooting)

- **SSH Permission Denied**: `SSH_KEY` noto'g'ri kiritilgan yoki serverda `~/.ssh/authorized_keys` ga Public Key qo'shilmagan bo'lishi mumkin.
- **Docker Login Failed**: GitHub Actions avtomatik ravishda `GITHUB_TOKEN` dan foydalanadi, lekin serverda `docker` o'rnatilmagan bo'lsa xato beradi.
- **Database Ulanish Xatosi**: `PROD_ENV_FILE` ichida `DATABASE_URL` to'g'ri ko'rsatilganligini tekshiring. Docker ichida `localhost` o'rniga `db` (servis nomi) ishlatilishi kerak.

Muvaffaqiyatli deploy tilayman! 🚀
