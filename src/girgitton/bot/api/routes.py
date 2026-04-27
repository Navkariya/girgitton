"""HTTP API endpointlari (v3.1 multi-tenant)."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from aiohttp import web

from girgitton.bot.api.schemas import (
    ConnectClaimRequest,
    ConnectInitRequest,
    SchemaError,
    StatusRequest,
)
from girgitton.core.models import AppStatus
from girgitton.shared.repositories import (
    consume_connect_token,
    consume_resume_signal,
    consume_stop_signal,
    get_connect_token,
    init_connect_token,
    list_active_groups,
    save_app_status,
)

if TYPE_CHECKING:
    from girgitton.core.config import Settings
    from girgitton.storage.base import StorageRepository

logger = logging.getLogger(__name__)


def _credentials_dict(settings: Settings) -> dict[str, object]:
    """Desktop appga uzatiladigan credentials."""
    return {
        "api_id": settings.api_id,
        "api_hash": settings.api_hash.get(),
        "bot_token": settings.bot_token.get(),
    }


def _bot_username_or_id(settings: Settings, override: str | None = None) -> str:
    """`.env`dagi BOT_USERNAME yoki bot tokenining boshlanishi (lokal uchun)."""
    if override:
        return override
    import os as _os

    env_user = _os.getenv("BOT_USERNAME", "").strip().lstrip("@")
    if env_user:
        return env_user
    token = settings.bot_token.get()
    return token.split(":", 1)[0] if ":" in token else "bot"


def make_routes(settings: Settings, storage: StorageRepository) -> web.RouteTableDef:
    routes = web.RouteTableDef()
    bot_handle = _bot_username_or_id(settings)

    @routes.get("/health")
    async def health(_: web.Request) -> web.Response:
        return web.json_response({"ok": True, "service": "girgitton", "version": "3.1.0"})

    # ─── Connect oqimi (token-based) ────────────────────────────────────────

    @routes.post("/connect-init")
    async def connect_init(request: web.Request) -> web.Response:
        """App connect tokenini ro'yxatga oladi.

        Auth: yo'q (token o'zi maxfiy va TTL).
        """
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"error": "Yaroqsiz JSON"}, status=400)

        try:
            req = ConnectInitRequest.parse(payload)
        except SchemaError as exc:
            return web.json_response({"error": str(exc)}, status=400)

        await init_connect_token(storage, req.token)
        return web.json_response(
            {
                "ok": True,
                "t_me_url": f"https://t.me/{bot_handle}?start={req.token}",
            }
        )

    @routes.get("/connect-status")
    async def connect_status(request: web.Request) -> web.Response:
        """Token holatini polling (App har 1.5s).

        Response:
          - {"ready": false} — hali biriktirilmagan
          - {"ready": true, "user_id": 123} — biriktirildi (claim qilish mumkin)
          - 404 — token yo'q yoki muddati o'tgan
        """
        token = request.query.get("token", "").strip()
        if not token:
            return web.json_response({"error": "token majburiy"}, status=400)

        raw = await storage.get(f"connect_token:{token}")
        if raw is None:
            return web.json_response({"error": "token yo'q yoki muddat tugagan"}, status=404)

        user_id = await get_connect_token(storage, token)
        if user_id is None:
            return web.json_response({"ready": False})
        return web.json_response({"ready": True, "user_id": user_id})

    @routes.post("/connect-claim")
    async def connect_claim(request: web.Request) -> web.Response:
        """Tokenni claim qilib (atomik o'chiriladi) credentialsni qaytaradi.

        Auth: token o'zi (one-time secret).
        """
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"error": "Yaroqsiz JSON"}, status=400)

        try:
            req = ConnectClaimRequest.parse(payload)
        except SchemaError as exc:
            return web.json_response({"error": str(exc)}, status=400)

        user_id = await consume_connect_token(storage, req.token)
        if user_id is None:
            return web.json_response(
                {"error": "Token hali biriktirilmagan yoki muddat tugagan"}, status=403
            )

        groups = [g.to_dict() for g in await list_active_groups(storage, user_id)]
        return web.json_response(
            {
                "ok": True,
                "user_id": user_id,
                "credentials": _credentials_dict(settings),
                "groups": groups,
                "api_secret": settings.api_secret.get(),
            }
        )

    # ─── Per-owner guruhlar (HMAC) ──────────────────────────────────────────

    @routes.get("/groups")
    async def groups(request: web.Request) -> web.Response:
        """`?user_id=<>` orqali shu user'ning guruhlarini qaytaradi (HMAC)."""
        user_id_raw = request.query.get("user_id", "")
        if not user_id_raw.lstrip("-").isdigit():
            return web.json_response({"error": "user_id majburiy"}, status=400)
        user_id = int(user_id_raw)

        groups_list = [g.to_dict() for g in await list_active_groups(storage, user_id)]
        return web.json_response({"ok": True, "groups": groups_list})

    # ─── App ↔ Bot status va task (HMAC) ────────────────────────────────────

    @routes.post("/status")
    async def status(request: web.Request) -> web.Response:
        body = request.get("__body") or await request.read()
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return web.json_response({"error": "Yaroqsiz JSON"}, status=400)

        try:
            req = StatusRequest.parse(payload)
        except SchemaError as exc:
            return web.json_response({"error": str(exc)}, status=400)

        await save_app_status(
            storage,
            AppStatus(
                user_id=req.user_id,
                chat_id=req.chat_id,
                batch=req.batch,
                total=req.total,
                speed=req.speed,
            ),
        )
        return web.json_response({"ok": True})

    @routes.get("/task")
    async def task(request: web.Request) -> web.Response:
        user_id_raw = request.query.get("user_id", "")
        if not user_id_raw.isdigit():
            return web.json_response({"error": "user_id majburiy"}, status=400)
        user_id = int(user_id_raw)

        # Stop yuqori prioritet (agar ikkala signal ham bor bo'lsa)
        if await consume_stop_signal(storage, user_id):
            return web.json_response({"action": "stop"})
        if await consume_resume_signal(storage, user_id):
            return web.json_response({"action": "resume"})
        return web.json_response({"action": None})

    return routes
