# Railway Deploy — Bot

> Bu hujjat Railway'da Girgitton botni 5 daqiqada ishga tushirish uchun.
> Desktop App lokalda ishlaydi, lekin **bot Railway'da turishi tavsiya etiladi** (24/7 uptime).

## 1. Talab qilinadigan sirlar

@BotFather va https://my.telegram.org/apps dan oling:

| Variable          | Kerak | Tavsif                                                  |
| ----------------- | ----- | ------------------------------------------------------- |
| `API_ID`          | ✅     | Telegram API ID (raqam)                                 |
| `API_HASH`        | ✅     | Telegram API Hash (32 hex)                              |
| `BOT_TOKEN`       | ✅     | @BotFather dan bot tokeni                               |
| `BOT_USERNAME`    | ✅     | Bot username (`@` siz, mas. `girgitton_media_bot`)      |
| `OWNER_ID`        | ✅     | Telegram ID (@userinfobot dan)                          |
| `API_SECRET`      | ✅     | HMAC kalit — `secrets.token_hex(32)` orqali yarating    |
| `ALLOWED_USERS`   | ⭕     | Vergulli ID ro'yxat (qo'shimcha ruxsat)                 |
| `REDIS_URL`       | ⭕     | Railway Redis plugin (auto-injected)                    |
| `LOG_JSON`        | ⭕     | `true` (Railway oqimi uchun)                            |
| `LOG_LEVEL`       | ⭕     | `INFO` (default)                                        |
| `GITHUB_REPO`     | ⭕     | `Navkariya/girgitton` (`/download` linklari uchun)      |

> ⚠️ `PORT` Railway tomonidan **avtomatik** beriladi — qo'lda kiritmang.

## 2. Deploy qadamlari

### 2.1 Railway loyiha yaratish

```
1. https://railway.app -> Login (GitHub)
2. New Project -> Deploy from GitHub Repo
3. Tanlang: Navkariya/girgitton
4. Railway avtomatik aniqlaydi: Nixpacks builder + `python -m girgitton.bot`
```

### 2.2 Variables o'rnatish

Railway dashboard → Variables → "Raw Editor" tab → quyidagini joylab `Update Variables`:

```env
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=1234567890:ABCdef
BOT_USERNAME=girgitton_media_bot
OWNER_ID=123456789
API_SECRET=64_char_hex_secret
LOG_JSON=true
GITHUB_REPO=Navkariya/girgitton
```

### 2.3 Redis plugin (tavsiya etiladi)

```
Railway dashboard -> + New -> Database -> Redis
```

`REDIS_URL` avtomatik bot service'ga inject bo'ladi. Bu **persistent storage** beradi — bot restart bo'lsa ham state saqlanadi.

> Redis bo'lmasa: JSON fayl fallback (`~/.girgitton/state.json`) — Railway ephemeral disk'da, restart'da yo'qoladi.

### 2.4 Deploy

`main` branch'ga push → avtomatik deploy:

```bash
git push origin main
```

Build ~2-3 daqiqa, keyin `https://<your-app>.railway.app/health` 200 OK qaytaradi.

### 2.5 Verify

```bash
curl https://<your-app>.railway.app/health
# {"ok": true, "service": "girgitton", "version": "3.2.0"}
```

Telegram'da botga `/start` yuboring → welcome matni keladi.

## 3. Domen

Railway avtomatik domen beradi (`*.railway.app`). Custom domen uchun:

```
Railway -> Settings -> Networking -> Custom Domain
```

`RAILWAY_PUBLIC_DOMAIN` avtomatik set'lanadi (env var).

## 4. Logs

```
Railway dashboard -> Deployments -> View Logs
```

JSON formatdagi loglar (LOG_JSON=true) — `level`, `ts`, `name`, `message` maydonlari bilan.

## 5. Troubleshooting

| Muammo                         | Yechim                                                         |
| ------------------------------ | -------------------------------------------------------------- |
| Build fail (PyInstaller error) | Bizga app extras kerak emas — nixpacks.toml `pip install .` to'g'ri |
| `BOT_TOKEN unauthorized`       | Token noto'g'ri — qaytadan @BotFather'dan oling                |
| `/health` 503                  | Bot start bo'lmadi — Logs tekshiring (API_ID/HASH muammosi)    |
| `POST /status` 401             | App'dagi `api_secret` Railway'dagi `API_SECRET` ga teng emas    |
| Bot Telegram'da javob bermaydi | BotFather webhook qo'yilgan — `/deleteWebhook` API orqali tozalash |

## 6. Disaster Recovery

| Hodisa            | Tiklash                                                    |
| ----------------- | ---------------------------------------------------------- |
| Bot crash         | Railway auto-restart (max 5 retry)                         |
| Redis o'chgan     | JSON fallback ishlaydi (warning log)                       |
| Variables o'chsa  | Railway dashboard'dan qayta kiriting                       |
| Yomon deploy      | Deployments tab → eski deploy → Promote                    |
