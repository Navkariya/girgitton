# Girgitton v2 — To'liq Loyiha va DevOps Rejasi

> **Status**: Reja (v1 ishda, v2 rivojlantirilmoqda)
> **Hujjat yangilandi**: 2026-04-26
> **v1 hujjati**: [project.md](project.md)

---

## 0. Yakuniy Texnologiya Qarorlari

| Masala | Qaror | Sabab |
|--------|-------|-------|
| Upload session | **Bot token** | Ban xavfi yo'q, sodda, Telegram ToS to'g'ri |
| User session | ❌ | Shaxsiy akkaunt ban xavfi |
| Web App | ❌ | 2× bandwidth sarfi (user→server→Telegram) |
| Desktop App | ✅ | Standalone .exe, Python shart emas, 0 server bandwidth |
| GUI framework | **CustomTkinter** | Zamonaviy, dark mode, yengil (~2 MB), ttk'dan ko'ra chiroyli |
| asyncio+GUI | **Thread isolation** | tkinter main thread, asyncio background thread |
| Bot↔App aloqa | **aiohttp mini API** | `/stop` real-time, `/status` ishlaydi, yengil |
| Persistent storage | **Redis** (Railway) | Ephemeral FS → progress yo'qolmaydi |
| Storage fallback | **JSON fayl** | Lokal test, REDIS_URL yo'q bo'lganda |
| API autentifikatsiya | **HMAC-SHA256** | Har so'rovda signature, replay attack yo'q |
| Config uzatish | **One-time JSON token** | `/setup` → fayl → app import, 30 min TTL |
| Worker pool | **Global, MAX 5** | Per-chat = 30 session = suspicious → ban |
| Rotation | **Qism + vaqt + tezlik** | 3 mezon — hech qaysi yolg'iz to'liq emas |
| CI/CD | **GitHub Actions** | Har tag push'da 3 platform build avtomatik |
| Hosting | **Railway** | Arzon, git-based deploy, Redis addon built-in |
| Package | **PyInstaller onefile** | Bitta .exe, foydalanuvchi heч narsa o'rnatmaydi |

---

## 1. Umumiy Arxitektura

```
┌─────────────────────────────── GITHUB ───────────────────────────────┐
│                                                                       │
│  git push main  ──────────────────────→  Railway auto-deploy         │
│  git push v1.x.x (tag)  ─────────────→  GitHub Actions → 3 .exe     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
                              │                     │
                    Railway deploy         GitHub Releases
                              │                     │
┌─────────────────────────────▼──────────────────── │ ──────────────────┐
│                      RAILWAY (24/7)               │                   │
│                                                   │  foydalanuvchi    │
│  ┌─ Python process ──────────────────────────┐    │  yuklab oladi     │
│  │                                           │    │                   │
│  │  Telegram Bot (Telethon)                  │    │                   │
│  │  ├── /start, /download, /setup            │    │                   │
│  │  ├── /status, /stop                       │    │                   │
│  │  └── /allow, /disallow, /allowed          │    │                   │
│  │                                           │    │                   │
│  │  aiohttp Mini API  (port 8080)            │    │                   │
│  │  ├── GET  /health   ← Railway health check│    │                   │
│  │  ├── POST /connect  ← App birinchi ulanish│    │                   │
│  │  ├── POST /status   ← App progress        │    │                   │
│  │  ├── GET  /task     ← App buyruq tekshir  │    │                   │
│  │  └── [HMAC-SHA256 autentifikatsiya]        │    │                   │
│  └───────────────────────────────────────────┘    │                   │
│                                                   │                   │
│  Redis  (Railway addon)                           │                   │
│  ├── setup_token:{token}  TTL 30m                 │                   │
│  ├── status:{uid}:{cid}   TTL 5m                  │                   │
│  ├── allowed_users        Set ∞                   │                   │
│  └── progress:{cid}:{h}   ∞                       │                   │
└───────────────────────────────────────────────────▼───────────────────┘
                              │ HTTPS
┌─────────────────────────────▼───────────────────────────────────────────┐
│                    DESKTOP APP (foydalanuvchi kompyuteri)                │
│                                                                          │
│  Main thread: CustomTkinter GUI                                          │
│  ├── LoginFrame: config import / sozlash                                 │
│  ├── MainFrame: papka, progress bar, log, start/stop                     │
│  └── ThrottleDialog: akkaunt throttle ogohlantirishlari                  │
│                                                                          │
│  Background thread: asyncio event loop                                   │
│  ├── UploadEngine  ← send_all_media() orqali                             │
│  ├── GlobalWorkerPool (3–5 worker, bot token)                            │
│  │   ├── Rotation: 15 qism YOKI 5 min YOKI tezlik < 0.10 MB/s          │
│  │   └── Throttle detect: 30 min avtokutish                              │
│  └── APIClient → har 5s Railway ga progress/task                         │
│                                                                          │
│  Thread köprüsü: asyncio ↔ tkinter                                       │
│  ├── GUI → async: asyncio.run_coroutine_threadsafe(coro, loop)           │
│  └── async → GUI: root.after(0, callback)                                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DevOps Pipeline

### 2.1 Railway Deploy

```
GitHub main branch
       │
       │ (push)
       ▼
