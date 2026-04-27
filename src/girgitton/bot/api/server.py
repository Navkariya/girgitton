"""aiohttp Application factory."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiohttp import web

from girgitton.bot.api.middleware import (
    error_middleware,
    make_hmac_middleware,
    make_rate_limit_middleware,
)
from girgitton.bot.api.routes import make_routes
from girgitton.shared.crypto import HMACSigner

if TYPE_CHECKING:
    from girgitton.core.config import Settings
    from girgitton.storage.base import StorageRepository

logger = logging.getLogger(__name__)

# HMAC dan ozod yo'llar — connect tokeni o'zi maxfiy kalit vazifasini bajaradi
_EXEMPT_PATHS = ("/health", "/connect-init", "/connect-status", "/connect-claim")


def build_app(settings: Settings, storage: StorageRepository) -> web.Application:
    """Sozlangan aiohttp Application qaytaradi."""
    signer = HMACSigner(settings.api_secret.get())

    app = web.Application(
        middlewares=[
            error_middleware,
            make_rate_limit_middleware(storage),
            make_hmac_middleware(signer, exempt_paths=_EXEMPT_PATHS),
        ]
    )
    app.add_routes(make_routes(settings, storage))
    return app


async def start_http_server(
    app: web.Application, port: int, host: str = "0.0.0.0"
) -> web.AppRunner:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info("HTTP API ishga tushdi: http://%s:%d", host, port)
    return runner
