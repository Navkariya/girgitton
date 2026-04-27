"""HTTP middleware: error handling, HMAC, rate-limit."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from aiohttp import web

from girgitton.core.constants import HTTP_RATE_LIMIT_PER_MINUTE
from girgitton.core.errors import (
    AuthError,
    GirgittonError,
    RateLimitError,
)
from girgitton.shared.repositories import hit_rate_limit

if TYPE_CHECKING:
    from girgitton.shared.crypto import HMACSigner
    from girgitton.storage.base import StorageRepository

logger = logging.getLogger(__name__)

Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


@web.middleware
async def error_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    """Domen xatolarini JSON 4xx/5xx ga aylantiradi."""
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except AuthError as exc:
        return web.json_response({"error": str(exc)}, status=401)
    except RateLimitError as exc:
        return web.json_response({"error": str(exc)}, status=429)
    except GirgittonError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except Exception:
        logger.exception("API ichki xatolik")
        return web.json_response({"error": "Internal error"}, status=500)


def make_hmac_middleware(signer: HMACSigner, *, exempt_paths: tuple[str, ...]) -> web.middleware:
    """HMAC tekshirish middleware'i.

    `exempt_paths` ichidagi path'larga kelgan so'rovlar HMAC dan ozod (masalan,
    `/health`, `/auto-pair`, `/pair`).
    """

    @web.middleware
    async def hmac_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
        if request.path in exempt_paths:
            return await handler(request)

        signature = request.headers.get("X-Signature", "")
        timestamp = request.headers.get("X-Timestamp", "")
        if not signature or not timestamp:
            raise AuthError("X-Signature/X-Timestamp majburiy")

        body = await request.read()
        signer.verify(body, signature, timestamp)
        # Re-set body so handler can read it again
        request["__body"] = body
        return await handler(request)

    return hmac_middleware


def make_rate_limit_middleware(
    storage: StorageRepository,
    *,
    limit: int = HTTP_RATE_LIMIT_PER_MINUTE,
    exempt_paths: tuple[str, ...] = ("/health",),
) -> web.middleware:
    """IP per-minute rate-limit middleware'i."""

    @web.middleware
    async def rate_limit_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
        if request.path in exempt_paths:
            return await handler(request)

        ip = request.remote or "unknown"
        hits = await hit_rate_limit(storage, f"ip:{ip}", window_seconds=60)
        if hits > limit:
            raise RateLimitError(f"Rate limit ({limit}/min) oshib ketdi")
        return await handler(request)

    return rate_limit_middleware
