"""
Girgitton v2 — Railway Bot + Mini HTTP API

Bot buyruqlari:
  /start     — yordam
  /download  — Desktop App yuklab olish
  /setup     — config fayl + one-time token
  /status    — Desktop App holati
  /stop      — App ga stop signal
  /allow     — foydalanuvchi qo'shish
  /disallow  — foydalanuvchi o'chirish
  /allowed   — ro'yxat

HTTP API (aiohttp):
  GET  /health
  POST /connect
  POST /status
  GET  /task
"""

import asyncio
import json
import logging
import os
import secrets
import sys
from pathlib import Path
from typing import Optional

# Windows konsoli UTF-8 emojilarni ko'rsatishi uchun
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from aiohttp import web
from telethon import TelegramClient, events

import config
import storage
from api import build_api, get_app_state, set_stop_command
from helpers import setup_logging

logger = setup_logging()

# ---------------------------------------------------------------------------
# Telegram client
# ---------------------------------------------------------------------------
client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)


# ---------------------------------------------------------------------------
# Ruxsat yordamchilari
# ---------------------------------------------------------------------------
def _is_owner(sender_id: Optional[int]) -> bool:
    if config.OWNER_ID == 0:
        return True
    return sender_id == config.OWNER_ID


async def _is_allowed(sender_id: Optional[int]) -> bool:
    if _is_owner(sender_id):
        return True
    if sender_id in config.ALLOWED_USERS:
        return True
    return sender_id in await storage.load_allowed_users()


# ---------------------------------------------------------------------------
# Bot buyruqlari
# ---------------------------------------------------------------------------
HELP_TEXT = """
🦎 **Girgitton v2.1** — Desktop Upload App

**Ishlatish tartibi:**
1. `/download` — App ni yuklab oling
2. Guruhda `/pair` yuboring (Guruhni faollashtirish)
3. App ni oching (avtomatik ulanadi yoki kodni kiriting)
4. Yuborishni boshlang

**Buyruqlar:**
• `/start`         — ushbu yordam
• `/download`      — Desktop App yuklab olish
• `/pair`          — Guruhni faollashtirish va ulanish kodi (guruhda)
• `/unpair`        — Guruhni faol ro'yxatdan o'chirish (guruhda)
• `/groups`        — Faol guruhlar ro'yxati
• `/status`        — App holati
• `/stop`          — App ga to'xtatish signali yuborish
• `/allow <ID>`    — foydalanuvchiga ruxsat (faqat egasi)
• `/disallow <ID>` — ruxsatni olib tashlash (faqat egasi)
• `/allowed`       — ruxsatli foydalanuvchilar ro'yxati
""".strip()

GITHUB_REPO = os.getenv("GITHUB_REPO", "Navkariya/girgitton")


@client.on(events.NewMessage(pattern=r"^/start(@\w+)?$"))
async def cmd_start(event: events.NewMessage.Event) -> None:
    await event.reply(HELP_TEXT, parse_mode="md")


@client.on(events.NewMessage(pattern=r"^/download(@\w+)?$"))
async def cmd_download(event: events.NewMessage.Event) -> None:
    base = f"https://github.com/{GITHUB_REPO}/releases/latest/download"
    await event.reply(
        "💻 **Girgitton Desktop App**\n\n"
        "Platformangizni tanlang:\n\n"
        f"🪟 [Windows]({base}/Girgitton_Windows.exe)\n"
        f"🍎 [macOS]({base}/Girgitton_macOS.zip)\n"
        f"🐧 [Linux]({base}/Girgitton_Linux.bin)\n\n"
        "Yuklab olgandan keyin `/setup` buyrug'ini yuboring.",
        parse_mode="md",
    )


def _generate_pair_code() -> str:
    import random
    import string
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


@client.on(events.NewMessage(pattern=r"^/pair(@\w+)?$"))
async def cmd_pair(event: events.NewMessage.Event) -> None:
    if not await _is_allowed(event.sender_id):
        await event.reply("⛔ Ruxsat yo'q.")
        return

    if event.is_private:
        await event.reply("Bu buyruq faqat guruhda ishlaydi!")
        return

    chat = await event.get_chat()
    await storage.add_active_group(event.chat_id, chat.title)

    code = _generate_pair_code()
    await storage.save_pair_code(code, {
        "group_id": event.chat_id,
        "group_title": chat.title,
        "user_id": event.sender_id,
    }, ttl=300)

    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
    server = f"https://{domain}" if domain else "http://localhost:8080"
    deep_link = f"girgitton://connect?code={code}&server={server}"

    await event.reply(
        f"✅ Guruh faollashdi: {chat.title}\n\n"
        f"🔑 Pair Code: **{code}**\n"
        f"⏳ Kod 5 daqiqa amal qiladi.\n\n"
        f"Desktop App oching — lokal avtomatik ulanadi.\n"
        f"Yoki shu linkni bosing: {deep_link}",
        parse_mode="md",
    )


@client.on(events.NewMessage(pattern=r"^/unpair(@\w+)?$"))
async def cmd_unpair(event: events.NewMessage.Event) -> None:
    if not await _is_allowed(event.sender_id):
        await event.reply("⛔ Ruxsat yo'q.")
        return
        
    if event.is_private:
        await event.reply("Bu buyruq faqat guruhda ishlaydi!")
        return
        
    await storage.remove_active_group(event.chat_id)
    await event.reply("❌ Guruh faol ro'yxatdan o'chirildi.")


