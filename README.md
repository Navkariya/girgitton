# 🐈 Girgitton v3.2

> **Telegram media auto-sender** — lokal papkadan rasm/video fayllarni guruhga **5 tadan album sifatida** (avval **media preview**, keyin **fayl/document**) navbatma-navbat yuboradi. **3 worker** parallel yuklash bilan tezlikni oshiradi, throttling sodir bo'lganda avtomatik tiklanadi.

[![Release](https://img.shields.io/github/v/release/Navkariya/girgitton)](https://github.com/Navkariya/girgitton/releases/latest)
[![CI](https://github.com/Navkariya/girgitton/actions/workflows/ci.yml/badge.svg)](https://github.com/Navkariya/girgitton/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

---

## 📥 Yuklab olish

| Platforma | Fayl                                                                                                                                                |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🪟 Windows | [Girgitton_Windows.exe](https://github.com/Navkariya/girgitton/releases/latest/download/Girgitton_Windows.exe)                                       |
| 🍎 macOS   | [Girgitton_macOS.zip](https://github.com/Navkariya/girgitton/releases/latest/download/Girgitton_macOS.zip)                                           |
| 🐧 Linux   | [Girgitton_Linux.bin](https://github.com/Navkariya/girgitton/releases/latest/download/Girgitton_Linux.bin)                                           |

Bot ichida `@girgitton_media_bot` ga `/download` yuborsangiz ham shu havolalar keladi.

---

## ✨ Asosiy xususiyatlar

- **Single-upload, dual-send** — har 5 fayl 1 marta yuklanadi va ikki marta yuboriladi (media + document) → trafik 2× tejaladi
- **3 worker pool** — parallel yuklash, sessiya rotatsiyasi, FloodWait avto-retry
- **Multi-tenant** — bir guruhda bir nechta foydalanuvchi (har biri o'z App'i bilan), bir-biriga halaqit bermaydi
- **Avtomatik ulanish** — App ochilishi bilanoq Telegram orqali START tugmasi bosilib ulanadi (pair kod kerak emas)
- **Resume** — internet uzilsa yoki crash bo'lsa, **kelgan joyidan davom ettirish** (`/resume` yoki "Davom ettirish" tugmasi)
- **Per-batch checkpoint** — har 5-batch tugagach atomic save
- **Encrypted local credentials** — Fernet + OS keyring (DPAPI/Keychain)
- **HMAC-SHA256** + replay protection (timestamp ±60s)
- **Drag-and-drop papka tanlash**, dark-mode UI

---

## 🚀 Tezkor start (foydalanuvchi)

1. Yuqoridan **App ni yuklab oling** (yoki `/download` botga yuboring)
2. Ishga tushiring → Telegramda START tugmasini bosing → App avtomatik ulanadi
3. Botni kerakli guruhga qo'shing va **admin** qiling
4. Guruhda `/here` yuboring → guruh App'ingizdagi ro'yxatga qo'shiladi
5. App'da har guruh uchun **papka tanlang** (yoki drag-drop)
6. **▶️ Boshlash** — yuborish boshlanadi
7. Internet uzilsa — **⏯ Davom ettirish** tugmasini bosing yoki botga `/resume` yuboring

---

## 🤖 Bot komandalari

| Komanda        | Joy        | Vazifa                                                  |
| -------------- | ---------- | ------------------------------------------------------- |
| `/start`       | DM         | Yordam matni                                            |
| `/download`    | DM         | App yuklab olish linklari                               |
| `/here`        | Guruhda    | Guruhni sizning App ro'yxatingizga qo'shish             |
| `/unhere`      | Guruhda    | Olib tashlash                                           |
| `/groups`      | DM         | Sizning faol guruhlar ro'yxati                          |
| `/status`      | DM         | Yuklash holati (% + tezlik)                             |
| `/stop`        | DM         | Yuklashni to'xtatish (progress saqlanadi)               |
| `/resume`      | DM         | Saqlangan joydan davom ettirish                         |
| `/allow <id>`  | DM (owner) | Foydalanuvchini ACL ga qo'shish                         |
| `/disallow`    | DM (owner) | Olib tashlash                                           |
| `/allowed`     | DM (owner) | ACL ro'yxat                                             |

---

## 🏗 Arxitektura

```
girgitton/
├── src/girgitton/
│   ├── core/        # Domen-pure (config, models, errors)
│   ├── shared/      # Crypto (HMAC+Fernet), media skaner, repositories
│   ├── storage/     # Repository Protocol + Redis/JSON adapter
│   ├── bot/         # Telethon handlerlar + aiohttp HTTP API
│   └── app/         # CustomTkinter GUI + 3-worker upload engine
├── tests/           # 118 test, coverage ≥80%
├── deploy/          # Railway + Docker + nixpacks
├── scripts/         # PyInstaller build
└── .github/         # CI + release workflows (Win/Mac/Linux)
```

To'liq diagrammalar uchun: [docs/architecture.md](docs/architecture.md).

---

## 🔐 Xavfsizlik

- **HMAC-SHA256** har request da (timing-safe `compare_digest`)
- **Connect token TTL 5 min** + one-time consume
- **Fernet at-rest** — `~/.girgitton/credentials.enc` shifrlangan
- **Per-IP/per-user rate limit**
- **SecretStr** + log filter — tokenlar log oqimiga chiqmaydi

To'liq tahdid modeli: [docs/security.md](docs/security.md).

---

## 🛠 Manba kodidan ishga tushirish

```bash
git clone https://github.com/Navkariya/girgitton.git
cd girgitton

# Virtual environment
python -m venv .venv
source .venv/Scripts/activate    # Win: .venv\Scripts\activate

pip install -e ".[app,dev]"

# Sirlar
cp .env.example .env
# API_ID, API_HASH, BOT_TOKEN, OWNER_ID, API_SECRET ni to'ldiring

# Bot (terminal 1)
python -m girgitton.bot

# Desktop App (terminal 2)
python -m girgitton.app
```

---

## 🧪 Verify

```bash
ruff check src/ tests/
mypy src/girgitton
pytest -q                  # 118 test, ≥80% coverage
bandit -r src/ -ll
```

---

## 🚢 Deploy

### Bot — Railway

1. https://railway.app → New Project → Deploy from GitHub Repo → `Navkariya/girgitton`
2. Variables: `API_ID`, `API_HASH`, `BOT_TOKEN`, `BOT_USERNAME`, `OWNER_ID`, `API_SECRET`
3. (Tavsiya) Add Plugin → Database → Redis (auto-injected `REDIS_URL`)
4. `git push origin main` → auto-deploy via Nixpacks

To'liq qo'llanma: [docs/railway-deploy.md](docs/railway-deploy.md)

```bash
curl https://<your>.railway.app/health
# {"ok": true, "service": "girgitton", "version": "3.2.0"}
```

**Desktop App (PyInstaller):**
```bash
pip install -e ".[app,build]"
pyinstaller scripts/package.spec --clean --noconfirm
# dist/Girgitton.{exe,app,bin}
```

**Cross-platform release** (avtomatik 3 platform):
```bash
git tag v3.2.0 && git push origin v3.2.0
# GitHub Actions: Win/Mac/Linux build + GitHub Release
```

To'liq onboarding: [docs/onboarding.md](docs/onboarding.md). Operatsion runbook: [docs/runbook.md](docs/runbook.md).

---

## 📋 Versiya tarixi

- **v3.2** — Resume support (per-batch checkpoint, /resume buyrug'i, "Davom ettirish" tugmasi), `girgitton_icon.jpg`
- **v3.1** — Multi-tenant (per-owner state, /pair olib tashlandi, token-based auto-connect, /here buyrug'i, ChatAction listener)
- **v3.0** — Yangi struktura (`src/girgitton/`, claude_all.jpg layout), per-owner storage Protocol, Fernet, HMAC-SHA256

---

## 📄 Litsenziya

MIT — [LICENSE](LICENSE)
