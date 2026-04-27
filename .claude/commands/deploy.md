---
description: Deploy bot to Railway and run smoke tests
---

Deploy the Girgitton bot to Railway:

1. Verify `.env` secrets are set on Railway (BOT_TOKEN, API_ID, API_HASH, OWNER_ID, API_SECRET, REDIS_URL)
2. Push to `main` branch — Railway auto-deploys
3. Wait 30s for Nixpacks build
4. `curl -i https://$RAILWAY_PUBLIC_DOMAIN/health` → expect 200
5. Send `/start` to bot in Telegram → expect help reply
6. Update `bajarildi.txt` deploy entry