Railway Git webhook
       │
       ▼
nixpacks build
├── python 3.12
├── pip install -r requirements.txt
└── python main.py (start command)
       │
       ▼
Health check: GET /health → {"ok": true}
       │ (3 urinish → pass bo'lmasa deploy qaytariladi)
       ▼
Traffic shifted to new deployment
```

**railway.toml:**
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python main.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
healthcheckPath = "/health"
healthcheckTimeout = 30
```

**nixpacks.toml:**
```toml
[phases.setup]
nixPkgs = ["python312"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "python main.py"
```

### 2.2 GitHub Actions — 3 Platformali Build

```yaml
# .github/workflows/build-release.yml
name: Build Release

on:
  push:
    tags: ['v*']

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: windows-latest
            name: Windows
            artifact: Girgitton_Windows.exe
          - os: macos-latest
            name: macOS
            artifact: Girgitton_macOS.zip
          - os: ubuntu-latest
            name: Linux
            artifact: Girgitton_Linux.bin

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements-app.txt pyinstaller

      - name: Build executable
        run: pyinstaller build/girgitton.spec

      - name: Package (macOS only)
        if: matrix.os == 'macos-latest'
        run: |
          cd dist
          zip -r Girgitton_macOS.zip Girgitton.app

      - name: Upload to GitHub Releases
        uses: softprops/action-gh-release@v2
        with:
          files: dist/${{ matrix.artifact }}
          generate_release_notes: true
```

### 2.3 Release Workflow

```
1. Kod yoziladi, main'ga merge
2. git tag v1.2.3
3. git push --tags
4. GitHub Actions: 3 build parallel (Windows, macOS, Linux)
5. GitHub Release yaratiladi → fayllar yuklanadi
6. Bot /download javob URL'lari yangilanadi (tag-based URL)
```

### 2.4 Environment Variables Boshqaruvi

```
Lokal test:       .env fayli (gitignore'da)
Railway prod:     Railway Dashboard → Variables
Desktop App:      /setup → config.json (lokal saqlash)
```

---

## 3. Desktop App — To'liq Arxitektura

### 3.1 asyncio + tkinter Thread Modeli

```
┌─ Main Thread ──────────────────────┐   ┌─ Background Thread ──────────────────┐
│                                    │   │                                       │
│  tkinter mainloop()                │   │  asyncio.run(async_main())            │
│                                    │   │                                       │
│  root.after(0, update_ui)  ◄───────┼───┼── loop.call_soon_threadsafe(cb)       │
│                                    │   │                                       │
│  Button click ─────────────────────┼──►│  asyncio.run_coroutine_threadsafe()   │
│                                    │   │                                       │
└────────────────────────────────────┘   └───────────────────────────────────────┘
```

**Nima uchun bu model?**
- tkinter: faqat main thread'da xavfsiz
- asyncio: bloklovchi operatsiyalarni (upload, API) main thread'dan ajratadi
- `run_coroutine_threadsafe` + `call_soon_threadsafe` — ikki tomonga xavfsiz köprü

**app/__main__.py:**
```python
import asyncio
import threading
import tkinter as tk
from app.gui import App

def start_async_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_async_loop, args=(loop,), daemon=True)
    t.start()

    root = tk.Tk()
    app = App(root, loop)
    root.mainloop()

    loop.call_soon_threadsafe(loop.stop)
    t.join(timeout=5)
```

### 3.2 GUI Fayl Strukturasi

```
app/
├── __main__.py          ← Entry point (thread setup)
├── gui.py               ← App class, frame switching
├── login_frame.py       ← Config import oynasi
├── main_frame.py        ← Asosiy ish oynasi
├── throttle_dialog.py   ← Throttle ogohlantiruv dialogi
├── engine.py            ← Upload orchestrator
├── worker_pool.py       ← GlobalWorkerPool
├── api_client.py        ← Railway HTTPS API client
├── app_config.py        ← config.json saqlash/o'qish
└── assets/
    ├── icon.ico         ← Windows taskbar
    ├── icon.icns        ← macOS dock
    └── icon.png         ← Linux/fallback
```

### 3.3 Birinchi Ishga Tushirish Oqimi

```
1. Foydalanuvchi /setup yozadi Telegram'da
   └── Bot: config.json faylini yuboradi (one-time token bilan)

2. Girgitton.exe ochiladi
   └── config.json yo'q → LoginFrame ko'rinadi

3. "Import config" → faylni tanlaydi
   └── app_config.py: faylni parse qiladi, lokal saqlaydi

4. "Ismingiz:" → kiritadi (caption uchun)
   └── Saqlandi → MainFrame ochiladi

5. Keyingi safar: config bor → to'g'ri MainFrame
```

### 3.4 Asosiy Oyna

```
┌──────────────────────────────────────────────┐
│  Girgitton v2.0                    [─][□][×] │
│──────────────────────────────────────────────│
│                                              │
│  📁 Papka: [C:\Photos\Wedding       ] [📂]  │
│  🎯 Guruh:  Oila Media (-1001234567890)      │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  557 ta fayl  •  112 qism  •  2.3 GB │  │
│  │                                        │  │
│  │  ████████████████░░░░░░  78/112  70%  │  │
│  │                                        │  │
│  │  ⚡ 1.3 MB/s  •  ⏱ ~12 daqiqa qoldi  │  │
│  └────────────────────────────────────────┘  │
│                                              │
│     [ ▶️ Boshlash ]    [ ⏹ To'xtatish ]      │
│                                              │
│  ┌─ Log ─────────────────────────────────┐  │
│  │ 14:32:01 W0/B78 → photo_390.jpg ✓    │  │
│  │ 14:32:03 W1/B79 → video_012.mp4 ↑    │  │
│  │ 14:32:05 Qism 78 media album ✓       │  │
│  │ 14:32:07 Qism 78 document album ✓    │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ⬤ Bot ulangan  •  Worker: 3/3 faol         │
└──────────────────────────────────────────────┘
```

### 3.5 Throttle Dialog

```
┌──────────────────────────────────────────────┐
│  ⚠️  Telegram tezlikni chekladi              │
│                                              │
│  Tezlik: 0.02 MB/s  (normal: 1.3 MB/s)      │
│  Reconnect sinaldi — yordam bermadi          │
│                                              │
│  Sabab: Telegram akkaunt darajasida throttle │
│  Bu vaqtincha — odatda 30-60 daqiqada ochiladi│
│                                              │
│  ⏱ Avtomatik qayta urinish: 28:45           │
│  Progress saqlangan — hech narsa yo'qolmaydi │
│                                              │
│  [Hozir qayta urinish]   [To'xtatish]        │
└──────────────────────────────────────────────┘
```

---

## 4. Global Worker Pool — Uch Mezonli Rotation

### 4.1 v1 → v2 O'zgarishi

```
v1: Per-chat pool
  Chat A → [W0][W1][W2]  (3 session)
  Chat B → [W0][W1][W2]  (3 session)
  ...
  10 chat = 30 session → Telegram suspicious flag → ban xavfi

v2: Global pool
  [W0][W1][W2][W3][W4]   (max 5 session, xavfsiz)
  asyncio.Queue orqali barcha chatlar birgalikda xizmat oladi
```

### 4.2 Rotation Parametrlari

```python
ROTATE_AFTER_N_BATCHES: int = 15       # Qism soni mezoni
ROTATE_AFTER_SECONDS: int   = 300      # Vaqt mezoni (5 daqiqa)
SPEED_DROP_THRESHOLD: float = 0.10     # Tezlik mezoni (MB/s)

THROTTLE_SPEED_LIMIT: float = 0.05     # Akkaunt throttle aniqlash
THROTTLE_WAIT_SECONDS: int  = 1800     # 30 daqiqa avtokutish
```

### 4.3 Worker Logikasi

```python
async def _worker(self, worker_id: int, queue, notify, stop_flag, upload_futures):
    client = self._clients[worker_id]
    batches_done = 0
    speed_history: list[float] = []
    last_rotate = time.monotonic()

    while True:
        item = await queue.get()
        if item is None:   # poison pill
            queue.task_done()
            break

        batch_idx, batch, chat_id = item

        if stop_flag[0]:
            upload_futures[batch_idx].cancel()
            queue.task_done()
            continue

        # ── 3 mezonli rotation (qismlar orasida) ──
        should_rotate = (
            (batches_done > 0 and batches_done % ROTATE_AFTER_N_BATCHES == 0)
            or (time.monotonic() - last_rotate >= ROTATE_AFTER_SECONDS)
            or (len(speed_history) >= 3
                and sum(speed_history[-3:]) / 3 < SPEED_DROP_THRESHOLD)
        )

        if should_rotate:
            await _reconnect(client, f"W{worker_id}")
            speed_history.clear()
            last_rotate = time.monotonic()

        # ── Upload ──
        t0 = time.perf_counter()
        size_mb = sum(p.stat().st_size for p in batch) / 1_048_576

        result = await _upload_batch_files(client, worker_id, batch_idx, batch, notify, stop_flag)
        elapsed = time.perf_counter() - t0
        speed = size_mb / elapsed if elapsed else 0

        speed_history.append(speed)
        batches_done += 1

        # ── Akkaunt throttle aniqlash ──
        if speed < THROTTLE_SPEED_LIMIT and should_rotate:
            # Reconnect ham yordam bermadi → akkaunt darajasida cheklov
            await notify(
                "⚠️ Telegram akkaunt darajasida tezlikni chekladi.\n"
                f"30 daqiqa kutilmoqda... Progress saqlandi (qism {batch_idx})."
            )
            save_progress(chat_id, batch_idx)
            await asyncio.sleep(THROTTLE_WAIT_SECONDS)
            await _reconnect(client, f"W{worker_id}")
            last_rotate = time.monotonic()

        upload_futures[batch_idx].set_result(result)
        queue.task_done()
```

### 4.4 Reconnect (Bot Token)

```python
async def _reconnect(client: TelegramClient, label: str) -> None:
    try:
        await client.disconnect()
        await asyncio.sleep(3)
        await client.start(bot_token=config.BOT_TOKEN)
        logger.info("%s: sessiya yangilandi (fresh bandwidth)", label)
    except Exception as exc:
        logger.warning("%s: reconnect xatosi: %s — davom etiladi", label, exc)
        with suppress(Exception):
            await client.start(bot_token=config.BOT_TOKEN)
```

---

## 5. Railway Bot + Mini API

### 5.1 Bot Buyruqlari

| Buyruq | Ruxsat | Vazifasi |
|--------|--------|---------|
| `/start` | Barcha | Yordam xabari |
| `/download` | Ruxsatli | Desktop app yuklab olish (GitHub Releases) |
| `/setup` | Ruxsatli | Config JSON + one-time token yaratish |
| `/status` | Ruxsatli | App holati (Redis'dan) |
| `/stop` | Egasi/yuboruvchi | App ga API orqali stop signal |
| `/allow <ID>` | Faqat egasi | Foydalanuvchi qo'shish |
| `/disallow <ID>` | Faqat egasi | Foydalanuvchi o'chirish |
| `/allowed` | Faqat egasi | Ro'yxat ko'rsatish |

### 5.2 Mini API Endpointlar

| Endpoint | Metod | Auth | Vazifasi |
|----------|-------|------|---------|
| `/health` | GET | Yo'q | Railway health check |
| `/connect` | POST | HMAC | App birinchi ulanish + token validate |
| `/status` | POST | HMAC | App progress yuboradi |
| `/task` | GET | HMAC | App buyruq tekshiradi |

### 5.3 HMAC Autentifikatsiya

```python
import hashlib
import hmac as _hmac

async def _verify_hmac(request: web.Request) -> bool:
    body = await request.read()
    secret = os.environ["API_SECRET"].encode()
    expected = _hmac.new(secret, body, hashlib.sha256).hexdigest()
    received = request.headers.get("X-Signature", "")
    return _hmac.compare_digest(expected, received)
```

Desktop app ham bir xil HMAC hisoblaydi:
```python
def _sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

headers = {"X-Signature": _sign(body, self.api_secret)}
```

### 5.4 `/setup` — One-Time Config

```python
@client.on(events.NewMessage(pattern=r"^/setup(@\w+)?$"))
async def cmd_setup(event):
    if not _is_allowed(event.sender_id):
        await event.reply("⛔ Ruxsat yo'q.")
        return

    token = secrets.token_urlsafe(32)
    await redis.setex(f"setup_token:{token}", 1800, "valid")

    config_data = {
        "bot_token": config.BOT_TOKEN,
        "api_id": config.API_ID,
        "api_hash": config.API_HASH,
        "api_url": f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN', '')}",
        "api_secret": os.getenv("API_SECRET", ""),
        "group_id": event.chat_id,
        "setup_token": token,
    }

    tmp = Path(f"/tmp/girgitton_{token[:8]}.json")
    tmp.write_text(json.dumps(config_data, indent=2))
    await event.reply(
        "📎 **Config fayl** (BIR MARTALIK, 30 daqiqa)\n\n"
        "1. Faylni yuklab oling\n"
        "2. Girgitton app → Import config\n"
        "3. Ismingizni kiriting → boshlang",
        file=str(tmp), parse_mode="md",
    )
    tmp.unlink(missing_ok=True)
```

### 5.5 Bot + API Birgalikda

```python
async def main() -> None:
    await init_storage()            # Redis yoki JSON fallback
    await client.start(bot_token=config.BOT_TOKEN)

    runner = web.AppRunner(build_api())
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    logger.info("API ishga tushdi port=%d", port)

    try:
        await client.run_until_disconnected()
    finally:
        await runner.cleanup()
```

---

## 6. Storage — Redis + JSON Fallback

### 6.1 Railway Redis Sozlash

```
Railway Dashboard
  → New Service
  → Database → Redis
  → Deploy
  → Otomatik: REDIS_URL qo'shiladi
```

### 6.2 Saqlanadigan Ma'lumotlar

| Kalit | TTL | Tavsif |
|-------|-----|--------|
| `setup_token:{token}` | 30 min | One-time config token |
| `status:{uid}:{cid}` | 5 min | App progress (auto-expire) |
| `allowed_users` | ∞ | Redis Set — dinamik ruxsatlar |
| `progress:{cid}:{folder_hash}` | ∞ | Qism progress |

### 6.3 storage.py — Abstraction Layer

```python
async def init_storage() -> None:
    global _redis
    url = os.getenv("REDIS_URL")
    if url:
        try:
            _redis = aioredis.from_url(url, decode_responses=True)
            await _redis.ping()
            logger.info("Redis ulandi")
        except Exception as exc:
            logger.warning("Redis xato → JSON fallback: %s", exc)
            _redis = None

# Barcha funksiyalar: Redis mavjud bo'lsa Redis, yo'q bo'lsa JSON fayl
async def save_progress(chat_id: int, folder: str, batch: int) -> None: ...
async def load_progress(chat_id: int, folder: str) -> int: ...
async def add_allowed_user(user_id: int) -> None: ...
async def load_allowed_users() -> set[int]: ...
```

---

## 7. App ↔ Bot Aloqa Oqimi

### 7.1 Setup

```
Foydalanuvchi          Bot (Railway)              App (Kompyuter)
     │                      │                           │
     ├── /setup ───────────►│                           │
     │◄── config.json ──────│                           │
     │                      │                           │
     │── app ochadi ─────────────────────────────────►  │
     │                      │                           ├── POST /connect
     │                      │◄── {setup_token, ...} ────┤
     │                      ├── token validate ──────── │
     │                      ├── {"ok": true} ──────────►│
     │                      │                           └── MainFrame ochiladi
```

### 7.2 Upload Jarayoni

```
App                                        Railway Bot
 │                                              │
 ├── upload → Telegram API (to'g'ri) → Guruh   │
 │                                              │
 ├── POST /status (har 5s) ────────────────────►│
 │    {user_id, chat_id, batch, total, speed}   │
 │                                              ├── Redis: setex status 5min
 │◄── {"ok": true} ─────────────────────────────┤
 │                                              │
 ├── GET /task (har 5s) ────────────────────────►│
 │◄── {"action": null} ─────────────────────────┤
 │                                              │
```

### 7.3 Stop Signali

```
Foydalanuvchi       Railway Bot              App
     │                   │                    │
     ├── /stop ─────────►│                    │
     │                   ├── stop_cmd[key] ──►│ (xotirada)
     │                   │                    │
     │                   │    GET /task ◄──── │ (5s da bir tekshiradi)
     │                   ├── {"action":"stop"}►│
     │                   │                    ├── stop_flag[0] = True
     │                   │                    ├── upload to'xtaydi
     │◄── "🛑 To'xtatildi"│                   └── progress saqlanadi
```

---

## 8. Build va Distribution

### 8.1 PyInstaller Spec

```python
# build/girgitton.spec
block_cipher = None

a = Analysis(
    ['app/__main__.py'],
    pathex=['.'],
    binaries=[],
    datas=[('app/assets', 'assets')],
    hiddenimports=['customtkinter', 'telethon', 'aiohttp'],
    hookspath=[],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name='Girgitton',
    debug=False,
    onefile=True,
    windowed=True,           # konsol oynasi yo'q (Windows)
    icon='app/assets/icon.ico',
)
```

### 8.2 Build Buyruqlari

```bash
# Windows (lokal test)
pip install pyinstaller
pyinstaller build/girgitton.spec
# dist/Girgitton.exe (~35-40 MB)

# macOS
pyinstaller build/girgitton.spec
cd dist && zip -r Girgitton_macOS.zip Girgitton.app

# Linux
pyinstaller build/girgitton.spec
# dist/Girgitton
```

### 8.3 Release Chiqarish

```bash
git tag v2.0.0
git push --tags
# GitHub Actions avtomatik 3 platform build qiladi
# GitHub Release yaratiladi, fayllar yuklanadi
# Bot /download link'lari tag-based → har yangi reliz avtomatik
```

---

## 9. Fayl Strukturasi (v2 to'liq)

```
girgitton/
│
├── app/                          ← Desktop App (CustomTkinter)
│   ├── __main__.py               ← Entry point (thread setup)
│   ├── gui.py                    ← App class, frame switching
│   ├── login_frame.py            ← Config import oynasi
│   ├── main_frame.py             ← Asosiy ish oynasi
│   ├── throttle_dialog.py        ← Throttle ogohlantiruv dialogi
│   ├── engine.py                 ← Upload orchestrator (asyncio)
│   ├── worker_pool.py            ← GlobalWorkerPool + rotation
│   ├── api_client.py             ← Railway API HTTPS client
│   ├── app_config.py             ← config.json saqlash/o'qish
│   └── assets/
│       ├── icon.ico
│       ├── icon.icns
│       └── icon.png
│
├── main.py                       ← Railway: bot + mini API birgalikda
├── api.py                        ← aiohttp endpointlar (/health, /connect, /status, /task)
├── storage.py                    ← Redis + JSON fallback abstraction
├── sender.py                     ← send_all_media() (v1 dan o'zgarishsiz)
├── uploader.py                   ← UploadPool + vaqt rotation qo'shiladi
├── helpers.py                    ← Logging, scan, chunked (o'zgarishsiz)
├── config.py                     ← + ROTATE_AFTER_SECONDS, API_SECRET
│
├── build/
│   ├── girgitton.spec            ← PyInstaller spec
│   └── build.sh                  ← Lokal build skripti
├── .github/
│   └── workflows/
│       └── build-release.yml     ← GitHub Actions
│
├── requirements.txt              ← Railway: telethon, dotenv, redis, aiohttp
├── requirements-app.txt          ← Desktop: telethon, customtkinter, aiohttp
├── .env.example                  ← + REDIS_URL, API_SECRET, RAILWAY_PUBLIC_DOMAIN
├── .env                          ← Gitignore (lokal)
├── Procfile                      ← worker: python main.py
├── railway.toml                  ← Railway deploy + health check
├── nixpacks.toml                 ← Build config
├── .gitignore                    ← + dist/, build/, *.session
├── project.md                    ← v1 hujjati
├── project2.md                   ← Shu hujjat
└── README.md                     ← Yangilanadi
```

---

## 10. Environment Variables

### Railway Dashboard

| Variable | Misol | Majburiy |
|----------|-------|---------|
| `API_ID` | `32710838` | ✅ |
| `API_HASH` | `e857db...` | ✅ |
| `BOT_TOKEN` | `8230570853:AAE...` | ✅ |
| `OWNER_ID` | `5567796386` | ✅ |
| `REDIS_URL` | `redis://default:xxx@host:port` | ✅ (Railway auto) |
| `API_SECRET` | `random_64_char_string` | ✅ |
| `RAILWAY_PUBLIC_DOMAIN` | `girgitton.up.railway.app` | ✅ |
| `PORT` | `8080` | Railway auto |
| `ALLOWED_USERS` | `5770408879,123456` | ixtiyoriy |
| `UPLOAD_WORKERS` | `3` | ixtiyoriy |
| `ROTATE_AFTER_N_BATCHES` | `15` | ixtiyoriy |
| `ROTATE_AFTER_SECONDS` | `300` | ixtiyoriy |
| `SPEED_DROP_THRESHOLD` | `0.10` | ixtiyoriy |

### Desktop App config.json (bot /setup tomonidan yaratiladi)

```json
{
  "bot_token": "8230570853:AAE...",
  "api_id": 32710838,
  "api_hash": "e857db...",
  "api_url": "https://girgitton.up.railway.app",
  "api_secret": "random_64_char_string",
  "group_id": -1001234567890,
  "setup_token": "abc123...",
  "display_name": "Azizbek",
  "upload_workers": 3,
  "last_folder": "C:\\Photos\\Wedding"
}
```

---

## 11. Dependencies

### requirements.txt (Railway bot)
```
telethon>=1.34.0
python-dotenv>=1.0.0
redis>=5.0.0
aiohttp>=3.9.0
```

### requirements-app.txt (Desktop app)
```
telethon>=1.34.0
customtkinter>=5.2.0
aiohttp>=3.9.0
```

---

## 12. Amalga Oshirish Tartibi

### Faza 1: Storage va API (2-3 soat) — BIRINCHI

> Nima uchun birinchi? Qolgan hamma narsa bunga bog'liq.

| # | Vazifa | Fayl | Vaqt |
|---|--------|------|------|
| 1.1 | `storage.py` — Redis + JSON fallback | `storage.py` | 1s |
| 1.2 | `api.py` — `/health`, `/connect`, `/status`, `/task` + HMAC | `api.py` | 1s |
| 1.3 | `main.py` — bot + API birgalikda, `/setup`, `/download`, `/status` buyruqlari | `main.py` | 1s |
| 1.4 | Railway: Redis addon qo'shish, `API_SECRET`, `RAILWAY_PUBLIC_DOMAIN` | Railway dashboard | 15d |
| 1.5 | `uploader.py` — vaqt mezoni (`ROTATE_AFTER_SECONDS`) qo'shish | `uploader.py` | 30d |
| 1.6 | Railway deploy, health check test | — | 15d |

### Faza 2: Desktop App asosi (4-5 soat) — IKKINCHI

| # | Vazifa | Fayl | Vaqt |
|---|--------|------|------|
| 2.1 | `app_config.py` — lokal config saqlash | `app/app_config.py` | 30d |
| 2.2 | `__main__.py` — thread setup | `app/__main__.py` | 15d |
| 2.3 | `login_frame.py` — config import UI | `app/login_frame.py` | 45d |
| 2.4 | `main_frame.py` — progress bar, log, start/stop | `app/main_frame.py` | 1.5s |
| 2.5 | `gui.py` — frame switching | `app/gui.py` | 30d |
| 2.6 | `worker_pool.py` — GlobalWorkerPool (global, 5 max) | `app/worker_pool.py` | 1s |
| 2.7 | `engine.py` — upload orchestrator | `app/engine.py` | 1s |
| 2.8 | `api_client.py` — Railway HTTPS client (har 5s) | `app/api_client.py` | 45d |
| 2.9 | `throttle_dialog.py` — ogohlantiruv dialogi | `app/throttle_dialog.py` | 30d |

### Faza 3: Build va CI/CD (2 soat) — UCHINCHI

| # | Vazifa | Fayl | Vaqt |
|---|--------|------|------|
| 3.1 | `build/girgitton.spec` — PyInstaller spec | `build/girgitton.spec` | 30d |
| 3.2 | Windows lokal build test | — | 30d |
| 3.3 | `.github/workflows/build-release.yml` — GitHub Actions | `build-release.yml` | 45d |
| 3.4 | v2.0.0 tag push, 3 platform build test | — | 15d |

### Faza 4: Polish (1-2 soat) — TO'RTINCHI

| # | Vazifa | Fayl | Vaqt |
|---|--------|------|------|
| 4.1 | Drag & drop papka (tkinter dnd) | `app/main_frame.py` | 30d |
| 4.2 | Ikonka yaratish (Windows/Mac/Linux) | `app/assets/` | 30d |
| 4.3 | `.env.example` yangilash | `.env.example` | 10d |
| 4.4 | README.md to'liq yangilash | `README.md` | 45d |
| 4.5 | `companion.py` arxivga o'tkazish (deprecated) | — | 5d |

**Jami: ~10-12 soat**

---

## 13. v1 → v2 O'tish Xaritasi

| v1 komponent | v2 holati | Izoh |
|-------------|-----------|------|
| `main.py` (faqat bot) | `main.py` (bot + API) | `/setup`, `/download`, `/status` qo'shiladi |
| `config.py` (JSON file) | `storage.py` (Redis + JSON) | Async funksiyalar |
| `companion.py` | `app/` (Desktop App) | To'liq almashtiradi |
| `picker.py` | `app/gui.py` ichida | Native file dialog |
| `uploader.py` (per-chat) | `app/worker_pool.py` (global) | +vaqt mezoni |
| `sender.py` | O'zgarishsiz | App ham ishlatadi |
| `helpers.py` | O'zgarishsiz | App ham ishlatadi |
| Yangi | `api.py`, `storage.py`, `app/`, `build/`, `.github/` | — |

---

## 14. Tezlik Prognozi

| Holat | Upload tezlik | 500 fayl × 4 MB |
|-------|--------------|-----------------|
| v1: 1 worker (throttled) | 0.05–0.10 MB/s | ~13 soat |
| v1: 3 worker + pipeline | 0.15–0.45 MB/s | ~4-5 soat |
| v2: 3 worker + uch mezonli rotation | 0.30–0.80 MB/s | ~2-3 soat |
| v2: 5 worker + rotation | 0.40–1.00 MB/s | ~1.5-2.5 soat |

> Tezlanish asosan rotation optimallashtirish (vaqt + tezlik mezoni) va global pool
> tufayli. Bot token throttle chegarasi Telegram tomonidan o'zgarmaydi —
> yaxshilanish throttle'dan "qochish" emas, balki uni tezroq aniqlash va reset qilish.

---

## 15. Ko'p Foydalanuvchi Bir Guruhda

```
Guruh:
┌────────────────────────────────────────────┐
│ 🤖 Girgitton Bot                           │
│    📸📸📸📸📸                              │
│    📤 Azizbek • Qism 12/45                │
│                                            │
│ 🤖 Girgitton Bot                           │
│    📸📸📸📸📸                              │
│    📤 Sardor • Qism 7/30                  │
└────────────────────────────────────────────┘
```

Caption `"{display_name} • Qism N/M"` orqali kim yuborganini ajratib ko'rsatiladi.
Global pool har foydalanuvchining qismlarini navbat bilan xizmat qiladi — biri
boshqasini bloklolmaydi.
