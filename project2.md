# Girgitton v2 — To'liq Loyiha va DevOps Rejasi

> **Status**: Reja (v1 ishda, v2 rivojlantirilmoqda)
> **Hujjat yangilandi**: 2026-04-26 (v2.1 — Secure Pairing)
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
| App↔Bot ulanish (lokal) | **Auto-connect** | App `localhost:8080` ga avtomatik ulanadi, 0 qadam |
| App↔Bot ulanish (remote) | **Deep Link** (`girgitton://`) | Guruhda `/pair` → inline tugma → App avtomatik ochiladi |
| App↔Bot ulanish (fallback) | **6 xonali pair code** | Deep link ishlamasa, kod kiritiladi (5 daqiqa TTL) |
| Credential uzatish | **API orqali** | JSON fayl YARATILMAYDI — faqat HTTPS/localhost orqali |
| Guruh aniqlash | **Avtomatik** | `/pair` yuborilgan guruh avtomatik ro'yxatga olinadi |
| Ko'p guruh | **Parallel upload** | Bir nechta guruhga teng yuborish |
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
│  │  ├── /start, /download                    │    │                   │
│  │  ├── /pair (guruhda → auto group detect)  │    │                   │
│  │  ├── /status, /stop                       │    │                   │
│  │  └── /allow, /disallow, /allowed          │    │                   │
│  │                                           │    │                   │
│  │  aiohttp Mini API  (port 8080)            │    │                   │
│  │  ├── GET  /health       ← health check    │    │                   │
│  │  ├── GET  /auto-pair    ← lokal auto      │    │                   │
│  │  ├── POST /pair         ← code validate   │    │                   │
│  │  ├── GET  /groups       ← faol guruhlar   │    │                   │
│  │  ├── POST /status       ← App progress    │    │                   │
│  │  ├── GET  /task         ← buyruq tekshir  │    │                   │
│  │  └── [HMAC-SHA256 autentifikatsiya]        │    │                   │
│  └───────────────────────────────────────────┘    │                   │
│                                                   │                   │
│  Redis  (Railway addon)                           │                   │
│  ├── pair_code:{CODE}    TTL 5m                   │                   │
│  ├── active_groups       Hash {gid: title}        │                   │
│  ├── status:{uid}:{cid}  TTL 5m                   │                   │
│  ├── allowed_users       Set ∞                    │                   │
│  └── progress:{cid}:{h}  ∞                        │                   │
└───────────────────────────────────────────────────▼───────────────────┘
                              │ HTTPS / localhost
┌─────────────────────────────▼───────────────────────────────────────────┐
│                    DESKTOP APP (foydalanuvchi kompyuteri)                │
│                                                                          │
│  Main thread: CustomTkinter GUI                                          │
│  ├── LoginFrame: auto-connect / pair code / deep link                    │
│  ├── MainFrame: papka, guruhlar ro'yxati, progress, log, start/stop      │
│  └── ThrottleDialog: akkaunt throttle ogohlantirishlari                  │
│                                                                          │
│  Background thread: asyncio event loop                                   │
│  ├── UploadEngine  ← send_all_media() → barcha faol guruhlarga          │
│  ├── GlobalWorkerPool (3–5 worker, bot token)                            │
│  │   ├── Rotation: 15 qism YOKI 5 min YOKI tezlik < 0.10 MB/s          │
│  │   └── Throttle detect: 30 min avtokutish                              │
│  └── APIClient → har 5s Railway ga progress/task                         │
│                                                                          │
│  Pairing oqimi:                                                          │
│  ├── Lokal:  localhost:8080/auto-pair → credentials avtomatik            │
│  ├── Remote: girgitton://connect?token=X&server=URL → deep link          │
│  └── Manual: 6 xonali kod kiritish (fallback)                            │
│                                                                          │
│  Credential saqlash: ~/.girgitton/credentials.json (lokal, xavfsiz)      │
│  Session fayllar:    ~/.girgitton/worker_N.session                        │
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

#### A. Lokal (bot va app bir mashinada) — 0 qadamlik

