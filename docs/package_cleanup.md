# GitHub Package Cleanup Guide

Bu hujjat GitHub Container Registry (ghcr.io) dagi eski va keraksiz package versiyalarni tozalash bo'yicha yo'l-yo'riq beradi.

## Masala

CI/CD workflow har bir commit va release uchun bir nechta Docker image tag yaratadi:
- `main` - eng oxirgi main branch
- `0.1.2` - aniq semantic version
- `0.1` - minor version (har yangi 0.1.x release bilan yangilanadi)
- `sha-<commit>` - har bir commit uchun alohida tag

Vaqt o'tishi bilan `sha-` tagli eski versiyalar to'planib qoladi va storage ishlatadi.

## Qaysi versiyalarni saqlash kerak

**Saqlash:**
- ✅ Semantic version taglar: `0.1.0`, `0.1.1`, `0.1.2`, `0.1`, `0.2` va h.k.
- ✅ `main` va `latest` taglar
- ✅ Eng oxirgi 5 ta `sha-` tagli version (rollback uchun)

**O'chirish:**
- ❌ 5 tadan eskiroq `sha-` tagli versiyalar

## Tozalash usullari

### 1-usul: GitHub Web Interface (Manual)

1. GitHub'da repo packagelariga o'ting:
   ```
   https://github.com/blogchik/bananapicsbot/packages
   ```

2. Package'ni tanlang (`bananapicsbot/api` yoki `bananapicsbot/bot`)

3. Package versiyalarni ko'ring va keraklilarini tanlang:
   - Har bir versiyaga o'ting
   - "Package settings" → "Delete this version"

**Afzalliklari:**
- Token/permission kerak emas
- Vizual interface
- Xavfsiz (har bir versiyani ko'rib tasdiqlash mumkin)

**Kamchiliklari:**
- Ko'p versiyalar uchun sekin
- Manual jarayon

### 2-usul: Automated Script

Repository'da tayyorlangan script mavjud: [scripts/cleanup_old_packages.sh](../scripts/cleanup_old_packages.sh)

#### Prerequisites

1. GitHub CLI o'rnatilgan bo'lishi kerak:
   ```bash
   gh --version
   ```

2. GitHub CLI autentifikatsiya qilish va package permissions qo'shish:
   ```bash
   gh auth login
   gh auth refresh -h github.com -s delete:packages,write:packages,read:packages
   ```

#### Ishlatish

```bash
# Scriptni ishga tushirish
./scripts/cleanup_old_packages.sh
```

Script quyidagilarni qiladi:
1. Har ikkala package (`api` va `bot`) uchun barcha versiyalarni oladi
2. Semantic version va main taglarni saqlab qoladi
3. Eng oxirgi 5 ta `sha-` versiyani saqlab qoladi
4. Qolgan eski `sha-` versiyalarni o'chiradi

#### Script konfiguratsiyasi

`scripts/cleanup_old_packages.sh` faylida sozlamalarni o'zgartirish mumkin:

```bash
# Nechta SHA versiya saqlash kerak
KEEP_SHA_VERSIONS=5

# Package nomlari
PACKAGES=("bananapicsbot-api" "bananapicsbot-bot")

# Owner
OWNER="blogchik"
```

### 3-usul: GitHub Actions Workflow (Automated)

Kelajakda avtomatik tozalash uchun workflow qo'shish mumkin:

```yaml
# .github/workflows/cleanup-packages.yml
name: Cleanup Old Packages

on:
  schedule:
    # Har hafta yakshanba kuni soat 2:00 da
    - cron: '0 2 * * 0'
  workflow_dispatch: # Manual trigger

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Delete old package versions
        uses: actions/delete-package-versions@v4
        with:
          package-name: 'bananapicsbot/api'
          package-type: 'container'
          min-versions-to-keep: 10
          delete-only-untagged-versions: 'false'
          token: ${{ secrets.GITHUB_TOKEN }}
```

## Package Storage Optimization

### Hozirgi holat

CI/CD workflow har bir push uchun 2 ta service × 4 ta tag = **8 ta image** yaratadi.

Masalan, 50 ta commit bo'lsa:
- Semantic versions: ~6 ta (0.1.0, 0.1.1, 0.1.2, 0.1, 0.2, va h.k.)
- main tag: 1 ta (eng oxirgi)
- SHA tags: 50 ta

**Jami**: 57 ta image version × 2 service = **114 ta image**

### Optimizatsiya qilgandan keyin

- Semantic versions: 6 ta (saqlaymiz)
- main tag: 1 ta (saqlaymiz)
- SHA tags: 5 ta (eng oxirgilari)

**Jami**: 12 ta image version × 2 service = **24 ta image**

**Tejamkorlik**: ~79% storage kamayadi

## Xavfsizlik

Package o'chirish qaytarilmaydigan operatsiya. Lekin:

✅ Semantic version taglar (**0.1.2**) saqlanadi - istalgan releasega rollback mumkin
✅ Eng oxirgi 5 ta SHA tag saqlanadi - yaqinda commitlarga rollback mumkin
✅ `main` tag doim mavjud - eng oxirgi production versiyaga access bor

## Troubleshooting

### Permission Error

```
Error: You need at least read:packages scope
```

**Yechim:**
```bash
gh auth refresh -h github.com -s delete:packages,write:packages,read:packages
```

### Package Not Found

```
Error: Unable to fetch package versions
```

**Yechim:**
1. Package nomi to'g'riligini tekshiring
2. Package visibility (public/private) ni tekshiring
3. Token'da package access borligini tekshiring

### Script Execution Error

```
bash: ./scripts/cleanup_old_packages.sh: Permission denied
```

**Yechim:**
```bash
chmod +x scripts/cleanup_old_packages.sh
```

## Best Practices

1. **Muntazam tozalash**: Har 2-3 oyda yoki 50+ commit dan keyin
2. **Backup**: Muhim versiyalarni semantic tag bilan mark qilish
3. **Monitoring**: Package storage o'lchamini kuzatish
4. **Testing**: Birinchi marta scriptni dry-run rejimida ishlatish (qo'shimcha flag qo'shish mumkin)

## Qo'shimcha Ma'lumot

- [GitHub Packages Documentation](https://docs.github.com/en/packages)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Tag Best Practices](https://docs.docker.com/develop/dev-best-practices/)
