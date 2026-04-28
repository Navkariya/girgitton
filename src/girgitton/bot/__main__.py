"""Bot kirish nuqtasi: `python -m girgitton.bot`.

Telethon bot va aiohttp API serverini bir asyncio loopda birga ishga tushiradi.
SIGTERM/SIGINT da graceful shutdown.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from contextlib import suppress

from girgitton.bot.api.server import build_app, start_http_server
from girgitton.bot.client import build_bot_client, start_bot_client
from girgitton.bot.handlers import (
    register_access,
    register_enrollment,
    register_help,
    register_status,
)
from girgitton.core.config import Settings
from girgitton.core.logging_setup import setup_logging
from girgitton.storage.factory import build_storage

logger = logging.getLogger(__name__)


async def _run() -> None:
    settings = Settings.load()
    settings.validate()

    from girgitton.core import app_paths

    setup_logging(
        level=settings.log_level,
        json=settings.log_json,
        log_dir=app_paths.get_logs_dir(),
    )
    logger.info("Bot ishga tushmoqda: %s", settings.to_safe_dict())

    storage = await build_storage(settings)

    client = build_bot_client(settings)
    register_help(client)
    register_enrollment(client, settings, storage)
    register_status(client, settings, storage)
    register_access(client, settings, storage)

    await start_bot_client(client, settings)

    app = build_app(settings, storage)
    runner = await start_http_server(app, port=settings.http_port)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            with suppress(NotImplementedError):
                loop.add_signal_handler(sig, stop_event.set)

    try:
        # Telethon disconnect yoki SIGTERM
        bot_task = asyncio.create_task(client.run_until_disconnected())
        stop_task = asyncio.create_task(stop_event.wait())
        _done, pending = await asyncio.wait(
            {bot_task, stop_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for t in pending:
            t.cancel()
            with suppress(asyncio.CancelledError):
                await t
    finally:
        logger.info("Bot to'xtatilmoqda...")
        await runner.cleanup()
        with suppress(Exception):
            await client.disconnect()
        await storage.close()


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Ctrl+C")


if __name__ == "__main__":
    main()
