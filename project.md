# 🐈 Girgitton — Avtomatik Media Yuboruvchi (v3.1 multi-tenant)

> **v3.1 yangilanishi (2026-04-28):**
> - `/pair`/`/unpair` olib tashlandi — App ochilishi bilan **avtomatik ulanish** (token + Telegram START)
> - **Per-owner state** — har user o'zining guruh ro'yxatiga ega (multi-tenant izolyatsiya)
> - `/here` (guruhda) — joriy guruhni o'z ro'yxatingizga qo'shadi (bir guruh — bir nechta owner mumkin)
> - **ChatAction listener** — bot guruhdan o'chirilsa avtomatik tozalash
> - Connect oqimi: `App → POST /connect-init → t.me/<bot>?start=<token> → /start <token> → POST /connect-claim`
>
> v3.0 spetsifikatsiyasi quyida (asosiy arxitektura) — o'zgarish bo'lim 4.6 va 5.4 da ko'rsatilgan.



> Lokal papkadan rasm/video fayllarni Telegram guruhiga **5 tadan** album sifatida (avval **media preview**, keyin **fayl/document**) navbatma-navbat yuboruvchi tizim. **3 worker** parallel yuklash bilan tezlikni oshiradi, throttling sodir bo'lganda avtomatik tiklanadi.

---

## 1. Yuqori Daraja Maqsad

```
Lokal papka            Bot/API (Railway)              Telegram Guruh
┌────────────┐         ┌──────────────────┐          ┌──────────────┐
│ ~/Photos/  │ scan→   │ aiohttp + Telethon│  send→  │  @target_chat│
│ *.jpg/*.mp4│         │ HMAC, pair, ACL   │          │              │
└────┬───────┘         └────────▲─────────┘          └──────────────┘
     │ Desktop App              │ HTTPS+HMAC
     │ (CustomTkinter)          │
     └──────────────────────────┘
            3-worker pool
            5-batch sender (media+document)
```

**Ish jarayoni** (**bitta upload — ikki marta yuborish** strategiyasi):

1. App papkani skanerlaydi → tartiblangan media ro'yxat.
2. Ro'yxat **5 tadan** qismlarga bo'linadi.
3. Har **5 ta fayl uchun** ikki bosqichli yuborish:
   - **A bosqich:** Media album (preview) — `force_document=False`
   - **B bosqich:** Document album (fayl) — `force_document=True`
