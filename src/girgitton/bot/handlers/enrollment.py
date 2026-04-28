"""Enrollment, /here, /unhere, /groups handlerlari + ChatAction listener.

`v3.1` (multi-tenant):
- `/start [token]` — App ulanishi (token bo'lsa) yoki oddiy welcome
- `/here` — guruhni shu user'ning aktiv ro'yxatiga qo'shadi (per-owner)
- `/unhere` — olib tashlash
- `/groups` — shu user'ning ro'yxati
- ChatAction listener — bot guruhga qo'shilsa/o'chirilsa avtomatik tozalash
"""

from __future__ import annotations

import logging

from telethon import TelegramClient, events

from girgitton import __version__ as _VERSION
from girgitton.bot.handlers.decorators import (
    EventT,
    _decorate_chain,
    allowed_only,
    group_only,
    safe_handler,
)
from girgitton.core.config import Settings
from girgitton.core.models import ActiveGroup
from girgitton.shared.repositories import (
    add_active_group,
    bind_connect_token,
    enroll_user,
    list_active_groups,
    remove_active_group,
    remove_group_from_all_owners,
)
from girgitton.storage.base import StorageRepository

logger = logging.getLogger(__name__)


WELCOME_TEXT = f"""
🐈 **Girgitton v{_VERSION}** — Telegram media auto-sender

Salom! Botdan foydalanish:

1. `/download` — Desktop App ni yuklab oling (Win/Mac/Linux)
2. App ni oching — Telegramda START tugmasini bosing → avtomatik ulanadi
3. Guruhga botni qo'shing va admin qiling
4. Guruhda `/here` yuboring — shu guruh sizning App ro'yxatingizga qo'shiladi
5. App'da papka tanlang va ▶️ Boshlash

**Buyruqlar:**
• `/start`              — ushbu yordam
• `/download`           — Desktop App yuklab olish
• `/here` (guruhda)     — guruhni faol ro'yxatga qo'shish
• `/unhere` (guruhda)   — olib tashlash
• `/groups`             — sizning guruhlar ro'yxati
• `/status`             — yuklash holati
• `/stop`               — yuklashni to'xtatish (progress saqlanadi)
• `/resume`             — saqlangan joydan davom ettirish
""".strip()


def register_enrollment(
    client: TelegramClient, settings: Settings, storage: StorageRepository
) -> None:
    """`/start [token]` handler — App ulanish oqimi va welcome."""
    acl = allowed_only(settings, storage)

    @client.on(events.NewMessage(pattern=r"^/start(?:@\w+)?(?:\s+([a-zA-Z0-9]+))?$"))
    @safe_handler
    async def cmd_start(event: EventT) -> None:
        sender_id = event.sender_id
        if sender_id is None:
            return

        # Foydalanuvchini ro'yxatga olamiz (idempotent)
        await enroll_user(storage, sender_id)

        # /start <token> — App connect oqimi
        token = event.pattern_match.group(1)
        if token:
            ok = await bind_connect_token(storage, token, sender_id)
            if ok:
                await event.reply(
                    "✅ **App muvaffaqiyatli ulandi!**\n\n"
                    "Endi App ga qayting va papka tanlab boshlang.\n\n"
                    "Guruhga botni qo'shib `/here` yuboring — shu guruh App ro'yxatingizga "
                    "qo'shiladi.",
                    parse_mode="md",
                )
                logger.info("Connect token bound: user=%s", sender_id)
                return
            await event.reply(
                "⚠️ Token yaroqsiz yoki muddati o'tgan.\nApp'da yangi ulanish urinishini bosing."
            )
            return

        # Oddiy /start
        await event.reply(WELCOME_TEXT, parse_mode="md")

    @client.on(events.NewMessage(pattern=r"^/here(@\w+)?$"))
    @_decorate_chain(safe_handler, acl, group_only)
    async def cmd_here(event: EventT) -> None:
        sender_id = event.sender_id
        if sender_id is None:
            return

        chat = await event.get_chat()
        title = getattr(chat, "title", f"chat:{event.chat_id}")
        await add_active_group(storage, sender_id, ActiveGroup(event.chat_id, title))
        await event.reply(
            f"✅ **{title}** sizning ro'yxatingizga qo'shildi.\n\n"
            f"App `📂 {title}` qatorida papka tanlasangiz, shu guruhga yuboriladi.",
            parse_mode="md",
        )
        logger.info("Group %s added for owner %s", event.chat_id, sender_id)

    @client.on(events.NewMessage(pattern=r"^/unhere(@\w+)?$"))
    @_decorate_chain(safe_handler, acl, group_only)
    async def cmd_unhere(event: EventT) -> None:
        sender_id = event.sender_id
        if sender_id is None:
            return
        await remove_active_group(storage, sender_id, event.chat_id)
        await event.reply("❌ Bu guruh sizning ro'yxatingizdan o'chirildi.")

    @client.on(events.NewMessage(pattern=r"^/groups(@\w+)?$"))
    @_decorate_chain(safe_handler, acl)
    async def cmd_groups(event: EventT) -> None:
        sender_id = event.sender_id
        if sender_id is None:
            return
        groups = await list_active_groups(storage, sender_id)
        if not groups:
            await event.reply(
                "ℹ️ Sizda faol guruhlar yo'q.\nBotni guruhga qo'shib `/here` yuboring."
            )
            return
        lines = "\n".join(f"• **{g.title}** `{g.id}`" for g in groups)
        await event.reply(f"🎯 **Sizning guruhlaringiz:**\n\n{lines}", parse_mode="md")

    @client.on(events.ChatAction)
    @safe_handler
    async def chat_action_listener(event: EventT) -> None:
        """Bot guruhdan o'chirilsa, barcha owner'lar uchun tozalaymiz."""
        # event.user_kicked / user_left bizga ham tegishli (bot)
        try:
            me = await client.get_me()
            bot_id = me.id
        except Exception:
            return

        action = event.action_message
        if action is None:
            return

        # Bot kicked/left bo'lganida
        was_removed = getattr(event, "user_kicked", False) or getattr(event, "user_left", False)
        if not was_removed:
            return

        affected_users: list[int] = []
        try:
            users = event.users or []
            for u in users:
                if getattr(u, "id", None) == bot_id:
                    affected_users.append(bot_id)
        except Exception:
            return

        if bot_id in affected_users:
            await remove_group_from_all_owners(storage, event.chat_id)
            logger.info(
                "Bot guruhdan chiqarildi: %s — barcha owner'lardan tozalandi",
                event.chat_id,
            )
