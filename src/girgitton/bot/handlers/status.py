"""/status va /stop handlerlari."""

from __future__ import annotations

from typing import TYPE_CHECKING

from telethon import TelegramClient, events

from girgitton.bot.handlers.decorators import (
    EventT,
    _decorate_chain,
    allowed_only,
    safe_handler,
)
from girgitton.shared.repositories import (
    latest_app_status,
    set_resume_signal,
    set_stop_signal,
)

if TYPE_CHECKING:
    from girgitton.core.config import Settings
    from girgitton.storage.base import StorageRepository


def register_status(client: TelegramClient, settings: Settings, storage: StorageRepository) -> None:
    acl = allowed_only(settings, storage)

    @client.on(events.NewMessage(pattern=r"^/status(@\w+)?$"))
    @_decorate_chain(safe_handler, acl)
    async def cmd_status(event: EventT) -> None:
        st = await latest_app_status(storage, event.sender_id or 0)
        if st is None:
            await event.reply("ℹ️ App holati ma'lum emas. App ishlamayapti yoki ulanmagan.")
            return

        bar_blocks = max(0, min(10, st.progress_pct // 10))
        bar = "█" * bar_blocks + "░" * (10 - bar_blocks)
        await event.reply(
            f"📊 **App holati**\n\n"
            f"`[{bar}]` {st.progress_pct}%\n"
            f"Qism: {st.batch}/{st.total}\n"
            f"Tezlik: {st.speed:.2f} MB/s",
            parse_mode="md",
        )

    @client.on(events.NewMessage(pattern=r"^/stop(@\w+)?$"))
    @_decorate_chain(safe_handler, acl)
    async def cmd_stop(event: EventT) -> None:
        await set_stop_signal(storage, event.sender_id or 0)
        await event.reply(
            "🛑 Stop signali yuborildi.\n"
            "App keyingi tekshiruvda (≤5s) to'xtaydi.\n"
            "Progress saqlanadi — keyin `/resume` bilan davom etish mumkin.",
            parse_mode="md",
        )

    @client.on(events.NewMessage(pattern=r"^/resume(@\w+)?$"))
    @_decorate_chain(safe_handler, acl)
    async def cmd_resume(event: EventT) -> None:
        """Lokal Appga "saqlangan progressdan davom et" signali."""
        await set_resume_signal(storage, event.sender_id or 0)
        await event.reply(
            "⏯ **Resume signali yuborildi.**\n\n"
            "Agar App ishlab tursa — saqlangan progressdan avtomatik davom etadi.\n"
            "Agar App yopiq bo'lsa — uni oching va papkalar tanlanganini tasdiqlang;\n"
            "Boshlash bosilganda dialog **Davom ettirish?** so'raydi.",
            parse_mode="md",
        )
