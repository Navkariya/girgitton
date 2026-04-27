"""Handler dekoratorlari: ACL va kontekst tekshiruvlari."""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import TYPE_CHECKING

from telethon import events

from girgitton.shared.repositories import list_allowed_users

if TYPE_CHECKING:
    from girgitton.core.config import Settings
    from girgitton.storage.base import StorageRepository

logger = logging.getLogger(__name__)

EventT = events.NewMessage.Event
HandlerT = Callable[[EventT], Awaitable[None]]


async def is_allowed(sender_id: int | None, settings: Settings, storage: StorageRepository) -> bool:
    if sender_id is None:
        return False
    if settings.owner_id and sender_id == settings.owner_id:
        return True
    if sender_id in settings.allowed_users:
        return True
    return sender_id in (await list_allowed_users(storage))


def is_owner(sender_id: int | None, settings: Settings) -> bool:
    if sender_id is None:
        return False
    if settings.owner_id == 0:  # owner sozlanmagan — har kim
        return True
    return sender_id == settings.owner_id


def owner_only(
    settings: Settings,
) -> Callable[[HandlerT], HandlerT]:
    """Decorator: faqat OWNER_ID ishlata oladi."""

    def wrap(handler: HandlerT) -> HandlerT:
        @wraps(handler)
        async def inner(event: EventT) -> None:
            if not is_owner(event.sender_id, settings):
                await event.reply("⛔ Bu buyruq faqat egasi uchun.")
                return
            await handler(event)

        return inner

    return wrap


def allowed_only(settings: Settings, storage: StorageRepository) -> Callable[[HandlerT], HandlerT]:
    """Decorator: ACL ga kirgan foydalanuvchilar."""

    def wrap(handler: HandlerT) -> HandlerT:
        @wraps(handler)
        async def inner(event: EventT) -> None:
            if not await is_allowed(event.sender_id, settings, storage):
                await event.reply("⛔ Ruxsat yo'q.")
                return
            await handler(event)

        return inner

    return wrap


def group_only(handler: HandlerT) -> HandlerT:
    @wraps(handler)
    async def inner(event: EventT) -> None:
        if event.is_private:
            await event.reply("⚠️ Bu buyruq faqat guruhda ishlaydi.")
            return
        await handler(event)

    return inner


def safe_handler(handler: HandlerT) -> HandlerT:
    """Har handler ichidagi istisnolarni tutadi va foydalanuvchiga xabar beradi."""

    @wraps(handler)
    async def inner(event: EventT) -> None:
        try:
            await handler(event)
        except Exception as exc:
            logger.exception("Handler xatoligi: %s", handler.__name__)
            with contextlib.suppress(Exception):
                await event.reply(f"⚠️ Ichki xatolik: {type(exc).__name__}")

    return inner


def _decorate_chain(
    *decorators: Callable[[HandlerT], HandlerT],
) -> Callable[[HandlerT], HandlerT]:
    """Bir necha dekoratorlarni ketma-ket qo'llovchi yagona dekorator qaytaradi.

    Tartib: birinchi dekorator eng tashqi (masalan, `safe_handler`),
    oxirgisi handlerga eng yaqin.
    """

    def apply(handler: HandlerT) -> HandlerT:
        out = handler
        for d in reversed(decorators):
            out = d(out)
        return out

    return apply


__all__ = [
    "EventT",
    "HandlerT",
    "_decorate_chain",
    "allowed_only",
    "group_only",
    "is_allowed",
    "is_owner",
    "owner_only",
    "safe_handler",
]