```
1. Foydalanuvchi python main.py ishga tushiradi
   └── Bot: Telegram ulanadi, API localhost:8080 da ishga tushadi

2. Foydalanuvchi guruhda /pair yozadi
   └── Bot: guruhni active_groups ga qo'shadi
   └── Bot: "✅ Guruh faollashdi. Desktop App oching" deydi

3. Girgitton.exe ochiladi
   └── Saqlangan credentials yo'q → LoginFrame ko'rinadi
   └── LoginFrame: localhost:8080/auto-pair ga avtomatik so'rov
   └── Bot API: credentials qaytaradi (faqat 127.0.0.1 dan)
   └── App: credentials saqlaydi → MainFrame ochiladi

4. Keyingi safar: credentials bor → to'g'ri MainFrame
```

#### B. Remote (Railway) — 1 bosilishlik

```
1. Bot Railway da 24/7 ishlaydi

2. Foydalanuvchi guruhda /pair yozadi
   └── Bot: 6 xonali kod yaratadi (A7X92K, 5 daqiqa TTL)
   └── Bot: inline tugma yuboradi:
       🔗 "Desktop App da ochish" → girgitton://connect?code=A7X92K&server=https://...
       📋 "Kod: A7X92K"

3a. Foydalanuvchi inline tugma bosadi (Deep Link)
    └── OS: Girgitton.exe ochiladi (custom protocol handler)
    └── App: URL dan code va server olinadi
    └── App: POST /pair {code} → credentials oladi
    └── MainFrame ochiladi

3b. Deep link ishlamasa (fallback)
    └── Foydalanuvchi App ni qo'lda ochadi
    └── Server URL: https://girgitton.up.railway.app
    └── Pair Code: A7X92K
    └── "Ulash" bosadi → POST /pair → credentials oladi
```

#### C. Bir nechta guruh qo'shish

```
1. Birinchi guruhda /pair → guruh A faollashadi
2. Ikkinchi guruhda /pair → guruh B ham faollashadi
3. App GET /groups → [guruh A, guruh B] oladi
4. Upload boshlanadi → har batch BARCHA guruhlarga yuboriladi
```

### 3.4 Asosiy Oyna

```
┌──────────────────────────────────────────────┐
│  Girgitton v2.0                    [─][□][×] │
│──────────────────────────────────────────────│
│                                              │
│  📁 Papka: [C:\Photos\Wedding       ] [📂]  │
│                                              │
│  🎯 Faol guruhlar:                           │
│  ├── ✅ Oila Media     (-1001234567890)      │
│  ├── ✅ Ish guruh      (-1001987654321)      │
│  └── [+ Guruh qo'shish (/pair guruhda)]     │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  557 ta fayl  •  112 qism  •  2.3 GB │  │
│  │  2 ta guruhga yuborilmoqda             │  │
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
│  │ 14:32:05 → Oila Media: qism 78 ✓     │  │
│  │ 14:32:06 → Ish guruh: qism 78 ✓      │  │
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
| `/download` | Barcha | Desktop app yuklab olish (GitHub Releases) |
| `/pair` | Ruxsatli, faqat guruhda | Guruhni faollashtirish + pair code yaratish |
| `/unpair` | Ruxsatli, faqat guruhda | Guruhni faol ro'yxatdan o'chirish |
| `/groups` | Ruxsatli | Faol guruhlar ro'yxati |
| `/status` | Ruxsatli | App holati (Redis'dan) |
| `/stop` | Egasi/yuboruvchi | App ga API orqali stop signal |
| `/allow <ID>` | Faqat egasi | Foydalanuvchi qo'shish |
| `/disallow <ID>` | Faqat egasi | Foydalanuvchi o'chirish |
| `/allowed` | Faqat egasi | Ro'yxat ko'rsatish |

### 5.2 Mini API Endpointlar

| Endpoint | Metod | Auth | Vazifasi |
|----------|-------|------|---------|
| `/health` | GET | Yo'q | Railway health check |
| `/auto-pair` | GET | Localhost-only (127.0.0.1) | Lokal avtomatik ulanish |
| `/pair` | POST | Yo'q (kod o'zi auth) | Pair code validate, credentials qaytarish |
| `/groups` | GET | HMAC | Faol guruhlar ro'yxati |
| `/status` | POST | HMAC | App progress yuboradi |
| `/task` | GET | HMAC | App buyruq tekshiradi (stop va h.k.) |

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

### 5.4 `/pair` — Xavfsiz Ulanish (JSON fayl yo'q!)

**Bot buyrug'i (guruhda):**
```python
@client.on(events.NewMessage(pattern=r"^/pair(@\w+)?$"))
async def cmd_pair(event):
    if event.is_private:
        await event.reply("Bu buyruq faqat guruhda ishlaydi!")
        return

    chat = await event.get_chat()
    await storage.add_active_group(event.chat_id, chat.title)

    code = _generate_pair_code()  # "A7X92K"
    await storage.save_pair_code(code, {
        "group_id": event.chat_id,
        "group_title": chat.title,
        "user_id": event.sender_id,
    }, ttl=300)

    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
    server = f"https://{domain}" if domain else "http://localhost:8080"
    deep_link = f"girgitton://connect?code={code}&server={server}"

    await event.reply(
        f"Guruh faollashdi: {chat.title}\n\n"
        f"Pair Code: {code}\n"
        f"Kod 5 daqiqa amal qiladi.\n\n"
        f"Desktop App oching — lokal avtomatik ulanadi.\n"
        f"Yoki shu linkni bosing: {deep_link}",
        parse_mode="md",
    )
