"""
Mini HTTP API — Desktop App ↔ Railway Bot ko'prigi.

Endpoints:
  GET  /health     — Railway health check (auth yo'q)
  GET  /auto-pair  — Lokal avtomatik ulanish (faqat localhost)
  POST /pair       — Pair code validate va credentials qaytarish
  GET  /groups     — Faol guruhlar ro'yxati
  POST /status     — App progress yuboradi (har 5s)
  GET  /task       — App stop/null buyruq tekshiradi

Autentifikatsiya: HMAC-SHA256 (X-Signature header).
"""

import hashlib
import hmac
import json
import logging
import os

from aiohttp import web

import config
import storage

logger = logging.getLogger("girgitton")

# user_id → progress dict
_app_states: dict[str, dict] = {}

# user_id → "stop" | None
_app_commands: dict[str, str | None] = {}


def _key(user_id: int | str) -> str:
    return str(user_id)


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


async def handle_auto_pair(request: web.Request) -> web.Response:
    peer = request.remote
    if peer not in ("127.0.0.1", "::1", "localhost"):
        return web.json_response({"error": "Faqat lokal"}, status=403)
    
    groups = await storage.get_active_groups()
    return web.json_response({
        "ok": True,
        "credentials": {
            "api_id": config.API_ID,
            "api_hash": config.API_HASH,
            "bot_token": config.BOT_TOKEN,
        },
        "groups": groups,
        "api_secret": os.getenv("API_SECRET", ""),
    })


async def handle_pair(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Bad JSON"}, status=400)
        
    code = data.get("code", "").strip().upper()
    pair_data = await storage.consume_pair_code(code)
    if not pair_data:
        return web.json_response({"error": "Kod yaroqsiz yoki muddati o'tgan"}, status=403)
        
    return web.json_response({
        "ok": True,
        "credentials": {
            "api_id": config.API_ID,
            "api_hash": config.API_HASH,
            "bot_token": config.BOT_TOKEN,
        },
        "group": {
            "id": pair_data["group_id"],
            "title": pair_data["group_title"],
        },
        "api_secret": os.getenv("API_SECRET", ""),
    })


async def handle_groups(request: web.Request) -> web.Response:
    if not await _verify_hmac(request):
        return web.json_response({"error": "Unauthorized"}, status=403)
        
    groups = await storage.get_active_groups()
    return web.json_response({"ok": True, "groups": groups})


async def handle_status(request: web.Request) -> web.Response:
    if not await _verify_hmac(request):
        return web.json_response({"error": "Unauthorized"}, status=403)
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Bad JSON"}, status=400)

    user_id = data.get("user_id")
    if user_id is None:
        return web.json_response({"error": "user_id majburiy"}, status=400)

    key = _key(user_id)
    _app_states[key] = data
    # Har bir guruh uchun ham saqlashimiz mumkin (compatibility uchun)
    if "chat_id" in data:
        await storage.save_app_status(int(user_id), int(data["chat_id"]), data)
    else:
        # Eski holatni saqlab qolish
        await storage.save_app_status(int(user_id), 0, data)
        
    return web.json_response({"ok": True})


async def handle_task(request: web.Request) -> web.Response:
    if not await _verify_hmac(request):
        return web.json_response({"error": "Unauthorized"}, status=403)

    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"error": "user_id majburiy"}, status=400)

    key = _key(user_id)
    action = _app_commands.pop(key, None)
    return web.json_response({"action": action})


# ── Bot tomonidan chaqiriladigan funksiyalar ──────────────────────────────

def set_stop_command(user_id: int) -> None:
    _app_commands[_key(user_id)] = "stop"


def get_app_state(user_id: int) -> dict | None:
    return _app_states.get(_key(user_id))


def build_api() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", handle_health)
    app.router.add_get("/auto-pair", handle_auto_pair)
    app.router.add_post("/pair", handle_pair)
    app.router.add_get("/groups", handle_groups)
    app.router.add_post("/status", handle_status)
    app.router.add_get("/task", handle_task)
    return app
