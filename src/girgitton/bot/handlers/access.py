"""/allow, /disallow, /allowed handlerlari (faqat owner)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from telethon import TelegramClient, events

from girgitton.bot.handlers.decorators import (
    EventT,
    _decorate_chain,
    owner_only,
    safe_handler,
)
from girgitton.shared.repositories import (
    add_allowed_user,
    list_allowed_users,
    remove_allowed_user,
)

if TYPE_CHECKING:
    from girgitton.core.config import Settings
    from girgitton.storage.base import StorageRepository


def register_access(client: TelegramClient, settings: Settings, storage: StorageRepository) -> None:
    only_owner = owner_only(settings)

    @client.on(events.NewMessage(pattern=r"^/allow(?:@\w+)?\s+(-?\d+)$"))
    @_decorate_chain(safe_handler, only_owner)
    async def cmd_allow(event: EventT) -> None:
        user_id = int(event.pattern_match.group(1))
        await add_allowed_user(storage, user_id)
        await event.reply(f"✅ `{user_id}` ruxsatlar ro'yxatiga qo'shildi.", parse_mode="md")

    @client.on(events.NewMessage(pattern=r"^/disallow(?:@\w+)?\s+(-?\d+)$"))
    @_decorate_chain(safe_handler, only_owner)
    async def cmd_disallow(event: EventT) -> None:
        user_id = int(event.pattern_match.group(1))
        await remove_allowed_user(storage, user_id)
        await event.reply(f"✅ `{user_id}` ro'yxatdan o'chirildi.", parse_mode="md")

    @client.on(events.NewMessage(pattern=r"^/allowed(@\w+)?$"))
    @_decorate_chain(safe_handler, only_owner)
    async def cmd_allowed(event: EventT) -> None:
        env_users = settings.allowed_users
        dyn_users = await list_allowed_users(storage)
        all_users = env_users | dyn_users
        if not all_users:
            await event.reply("ℹ️ Ruxsatlar ro'yxati bo'sh.")
            return
        lines = "\n".join(
            f"• `{uid}`{' (.env)' if uid in env_users else ''}" for uid in sorted(all_users)
        )
        await event.reply("👥 **Ruxsatli foydalanuvchilar:**\n" + lines, parse_mode="md")