```

**API — POST /pair:**
```python
async def handle_pair(request):
    data = await request.json()
    code = data.get("code", "").strip().upper()

    pair_data = await storage.consume_pair_code(code)
    if not pair_data:
        return json_response({"error": "Kod yaroqsiz"}, 403)

    return json_response({
        "ok": True,
        "credentials": {
            "api_id": config.API_ID,
            "api_hash": config.API_HASH,
            "bot_token": config.BOT_TOKEN,
        },
        "group": {
            "id": pair_data["group_id"],
            "title": pair_data["group_title"],
        },
        "api_secret": os.getenv("API_SECRET", ""),
    })
```

**API — GET /auto-pair (faqat localhost):**
```python
async def handle_auto_pair(request):
    peer = request.remote
    if peer not in ("127.0.0.1", "::1", "localhost"):
        return json_response({"error": "Faqat lokal"}, 403)

    groups = await storage.get_active_groups()
    return json_response({
        "ok": True,
        "credentials": {
            "api_id": config.API_ID,
            "api_hash": config.API_HASH,
            "bot_token": config.BOT_TOKEN,
        },
        "groups": groups,
        "api_secret": os.getenv("API_SECRET", ""),
    })
```

### 5.5 Xavfsizlik Taqqoslash

| Xavf | Eski (JSON fayl) | Yangi (Pair Code) |
|------|-------------------|-------------------|
| Credentials faylda | BOT_TOKEN, API_HASH ochiq | Fayl YARATILMAYDI |
| Faylni kimdir olsa | Botni to'liq nazorat | Kod 5 daqiqada o'ladi |
| Man-in-the-middle | Telegram orqali fayl | Localhost yoki HTTPS |
| Replay attack | Token 30 daqiqa | Kod bir martalik, 5 daqiqa |
| Noto'g'ri group_id | DM da /setup = xato ID | Avtomatik, /pair faqat guruhda |

### 5.6 Bot + API Birgalikda

```python
async def main() -> None:
    await init_storage()
    await client.start(bot_token=config.BOT_TOKEN)

    runner = web.AppRunner(build_api())
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", port).start()

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
| `pair_code:{CODE}` | 5 min | 6 xonali pair kod + group_id, bir martalik |
| `active_groups` | ∞ | Hash — {group_id: title} |
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
async def save_pair_code(code: str, data: dict, ttl: int = 300) -> None: ...
async def consume_pair_code(code: str) -> dict | None: ...
async def add_active_group(group_id: int, title: str) -> None: ...
async def remove_active_group(group_id: int) -> None: ...
async def get_active_groups() -> list[dict]: ...
async def save_progress(chat_id: int, folder: str, batch: int) -> None: ...
async def load_progress(chat_id: int, folder: str) -> int: ...
async def add_allowed_user(user_id: int) -> None: ...
async def load_allowed_users() -> set[int]: ...
```

---

## 7. App ↔ Bot Aloqa Oqimi

### 7.1 Pairing (Lokal — Auto-Connect)

```
App (Kompyuter)                 Bot (localhost:8080)
     │                                │
     ├── GET /auto-pair ─────────────►│
     │   (127.0.0.1 tekshiradi)       │
     │◄── {credentials, groups} ──────│
     │                                │
     └── Credentials saqlandi         │
         MainFrame ochiladi           │
