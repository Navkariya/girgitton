"""
Mini HTTP API — Desktop App ↔ Railway Bot ko'prigi.

Endpoints:
  GET  /health   — Railway health check (auth yo'q)
  POST /connect  — App birinchi ulanish, one-time token validate
  POST /status   — App progress yuboradi (har 5s)
  GET  /task     — App stop/null buyruq tekshiradi

Autentifikatsiya: HMAC-SHA256 (X-Signature header).
API_SECRET bo'sh bo'lsa tekshiruv o'tkazib yuboriladi (lokal test).
"""

import hashlib
import hmac
import json
import logging
import os

from aiohttp import web

import storage

logger = logging.getLogger("girgitton")

# user_id:chat_id → progress dict
_app_states: dict[str, dict] = {}

# user_id:chat_id → "stop" | None
_app_commands: dict[str, str | None] = {}


def _key(user_id: int | str, chat_id: int | str) -> str:
    return f"{user_id}:{chat_id}"


async def _verify_hmac(request: web.Request) -> bool:
    body = await request.read()
    secret = os.getenv("API_SECRET", "").encode()
    if not secret:
        return True  # lokal test uchun
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    received = request.headers.get("X-Signature", "")
    return hmac.compare_digest(expected, received)


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "service": "girgitton"})


async def handle_connect(request: web.Request) -> web.Response:
    if not await _verify_hmac(request):
        return web.json_response({"error": "Unauthorized"}, status=403)
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Bad JSON"}, status=400)

    token = data.get("setup_token", "")
    if not await storage.consume_setup_token(token):
        return web.json_response({"error": "Token yaroqsiz yoki muddati o'tgan"}, status=403)

    logger.info("API /connect: user=%s chat=%s", data.get("user_id"), data.get("chat_id"))
    return web.json_response({"ok": True})


async def handle_status(request: web.Request) -> web.Response:
    if not await _verify_hmac(request):
        return web.json_response({"error": "Unauthorized"}, status=403)
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Bad JSON"}, status=400)

    user_id = data.get("user_id")
    chat_id = data.get("chat_id")
    if user_id is None or chat_id is None:
        return web.json_response({"error": "user_id va chat_id majburiy"}, status=400)

    key = _key(user_id, chat_id)
    _app_states[key] = data
    await storage.save_app_status(int(user_id), int(chat_id), data)
    return web.json_response({"ok": True})


async def handle_task(request: web.Request) -> web.Response:
    if not await _verify_hmac(request):
        return web.json_response({"error": "Unauthorized"}, status=403)

    user_id = request.query.get("user_id")
    chat_id = request.query.get("chat_id")
    if not user_id or not chat_id:
        return web.json_response({"error": "user_id va chat_id majburiy"}, status=400)

    key = _key(user_id, chat_id)
    action = _app_commands.pop(key, None)
    return web.json_response({"action": action})


# ── Bot tomonidan chaqiriladigan funksiyalar ──────────────────────────────

def set_stop_command(user_id: int, chat_id: int) -> None:
    _app_commands[_key(user_id, chat_id)] = "stop"


def get_app_state(user_id: int, chat_id: int) -> dict | None:
    return _app_states.get(_key(user_id, chat_id))


def build_api() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", handle_health)
    app.router.add_post("/connect", handle_connect)
    app.router.add_post("/status", handle_status)
    app.router.add_get("/task", handle_task)
    return app
