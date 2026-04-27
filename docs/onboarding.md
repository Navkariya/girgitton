# Onboarding — yangi foydalanuvchi (30 daqiqa)

> Bot Railway'da, App lokal kompyuterda. Quyida 0 dan ishga tushirish.

## 1. Telegram tomonida tayyorgarlik

1. **API ID + API Hash** — https://my.telegram.org/apps
2. **Bot yaratish** — `@BotFather` → `/newbot` → token oling
3. **Owner ID** — `@userinfobot` ga `/start` yuborib ID oling
4. **Maqsadli guruh** — botni guruhga qo'shing va admin qiling (faylar yuborish uchun)

## 2. Lokal repo

```bash
git clone https://github.com/Navkariya/girgitton.git
cd girgitton
python -m venv .venv && source .venv/Scripts/activate
pip install -e ".[app,dev]"
cp .env.example .env
# .env ni tahrirlang
```

`.env` minimum:

```env
API_ID=12345678
API_HASH=...
BOT_TOKEN=...
OWNER_ID=...
API_SECRET=$(python -c "import secrets;print(secrets.token_hex(32))")
```

## 3. Lokal sinov

```bash
# Terminal 1
python -m girgitton.bot
# Terminal 2
python -m girgitton.app
```

Botga Telegram orqali `/start` yuboring. Guruhga `/pair` yuboring → 6 xonali kod oling.
App da "Avtomatik ulanish" ni bosing (yoki kodni qo'lda kiriting).

## 4. Railway deploy

1. https://railway.app — yangi loyiha → "Deploy from GitHub"
2. **Variables**: `API_ID`, `API_HASH`, `BOT_TOKEN`, `OWNER_ID`, `API_SECRET`
3. **Add Redis plugin** — `REDIS_URL` avtomatik
4. Push to `main` → avtomatik deploy

`/health` tekshirish:

```bash
curl https://<your-app>.railway.app/health
```

## 5. Desktop App release

```bash
pip install -e ".[app,build]"
python scripts/build_app.py
# dist/Girgitton.exe (Windows) / Girgitton.app (macOS)
```

## 6. Ishlatish

1. App → Avtomatik ulanish (lokal) yoki pair kod
2. Guruhlar ro'yxatida har biri uchun papka tanlang (drag-drop ham mumkin)
3. ▶️ Boshlash
4. Progress kuzating, `/status` botga yuboring
5. Throttle bo'lsa — dialog ochiladi, kuting yoki to'xtating
