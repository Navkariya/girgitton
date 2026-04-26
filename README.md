# 🐈 Girgitton v2.1

Telegram media upload bot + Desktop App.

Kompyuteringizdagi rasm va videolarni guruhlarga avtomatik ravishda 5 tadan qism qilib yuboradi. Yangilangan **v2.1** versiyasida ulanish butunlay xavfsiz (fayllarsiz) va ko'p-guruhli (multi-group) parallel yuklash qobiliyatiga ega!

---

## Ish tartibi

Har 5 talik qism uchun:

1. **Media album** — 5 ta fayl preview (rasm/video) ko'rinishida
2. **Document album** — xuddi o'sha 5 ta fayl fayl (document) ko'rinishida

---

## Yangiliklar (v2.1)

- **Xavfsiz Pairing:** Endi `config.json` faylini yuklab olish va o'tkazish yo'q. Guruhda `/pair` buyrug'ini berasiz va to'g'ridan-to'g'ri appga ulanasiz (yoki 6 xonali kod orqali).
- **Deep Link:** `girgitton://` protokoli orqali bitta bosishda Desktop App avtomatik ochilib, serverga ulanadi.
- **Multi-group Upload:** Bir vaqtning o'zida bir nechta guruhlarga fayl yuklash mumkin (round-robin GlobalWorkerPool yordamida).
- **Local Auto-pair:** Agar bot va app bitta kompyuterda ishlayotgan bo'lsa, hech qanday kodsiz to'g'ridan to'g'ri ulanadi.

---

## Arxitektura

```
Railway (24/7)             Desktop App (siz)
┌─────────────────────┐    ┌──────────────────────┐
│ Telegram Bot        │    │ CustomTkinter GUI    │
│ aiohttp Mini API    │◄──►│ asyncio upload engine│
│ Redis storage       │    │ GlobalWorkerPool     │
└─────────────────────┘    └──────────────────────┘
```

---

## Deploy va O'rnatish

### 1. Muhit o'zgaruvchilari (Server)

Railway Dashboard yoki lokal `.env` da kerak:

```env
API_ID=...
API_HASH=...
BOT_TOKEN=...
OWNER_ID=...
API_SECRET=your_random_secret   # App xavfsizligi uchun maxfiy so'z
ALLOWED_USERS=111,222           # Ixtiyoriy, qo'shimcha adminlar
```

Redis — Railway Dashboard → New Service → Database → Redis (`REDIS_URL` avtomatik qo'shiladi).

### 2. Desktop App

Bot ga `/download` yuboring va platformangiz uchun dasturni yuklab oling.

### 3. Ulanish

1. Telegramda o'z guruhingizga botni qo'shing.
2. Guruhda `/pair` buyrug'ini bering.
3. Bot sizga 6-xonali kod va **Deep link** beradi.
4. Deep link ni bosing (App avtomatik ulanadi) yoki Appni ochib 6-xonali kodni kiriting.
5. Har bir guruh uchun papka tanlang va "Boshlash" ni bosing.

---

## Bot buyruqlari

| Buyruq | Vazifasi |
|--------|----------|
| `/start` | Yordam |
| `/download` | Desktop App yuklab olish |
| `/pair` | Guruhni faollashtirish va ulanish kodi olish (Guruhda) |
| `/unpair` | Guruhni faol ro'yxatdan o'chirish (Guruhda) |
| `/groups` | Barcha faol guruhlarni ko'rish |
| `/status` | App holati (progress bar) |
| `/stop` | Yuklashni to'xtatish (App ga signal) |
| `/allow <ID>` | Foydalanuvchi qo'shish (faqat egasi) |
| `/disallow <ID>` | Ruxsatni olib tashlash |

---

## Loyiha strukturasi

```
girgitton/
├── main.py              ← Railway bot + API server
├── api.py               ← Mini API endpointlar (/pair, /groups)
├── storage.py           ← Redis + JSON fallback (pair kodlar uchun)
├── config.py            ← Sozlamalar
├── app/                 ← Desktop App (GUI)
│   ├── __main__.py      ← Entry point (deep link handler)
│   ├── gui.py           ← App class
│   ├── login_frame.py   ← Pair code oyna
│   ├── main_frame.py    ← Multi-group papka tanlash
│   ├── engine.py        ← Orchestrator
│   ├── worker_pool.py   ← Session rotation pool
│   └── api_client.py    ← HTTP Client
├── build/
│   └── girgitton.spec   ← PyInstaller config (girgitton:// URL protocol)
└── .github/workflows/   ← CI/CD Actions
```

---

## Qo'llab-quvvatlanadigan formatlar

| Tur | Kengaytmalar |
|-----|--------------|
| Rasmlar | `jpg, jpeg, png, webp, bmp` |
| Videolar | `mp4, mov, avi, mkv, webm, m4v` |