@client.on(events.NewMessage(pattern=r"^/groups(@\w+)?$"))
async def cmd_groups(event: events.NewMessage.Event) -> None:
    if not await _is_allowed(event.sender_id):
        await event.reply("⛔ Ruxsat yo'q.")
        return
        
    groups = await storage.get_active_groups()
    if not groups:
        await event.reply("ℹ️ Hozircha faol guruhlar yo'q.\nGuruhga botni qo'shib, `/pair` buyrug'ini yuboring.")
        return
        
    lines = [f"• {g['title']} (`{g['id']}`)" for g in groups]
    await event.reply("🎯 **Faol guruhlar:**\n\n" + "\n".join(lines), parse_mode="md")



@client.on(events.NewMessage(pattern=r"^/status(@\w+)?$"))
async def cmd_status(event: events.NewMessage.Event) -> None:
    if not await _is_allowed(event.sender_id):
        await event.reply("⛔ Ruxsat yo'q.")
        return

    state = (
        get_app_state(event.sender_id)
        or await storage.load_app_status(event.sender_id, 0)
    )

    if not state:
        await event.reply(
            "ℹ️ **App holati ma'lum emas**\n\n"
            "App ishlamayapti yoki ulanmagan.\n"
            "App ni ishga tushiring va yuborishni boshlang.",
            parse_mode="md",
        )
        return

    batch = state.get("batch", 0)
    total = state.get("total", 0)
    speed = state.get("speed", 0.0)
    pct = int(batch / total * 100) if total else 0
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)

    await event.reply(
        f"📊 **App holati**\n\n"
        f"`[{bar}]` {pct}%\n"
        f"Qism: {batch}/{total}\n"
        f"Tezlik: {speed:.2f} MB/s",
        parse_mode="md",
    )


@client.on(events.NewMessage(pattern=r"^/stop(@\w+)?$"))
async def cmd_stop(event: events.NewMessage.Event) -> None:
    if not await _is_allowed(event.sender_id):
        await event.reply("⛔ Ruxsat yo'q.")
        return

    set_stop_command(event.sender_id)
    await event.reply(
        "🛑 **Stop signali yuborildi**\n\n"
        "App keyingi tekshiruvda (≤5s) to'xtaydi.\n"
        "Progress saqlangan — `/setup` → app → davom ettirishingiz mumkin.",
        parse_mode="md",
    )


@client.on(events.NewMessage(pattern=r"^/allow(?:@\w+)?\s+(\d+)$"))
async def cmd_allow(event: events.NewMessage.Event) -> None:
    if not _is_owner(event.sender_id):
        await event.reply("⛔ Bu buyruq faqat egasi uchun.")
        return
    user_id = int(event.pattern_match.group(1))
    await storage.add_allowed_user(user_id)
    await event.reply(f"✅ `{user_id}` ruxsatlar ro'yxatiga qo'shildi.", parse_mode="md")


@client.on(events.NewMessage(pattern=r"^/disallow(?:@\w+)?\s+(\d+)$"))
async def cmd_disallow(event: events.NewMessage.Event) -> None:
    if not _is_owner(event.sender_id):
        await event.reply("⛔ Bu buyruq faqat egasi uchun.")
        return
    user_id = int(event.pattern_match.group(1))
    await storage.remove_allowed_user(user_id)
    await event.reply(f"✅ `{user_id}` ruxsatlar ro'yxatidan o'chirildi.", parse_mode="md")


@client.on(events.NewMessage(pattern=r"^/allowed(@\w+)?$"))
async def cmd_allowed_list(event: events.NewMessage.Event) -> None:
    if not _is_owner(event.sender_id):
        await event.reply("⛔ Bu buyruq faqat egasi uchun.")
        return
    env_users = config.ALLOWED_USERS
    dyn_users = await storage.load_allowed_users()
    all_users = env_users | dyn_users
    if not all_users:
        await event.reply("ℹ️ Ruxsatli foydalanuvchilar ro'yxati bo'sh.")
        return
    lines = [
        f"• `{uid}`{' (.env)' if uid in env_users else ''}"
        for uid in sorted(all_users)
    ]
    await event.reply("👥 **Ruxsatli foydalanuvchilar:**\n" + "\n".join(lines), parse_mode="md")


# ---------------------------------------------------------------------------
# Ishga tushirish
# ---------------------------------------------------------------------------
async def main() -> None:
    config.validate()
    await storage.init_storage()

    await client.start(bot_token=config.BOT_TOKEN)
    me = await client.get_me()
    logger.info("Bot: %s (@%s) [%s]", me.first_name, me.username, me.id)

    # HTTP API serverini ishga tushirish
    runner = web.AppRunner(build_api())
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    logger.info("API server ishga tushdi: port=%d", port)

    def _safe_print(msg: str) -> None:
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode("ascii", errors="replace").decode())

    _safe_print(f"\n✅ Girgitton v2 ishga tushdi!")
    _safe_print(f"   Bot    : {me.first_name} (@{me.username})")
    _safe_print(f"   API    : http://0.0.0.0:{port}/health")
    _safe_print(f"   Storage: {'Redis' if os.getenv('REDIS_URL') else 'JSON fayl'}")
    _safe_print("\nTo'xtatish uchun Ctrl+C.\n")

    try:
        await client.run_until_disconnected()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Girgitton to'xtatildi (Ctrl+C).")
        print("\n👋 Girgitton to'xtatildi.")
    except Exception as exc:
        logger.critical("Kritik xatolik: %s", exc, exc_info=True)
        sys.exit(1)