4. **Bitta yuklab olingan media** Telethon `InputDocument` orqali ikkala albomda ham qayta ishlatiladi → trafik 2x kamayadi.
5. **3 ta worker** parallel ravishda **turli batchlarni** yuklaydi (album tartibi qat'iy saqlanadi).
6. **Rate-limit aniqlash** (`FloodWaitError`, tezlik pasayishi, vaqt bo'yicha) → avtomatik **sessiya rotatsiyasi** + 30 daqiqa kutish.

---

## 2. Strukturasi (Claude Code Project Structure)

`claude_all.jpg` da ko'rsatilgan layoutni Telegram bot + Desktop app kontekstiga moslashtirilgan:

```
girgitton/
├── CLAUDE.md                         # AI agent yo'riqnomasi (ushbu loyiha uchun)
├── .claude/
│   ├── settings.json                 # Hooks, allowed tools, env
│   ├── settings.local.json           # Foydalanuvchi override (gitignore)
│   ├── commands/                     # Loyihaga xos slash-komandalar
│   │   ├── deploy.md                 # /deploy → Railway push + smoke
│   │   ├── build-app.md              # /build-app → PyInstaller .exe
│   │   └── verify.md                 # /verify → ruff+mypy+pytest
│   ├── agents/
│   │   ├── bot-handler-reviewer.md   # Bot hodisalarini tahlil qilish
│   │   ├── upload-engine-reviewer.md # Worker pool / rate-limit uchun
│   │   └── security-auditor.md       # HMAC, secret oqimi, ACL
│   └── skills/
│       └── batch-album-sender/       # Media+document album yuborish patterni
│           └── SKILL.md
├── docs/
│   ├── architecture.md               # Tizim arxitekturasi
│   ├── api-reference.md              # HTTP API
│   ├── security.md                   # Tahdid modeli, HMAC, secret menejmenti
│   ├── onboarding.md                 # Yangi foydalanuvchi
│   └── runbook.md                    # Operatsion runbook (deploy, rollback)
├── src/
│   └── girgitton/
│       ├── __init__.py
│       ├── core/                     # Domain (ramka-mustaqil)
│       │   ├── __init__.py
│       │   ├── config.py             # Settings (pydantic-uslub)
│       │   ├── models.py             # Frozen dataclasses (DTO)
│       │   ├── constants.py          # Kengaytmalar, BATCH_SIZE = 5
│       │   ├── logging_setup.py      # Structured JSON log
│       │   └── errors.py             # Domain xatoliklari
│       ├── shared/                   # Bot va App umumiy
│       │   ├── __init__.py
│       │   ├── crypto.py             # HMAC-SHA256 + Fernet
│       │   ├── media.py              # Skaner, hash, sanitize
│       │   └── repositories.py       # Repository protokoli
│       ├── storage/                  # Storage qatlami
│       │   ├── __init__.py
│       │   ├── base.py               # Repository protokoli
│       │   ├── redis_store.py        # Redis adapter
│       │   ├── json_store.py         # JSON fallback (atomic write)
│       │   └── factory.py            # Auto-select Redis/JSON
│       ├── bot/                      # Telegram Bot (Railway)
│       │   ├── __init__.py
│       │   ├── __main__.py           # Entry: python -m girgitton.bot
│       │   ├── client.py             # Telethon bot client init
│       │   ├── handlers/             # Komanda handlerlar
│       │   │   ├── __init__.py
│       │   │   ├── help.py           # /start, /help
│       │   │   ├── pairing.py        # /pair, /unpair, /groups
│       │   │   ├── status.py         # /status, /stop
│       │   │   ├── access.py         # /allow, /disallow, /allowed
│       │   │   └── decorators.py     # @owner_only, @allowed_only
│       │   ├── api/                  # HTTP API (aiohttp)
│       │   │   ├── __init__.py
│       │   │   ├── server.py         # AppRunner factory
│       │   │   ├── routes.py         # /health, /pair, /status, /task
│       │   │   ├── middleware.py     # HMAC, rate limit, error
│       │   │   └── schemas.py        # Request/Response DTOs
│       │   └── pairing.py            # Pair code generate/consume
│       ├── app/                      # Desktop App (lokal)
│       │   ├── __init__.py
│       │   ├── __main__.py           # Entry: python -m girgitton.app
│       │   ├── gui/                  # CustomTkinter UI
│       │   │   ├── __init__.py
│       │   │   ├── window.py         # App (root)
│       │   │   ├── login_frame.py    # Pair/auto-pair
│       │   │   ├── main_frame.py     # Papka tanlash, progress
│       │   │   └── throttle_dialog.py
│       │   ├── upload/               # Yuklash dvigateli
│       │   │   ├── __init__.py
│       │   │   ├── engine.py         # Orkestrator
│       │   │   ├── worker_pool.py    # 3 worker, queue
│       │   │   ├── batch.py          # 5-batch + media+document logic
│       │   │   ├── rate_limit.py     # FloodWait, tezlik trekeri
│       │   │   └── reuse_cache.py    # Telethon InputDocument re-use
│       │   ├── api_client.py         # Bot HTTP klient (HMAC)
│       │   ├── config_store.py       # Lokal credentials (Fernet)
│       │   └── deeplink.py           # girgitton:// protokol
│       └── platform/                 # OS xos kod
│           ├── __init__.py
│           ├── windows.py            # winreg deep link
│           ├── macos.py              # plist URL handler
│           └── secret_store.py       # Keyring/DPAPI/Keychain
├── tests/
│   ├── unit/
│   │   ├── test_crypto.py
│   │   ├── test_media.py
│   │   ├── test_batch.py
│   │   └── test_storage.py
│   ├── integration/
│   │   ├── test_api_routes.py
│   │   └── test_pairing_flow.py
│   └── e2e/
│       └── test_smoke.py
├── scripts/
│   ├── build_app.py                  # PyInstaller wrapper
│   ├── package.spec                  # PyInstaller spec
│   └── seed_demo.py                  # Demo guruh + foydalanuvchi
├── deploy/
│   ├── railway.toml                  # Railway config
│   ├── nixpacks.toml                 # Build provider
│   ├── Dockerfile                    # Konteyner (alternativ)
│   └── docker-compose.yml            # Lokal Redis bilan testlash
├── .github/
│   └── workflows/
│       ├── ci.yml                    # ruff + mypy + pytest + bandit
│       └── release.yml               # PyInstaller artifact
├── .env.example
├── .gitignore
├── pyproject.toml                    # PEP 621 — barcha bog'liqliklar
├── README.md
├── project.md                        # USHBU FAYL — Arxitektura
├── jarayon.txt                       # Bosqichma-bosqich TZ
└── bajarildi.txt                     # Bajarilgan bosqichlar
```

---

## 3. Texnologiyalar

### 3.1 Core stack

| Sloy             | Texnologiya                            | Sabab                                              |
| ---------------- | -------------------------------------- | -------------------------------------------------- |
| Til              | **Python 3.11+**                       | `match`, frozen dataclass, `asyncio.TaskGroup`     |
| Telegram         | **Telethon ≥ 1.34**                    | MTProto bilan ishlash, file re-use, FloodWait      |
| HTTP server      | **aiohttp ≥ 3.9**                      | Async, hafif, Telethon bilan bir loop              |
| HTTP klient      | **aiohttp.ClientSession**              | Same loop, keep-alive                              |
| Storage          | **redis-py ≥ 5** (asosiy) / JSON       | Railway add-on bor, lokal uchun fallback           |
| GUI              | **customtkinter 5** + **tkinterdnd2**  | Cross-platform, drag-drop, dark mode               |
| Crypto           | **cryptography (Fernet) + hmac/stdlib**| Local secret-at-rest + tarmoq autentifikatsiya     |
| Logging          | **logging + python-json-logger**       | Structured, Railway log oqimiga mos                |
| Test             | **pytest + pytest-asyncio**            | Async test, fixtures                               |
| Lint             | **ruff** (replaces flake8/isort/black) | Eng tezkor                                         |
| Type             | **mypy --strict**                      | Type sof                                           |
| Security         | **bandit + pip-audit**                 | Static + sup-chain                                 |
| Build            | **PyInstaller ≥ 6**                    | Bitta `.exe`/`.app`/`.bin`                         |
| Deploy           | **Railway (Nixpacks)** / Dockerfile    | Bot uchun                                          |

### 3.2 Configuration uslubi

`.env` muhit o'zgaruvchilari → `core.config.Settings` (frozen dataclass) — 12-factor.

```python
@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: SecretStr
    bot_token: SecretStr
    owner_id: int
    api_secret: SecretStr
    redis_url: str | None
    upload_workers: int = 3
    batch_size: int = 5
```

`SecretStr` — repr da `***` ko'rsatadi, log oqishidan himoya.

---

## 4. Funksionallik (To'liq)

### 4.1 Bot komandalari

| Komanda          | Ruxsat | Tavsif                                                |
| ---------------- | ------ | ----------------------------------------------------- |
| `/start`, `/help`| All    | Yordam matni                                          |
| `/download`      | All    | Desktop app yuklab olish havolalari                   |
| `/pair`          | Allow  | Guruhni faollashtirish + 6-xonali kod (TTL 5 daq)     |
| `/unpair`        | Allow  | Guruhni ro'yxatdan o'chirish                          |
| `/groups`        | Allow  | Faol guruhlar ro'yxati                                |
| `/status`        | Allow  | App progress (% + tezlik)                             |
| `/stop`          | Allow  | App ga stop signal yuborish                           |
| `/allow <ID>`    | Owner  | Foydalanuvchini ruxsatlar ro'yxatiga qo'shish         |
| `/disallow <ID>` | Owner  | Ruxsatni olib tashlash                                |
| `/allowed`       | Owner  | Ruxsatlilar ro'yxati                                  |

### 4.2 HTTP API

| Method | Path        | Auth         | Maqsad                                             |
| ------ | ----------- | ------------ | -------------------------------------------------- |
| GET    | /health     | —            | Railway health check                               |
| GET    | /auto-pair  | Localhost    | Lokal app uchun avtomatik credentials             |
| POST   | /pair       | Pair code    | Kod orqali credentials almashish                   |
| GET    | /groups     | HMAC         | Faol guruhlar ro'yxati                             |
| POST   | /status     | HMAC         | App progress yuboradi (har 5s)                    |
| GET    | /task       | HMAC         | App stop signalini tekshiradi                      |

### 4.3 Desktop App ekranlari

1. **Login** — auto-pair (lokal) yoki pair kod
2. **Main** — guruh-papka jadvali, Boshlash/To'xtatish, progress bar, log paneli
3. **Throttle Dialog** — Telegram throttle hodisasida countdown

### 4.4 Yuborish algoritmi (qat'iy tartib)

```python
# Pseudocode (5-batch, media+document, 3 worker)
files = scan_media(folder)        # tartiblangan
batches = chunked(files, 5)       # [[5], [5], [5], ...]

# 3 ta worker parallel bo'lib, lekin har bir batch ichida tartib qat'iy:
async def process_batch(batch, idx, total):
    # 1) Bitta yuklash — InputMedia listni hosil qiladi
    uploaded = await upload_files(batch)         # Telethon -> InputDocument list
    
    # 2) A bosqich: media album (preview)
    await client.send_file(chat, uploaded, force_document=False, caption=...)
    
    # 3) B bosqich: o'sha 5 ta InputDocument document album sifatida
    await client.send_file(chat, uploaded, force_document=True, caption=...)
```

> Telethon `send_file` `InputDocument` ro'yxatini qabul qiladi → faylni qayta yuklamaydi. Bu **trafikni 2x kamaytiradi**.

### 4.5 Rate-limit / Throttle handler

3 mezonli rotatsiya:
1. **Batch soni**: har 15 batchdan keyin sessiyani yangilash
2. **Vaqt**: 5 daqiqadan keyin sessiyani yangilash
3. **Tezlik**: 3 ta oxirgi batch o'rta tezligi 0.10 MB/s dan past bo'lsa

`FloodWaitError` aniqlansa: kutiladigan vaqt o'qiladi, GUI dialog ko'rsatiladi, taymer + auto-retry.

---

## 5. Xavfsizlik Modeli

### 5.1 Tahdid modeli

| Tahdid                            | Mitigation                                                  |
| --------------------------------- | ----------------------------------------------------------- |
| Bot tokenining oqishi             | `.env` faqat serverda; app fernet bilan saqlaydi            |
| API endpointlarga noma'lum kirish | Har request HMAC-SHA256 imzo + nonce                        |
| Pair code brute-force             | TTL 5 daq, 10 urinishdan keyin lock                         |
| Replay attack                     | Har imzoda `X-Timestamp`, ±60s skew                         |
| MITM (HTTPS yo'q)                 | Railway prod faqat `https://...`; lokal `127.0.0.1` only    |
| Ruxsatsiz `/pair`                 | Owner + ALLOWED_USERS ro'yxati                              |
| Lokal credentials.json o'g'rilish | Fernet key — OS keyring/DPAPI/Keychain ichida saqlanadi     |
| Log da maxfiy ma'lumot            | `SecretStr.__repr__` = "***", structured filter             |
| Resource exhaustion (DoS)         | Per-user rate limit 60 req/min API ga                       |

### 5.2 Secret oqimi

```
Railway Variables (.env)
       │
       ▼
Bot startup (Settings frozen)
       │
   ┌───┴───┐
   ▼       ▼
HMAC sign  Pair-code → temp Redis (TTL 5m)
   │            │
   │            ▼
   │       /pair endpoint → app
   │            │
   │            ▼
   │       App: cred + api_secret → Fernet → ~/.girgitton/credentials.enc
   │            │
   ▼            ▼
Har request: X-Signature: hmac(api_secret, body+timestamp)
```

### 5.3 Mandatory checks (har commitdan oldin)

- [ ] Hech qanday hardcoded secret (`bandit -r src/`)
- [ ] Barcha tashqi input validatsiyadan o'tadi (pydantic/dataclass)
- [ ] Rate-limit har endpointda yoqilgan
- [ ] Fernet kalit OS keyring da
- [ ] HMAC `compare_digest` (timing safe)
- [ ] Logda `bot_token`, `api_hash`, `api_secret` chiqmasligini test qilish

---

## 6. DevOps / Operations

### 6.1 Branching va versiya

- `main` — prod (Railway auto-deploy)
- `dev` — integratsiya
- `feature/*`, `fix/*`, `chore/*`
- Semantic versiya: `v3.0.0`, tag → release artifact

### 6.2 CI Pipeline (`.github/workflows/ci.yml`)

```yaml
1. checkout
2. setup-python 3.11
3. pip install -e .[dev]
4. ruff check + ruff format --check
5. mypy --strict src/
6. pytest --cov=src/girgitton (≥ 80%)
7. bandit -r src/ + pip-audit
8. artifact: coverage.xml
```

### 6.3 Release Pipeline (`.github/workflows/release.yml`)

```yaml
on: push tags v*
1. matrix [windows, macos, ubuntu]
2. PyInstaller .exe / .app / .bin
3. zip + sha256 checksum
4. gh release create
```

### 6.4 Observability

- **Bot:** structured JSON log → Railway oqimi
- **App:** `~/.girgitton/desktop_app.log` (rotation 10 MB)
- **Metrics:** `/health` JSON da `version`, `uptime`, `active_groups`, `connected_apps`

### 6.5 Disaster Recovery

| Buzilish              | Tiklash                                    |
| --------------------- | ------------------------------------------ |
| Redis o'chgan         | JSON fallback avtomatik                    |
| Bot crash             | Railway auto-restart + state Redis da      |
| App crash             | Progress saqlangan; qayta ochilsa davom    |
| Telegram throttle     | 30 daq taymer + sessiya rotatsiya          |
| Pair code yo'qotilgan | Yangi `/pair`, eski auto-expire            |

---

## 7. Quality Gates

| Gate              | Talab                              |
| ----------------- | ---------------------------------- |
| Type coverage     | mypy --strict, 100%                |
| Test coverage     | ≥ 80%                              |
| Lint              | ruff zero error                    |
| Security          | bandit zero high                   |
| Bundle size (app) | < 60 MB                            |
| Bot startup       | < 3s gacha                         |
| Memory (app idle) | < 200 MB                           |
| Worker latency    | batch tugash medianasi < 30s/batch |

---

## 8. Prinsiplar (loyihani boshqaruvchi qoidalar)

1. **KISS / DRY / YAGNI** — har yangi modulda asoslash kerak.
2. **Immutability** — `dataclass(frozen=True)` standart.
3. **Repository pattern** — storage adapterlari bir interfeys.
4. **Protocol-based DI** — Telethon, Redis va boshqalar Protocol orqali abstraktsiyada.
5. **Fail loud** — hech qachon `except: pass`. Har xato `logger.exception` + raise yoki user-facing dialog.
6. **No god-files** — ≤ 400 line/fayl, ≤ 50 line/funksiya.
7. **Async first** — barcha I/O `async`, bloklovchi qism `loop.run_in_executor`.
8. **Test like a user** — integration test pair flow ni `/pair → /pair endpoint → app save` to'liq qamrab oladi.

---

## 9. Roadmap (v3.0 → v3.x)

- **v3.0** — ushbu spetsifikatsiya (3 worker, batch reuse, Fernet)
- **v3.1** — Auto-resume (sessiya yo'qolsa progressdan davom etish)
- **v3.2** — Multi-folder per-group queue (har guruhga alohida papkalar)
- **v3.3** — Schedule (cron-uslub: ertaga 09:00 da boshlasin)
- **v3.4** — Web dashboard (admin uchun)
