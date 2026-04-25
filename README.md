# 🐈 Girgitton v2

Telegram media upload bot + Desktop App.

Kompyuteringizdagi rasm va videolarni guruhga avtomatik ravishda 5 tadan qism qilib yuboradi.

---

## Ish tartibi

Har 5 talik qism uchun:

1. **Media album** — 5 ta fayl preview (rasm/video) ko'rinishida
2. **Document album** — xuddi o'sha 5 ta fayl fayl (document) ko'rinishida

---

## Arxitektura

```
Railway (24/7)          Desktop App (siz)
┌──────────────────┐    ┌──────────────────────┐
│ Telegram Bot     │    │ CustomTkinter GUI     │
│ aiohttp Mini API │◄──►│ asyncio upload engine│
│ Redis storage    │    │ GlobalWorkerPool      │
└──────────────────┘    └──────────────────────┘
```

---

## Railway Deploy

### 1. Muhit o'zgaruvchilari

Railway Dashboard → Variables:

```
API_ID=
API_HASH=
BOT_TOKEN=
OWNER_ID=
API_SECRET=    # istalgan uzun tasodifiy satr
```

Redis — Railway Dashboard → New Service → Database → Redis (REDIS_URL avtomatik qo'shiladi)

### 2. Deploy

```bash
git push origin main
```

Railway avtomatik build va deploy qiladi. Health check: `GET /health`

---

## Desktop App

### Yuklab olish

Bot ga `/download` yuboring → platformangiz uchun havola

### Birinchi ishga tushirish

1. `/setup` → config.json faylini yuklab oling
2. Girgitton.exe → "Config import" → faylni tanlang
3. Ismingizni kiriting → Boshlash

### Qurilish (Developer)

```bash
pip install -r requirements-app.txt pyinstaller
pyinstaller build/girgitton.spec
```

---

## Lokal test (bot)

```bash
pip install -r requirements.txt
cp .env.example .env
# .env ni to'ldiring
python main.py
```

---

## Bot buyruqlari

| Buyruq | Vazifasi |
|--------|----------|
| `/start` | Yordam |
| `/download` | Desktop App yuklab olish |
| `/setup` | Config fayl + token (30 daqiqa) |
| `/status` | App holati |
| `/stop` | Yuklashtni to'xtatish |
| `/allow <ID>` | Foydalanuvchi qo'shish (faqat egasi) |
| `/disallow <ID>` | Ruxsatni olib tashlash |
| `/allowed` | Ro'yxat |

---

## Loyiha strukturasi

```
girgitton/
├── main.py              ← Railway bot + aiohttp API server
├── api.py               ← Mini API endpointlar (HMAC auth)
├── storage.py           ← Redis + JSON fallback
├── config.py            ← Sozlamalar
├── sender.py            ← Media yuborish logikasi
├── helpers.py           ← Fayl skanerlash, logging
├── requirements.txt     ← Server kutubxonalari
├── requirements-app.txt ← Desktop App kutubxonalari
├── railway.toml         ← Railway deploy konfiguratsiyasi
├── nixpacks.toml        ← Build konfiguratsiyasi
├── app/                 ← Desktop App
│   ├── __main__.py      ← Entry point (thread setup)
│   ├── gui.py           ← App class, frame switching
│   ├── login_frame.py   ← Config import oynasi
│   ├── main_frame.py    ← Asosiy ish oynasi
│   ├── throttle_dialog.py ← Throttle ogohlantiruv
│   ├── engine.py        ← Upload orkestratori
│   ├── worker_pool.py   ← GlobalWorkerPool (3-criterion rotation)
│   ├── api_client.py    ← Railway HTTPS client (HMAC)
│   └── app_config.py    ← Lokal config saqlash
├── build/
│   └── girgitton.spec   ← PyInstaller spec
└── .github/workflows/
    └── build-release.yml ← 3-platform CI/CD
```

---

## Qo'llab-quvvatlanadigan formatlar

| Tur | Kengaytmalar |
|-----|--------------|
| Rasmlar | `jpg, jpeg, png, webp, bmp` |
| Videolar | `mp4, mov, avi, mkv, webm, m4v` |
