"""Telethon bot client factory."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telethon import TelegramClient

if TYPE_CHECKING:
    from pathlib import Path

    from girgitton.core.config import Settings

logger = logging.getLogger(__name__)


def build_bot_client(settings: Settings, *, session_dir: Path | None = None) -> TelegramClient:
    """Bot rejimida ishlovchi Telethon client yaratadi.

    Sessiya fayli `session_dir/session_name.session` da saqlanadi (default —
    joriy katalog).
    """
    if session_dir is not None:
        session_dir.mkdir(parents=True, exist_ok=True)
        session_path = str(session_dir / settings.session_name)
    else:
        session_path = settings.session_name

    return TelegramClient(
        session_path,
        api_id=settings.api_id,
        api_hash=settings.api_hash.get(),
    )


async def start_bot_client(client: TelegramClient, settings: Settings) -> None:
    """Bot tokeni bilan ulanishni boshlaydi."""
    await client.start(bot_token=settings.bot_token.get())
    me = await client.get_me()
    logger.info("Bot ulandi: @%s id=%s", me.username, me.id)