```

### 7.2 Pairing (Remote — Deep Link / Pair Code)

```
Foydalanuvchi          Bot (Railway)              App (Kompyuter)
     │                      │                           │
     ├── /pair (guruhda) ──►│                           │
     │◄── "Kod: A7X92K" ───│                           │
     │    + deep link tugma │                           │
     │                      │                           │
     │── tugma bosadi ──────────────────────────────►  │
     │   girgitton://connect?code=A7X92K&server=URL    │
     │                      │                           │
     │                      │◄── POST /pair {code} ────┤
     │                      ├── validate ──────────────►│
     │                      ├── {credentials, group} ──►│
     │                      │                           │
     │                      │                  MainFrame ochiladi
```

### 7.3 Multi-Group Upload Jarayoni

```
App                                        Railway Bot
 │                                              │
 ├── GET /groups ─────────────────────────────►│
 │◄── [{id: -100A, title: "Oila"}, ...] ──────│
 │                                              │
 ├── upload batch 1 → Telegram → Guruh A       │
 ├── upload batch 1 → Telegram → Guruh B       │
 ├── upload batch 2 → Telegram → Guruh A       │
 ├── upload batch 2 → Telegram → Guruh B       │
 │  ...                                         │
 │                                              │
 ├── POST /status (har 5s) ────────────────────►│
 │    {user_id, groups, batch, total, speed}    │
 │◄── {"ok": true} ─────────────────────────────│
 │                                              │
 ├── GET /task (har 5s) ────────────────────────►│
 │◄── {"action": null} ─────────────────────────│
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
│   ├── __main__.py               ← Entry point (thread + logging setup)
│   ├── gui.py                    ← App class, frame switching
│   ├── login_frame.py            ← Auto-connect / pair code / deep link
│   ├── main_frame.py             ← Guruhlar, papka, progress, log
│   ├── throttle_dialog.py        ← Throttle ogohlantiruv dialogi
│   ├── engine.py                 ← Multi-group upload orchestrator
│   ├── worker_pool.py            ← GlobalWorkerPool + rotation
│   ├── api_client.py             ← API client (pair, groups, status, task)
│   ├── app_config.py             ← ~/.girgitton/credentials.json
│   └── assets/
│       ├── icon.ico
│       ├── icon.icns
│       └── icon.png
│
├── main.py                       ← Bot + mini API birgalikda
├── api.py                        ← /health, /auto-pair, /pair, /groups, /status, /task
├── storage.py                    ← Redis + JSON fallback (pair_code, active_groups)
├── sender.py                     ← send_all_media() (v1 dan o'zgarishsiz)
├── helpers.py                    ← Logging, scan, chunked
├── config.py                     ← Telegram + rotation sozlamalari
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
├── .env.example
├── .env                          ← Gitignore (lokal)
├── railway.toml                  ← Railway deploy + health check
├── nixpacks.toml                 ← Build config
├── .gitignore
├── project2.md                   ← Shu hujjat
└── README.md

~/.girgitton/                     ← Desktop App lokal ma'lumotlar
├── credentials.json              ← API credentials (pair orqali olingan)
├── desktop_app.log               ← App log fayli
├── worker_0.session              ← Telethon session fayllar
├── worker_1.session
└── worker_2.session
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

### Desktop App ~/.girgitton/credentials.json (API orqali olinadi, fayl YARATILMAYDI)

```json
{
  "api_id": 32710838,
  "api_hash": "e857db...",
  "bot_token": "8230570853:AAE...",
  "api_url": "http://localhost:8080",
  "api_secret": "random_64_char_string",
  "groups": [
    {"id": -1001234567890, "title": "Oila Media"},
    {"id": -1001987654321, "title": "Ish guruh"}
  ],
  "display_name": "Azizbek",
  "last_folder": "C:\\Photos\\Wedding"
}
```

> **Xavfsizlik:** Bu fayl faqat foydalanuvchining kompyuterida (`~/.girgitton/`)
> saqlanadi. Telegram orqali fayl sifatida HECH QACHON yuborilmaydi.
> Credentials faqat `POST /pair` yoki `GET /auto-pair` orqali olinadi.

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

### Faza 1: Xavfsiz Pairing Infra (2-3 soat) — BIRINCHI

> Nima uchun birinchi? Desktop App ulanishi bunga bog'liq.

| # | Vazifa | Fayl | Vaqt |
|---|--------|------|------|
| 1.1 | `storage.py` — pair_code, active_groups, Redis + JSON fallback | `storage.py` | 1s |
| 1.2 | `api.py` — `/auto-pair`, `POST /pair`, `/groups`, `/status`, `/task` | `api.py` | 1.5s |
| 1.3 | `main.py` — `/pair`, `/unpair`, `/groups`, `/download` buyruqlari | `main.py` | 1s |
| 1.4 | `/setup` va `/connect` o'chirish | `main.py`, `api.py` | 15d |
| 1.5 | Railway: Redis addon, `API_SECRET`, `RAILWAY_PUBLIC_DOMAIN` | Railway dashboard | 15d |
| 1.6 | Lokal test: `/pair` guruhda → Desktop App auto-connect | — | 30d |

### Faza 2: Desktop App yangilash (4-5 soat) — IKKINCHI

| # | Vazifa | Fayl | Vaqt |
|---|--------|------|------|
| 2.1 | `app_config.py` — ~/.girgitton/credentials.json | `app/app_config.py` | 30d |
| 2.2 | `__main__.py` — logging + deep link protocol handler | `app/__main__.py` | 30d |
| 2.3 | `login_frame.py` — auto-connect + pair code UI (fayl tanlash o'chiriladi) | `app/login_frame.py` | 1s |
| 2.4 | `api_client.py` — `pair()`, `auto_pair()`, `get_groups()` metodlar | `app/api_client.py` | 45d |
| 2.5 | `main_frame.py` — guruhlar ro'yxati, multi-group progress | `app/main_frame.py` | 1.5s |
| 2.6 | `engine.py` — multi-group upload orchestrator | `app/engine.py` | 1s |
| 2.7 | `worker_pool.py` — session fayllar ~/.girgitton/ da | `app/worker_pool.py` | 15d |
| 2.8 | `gui.py` — frame switching (o'zgarishsiz) | `app/gui.py` | — |
| 2.9 | `throttle_dialog.py` — o'zgarishsiz | `app/throttle_dialog.py` | — |

### Faza 3: Build va CI/CD (2 soat) — UCHINCHI

| # | Vazifa | Fayl | Vaqt |
|---|--------|------|------|
| 3.1 | `build/girgitton.spec` — deep link protocol handler qo'shish | `build/girgitton.spec` | 30d |
| 3.2 | Windows lokal build + auto-connect test | — | 30d |
| 3.3 | `.github/workflows/build-release.yml` — GitHub Actions | `build-release.yml` | 45d |
| 3.4 | v2.1.0 tag push, 3 platform build test | — | 15d |

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
| `main.py` (faqat bot) | `main.py` (bot + API) | `/pair`, `/groups`, `/download`, `/status` |
| `/setup` (JSON fayl) | `/pair` (6 xonali kod) | Xavfsiz, fayl yaratilmaydi |
| Bitta guruh | Ko'p guruh (parallel) | `/pair` har guruhda → hammaga yuborish |
| `config.py` (JSON file) | `storage.py` (Redis + JSON) | + pair_code, active_groups |
| `companion.py` | `app/` (Desktop App) | Auto-connect + deep link |
| `picker.py` | `app/gui.py` ichida | Native file dialog |
| `uploader.py` (per-chat) | `app/worker_pool.py` (global) | +vaqt mezoni, ~/.girgitton/ sessions |
| `sender.py` | O'zgarishsiz | App ham ishlatadi |
| `helpers.py` | O'zgarishsiz | App ham ishlatadi |
| Yangi | `api.py` (`/auto-pair`, `/pair`, `/groups`), `app/`, `build/`, `.github/` | — |

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
