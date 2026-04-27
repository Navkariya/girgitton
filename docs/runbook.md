# Runbook — Operatsion ssenariylar

## Deploy

```bash
git push origin main           # Railway auto-deploy (Nixpacks)
curl https://$DOMAIN/health    # 200 kutiladi
```

Rollback:

```bash
railway logout && railway login
railway environment use production
railway service ls
railway service rollback <deployment_id>
```

## Bot xato beradi

1. Logni ko'ring: `railway logs --service bot`
2. Tipik sabablar:
   - `BOT_TOKEN` noto'g'ri → `@BotFather /token`
   - `API_ID`/`API_HASH` noto'g'ri → my.telegram.org
   - `REDIS_URL` ulanmaydi → JSON fallback ishlaydi (warning)
3. Restart: `railway service restart bot`

## App qora ekran / hang

1. `~/.girgitton/desktop_app.log` ni ko'ring
2. Eski sessiya buzilgan: `~/.girgitton/sessions/` ni o'chiring
3. Credentials: `~/.girgitton/credentials.enc` ni o'chiring → qaytadan pair

## Throttle 30+ daqiqa

- App avtomatik kutadi
- `BAJARILGAN/JAMI` foiz saqlanadi
- App'ni yopib qayta ochsangiz ham progress saqlangan

## Pair code yaroqsiz

- TTL 5 daqiqa
- Yangi `/pair` yuboring (eski avtomatik o'chiriladi)

## Redis o'chgan

JSON fallback `~/.girgitton/state.json` ga avtomatik o'tadi (warning). Redis qaytgach, qayta deploy qiling — yangi kalit nomlari qoladi (eski JSON o'qilmaydi).

## Foydalanuvchi qo'shish

```text
/allow 123456789
/disallow 123456789
/allowed
```

## Mahalliy bot+app dev cycle

```bash
# 1) tezkor verify
ruff check src/ tests/
mypy src/girgitton
pytest -q

# 2) Bot
python -m girgitton.bot

# 3) App
python -m girgitton.app
```

## Incident: bot tokeni oqib ketdi

1. `@BotFather` → `/revoke` → tanglang
2. Yangi token Railway Variables ga
3. `railway service restart bot`
4. Eski `*.session` ni o'chiring
