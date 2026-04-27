"""App ↔ Bot token-based connect oqimi (v3.1).

Senariy:
  1. App: token = secrets.token_hex(8)
  2. App: POST /connect-init {token}  → {t_me_url}
  3. App: webbrowser.open(t_me_url)
  4. User: Telegram'da START tugmasini bosadi
  5. Bot: /start <token> → bind_connect_token(token, user_id)
  6. App: GET /connect-status?token=… har 1.5s
  7. Tayyor bo'lsa: POST /connect-claim {token} → {credentials, user_id, groups}
  8. App: Fernet bilan saqlaydi
"""

from __future__ import annotations

import asyncio
import logging
import secrets
import webbrowser
from collections.abc import Callable
from typing import Any

import aiohttp

from girgitton.core.constants import HTTP_REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 1.5
MAX_POLL_DURATION_SECONDS = 300


def generate_connect_token() -> str:
    return secrets.token_hex(8)


async def init_connect(server_url: str, token: str) -> dict[str, Any]:
    """`POST /connect-init` — t_me_url qaytaradi."""
    url = f"{server_url.rstrip('/')}/connect-init"
    timeout = aiohttp.ClientTimeout(total=HTTP_REQUEST_TIMEOUT_SECONDS)
    try:
        async with (
            aiohttp.ClientSession(timeout=timeout) as sess,
            sess.post(url, json={"token": token}) as resp,
        ):
            return await resp.json()
    except Exception as exc:
        return {"error": f"connect-init: {exc}"}


async def poll_connect_status(server_url: str, token: str) -> dict[str, Any] | None:
    """`GET /connect-status?token=…`. None — 404 (token yo'q)."""
    url = f"{server_url.rstrip('/')}/connect-status?token={token}"
    timeout = aiohttp.ClientTimeout(total=HTTP_REQUEST_TIMEOUT_SECONDS)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as sess, sess.get(url) as resp:
            if resp.status == 404:
                return None
            return await resp.json()
    except Exception as exc:
        logger.debug("poll error: %s", exc)
        return {"ready": False}


async def claim_connect(server_url: str, token: str) -> dict[str, Any]:
    """`POST /connect-claim {token}` → credentials + user_id."""
    url = f"{server_url.rstrip('/')}/connect-claim"
    timeout = aiohttp.ClientTimeout(total=HTTP_REQUEST_TIMEOUT_SECONDS)
    try:
        async with (
            aiohttp.ClientSession(timeout=timeout) as sess,
            sess.post(url, json={"token": token}) as resp,
        ):
            return await resp.json()
    except Exception as exc:
        return {"error": f"claim: {exc}"}


CancelFn = Callable[[], bool]
StatusUpdateFn = Callable[[str], None]


async def run_connect_flow(
    server_url: str,
    *,
    on_url_ready: Callable[[str], None],
    on_status: StatusUpdateFn | None = None,
    is_cancelled: CancelFn | None = None,
) -> dict[str, Any]:
    """To'liq oqim: token → init → open URL → poll → claim.

    Returns:
        Muvaffaqiyat: `{ok: true, user_id, credentials, groups, api_secret, api_url}`
        Xato: `{error: "..."}`
    """
    token = generate_connect_token()

    init = await init_connect(server_url, token)
    if not init.get("ok"):
        return {"error": init.get("error", "connect-init muvaffaqiyatsiz")}

    t_me_url: str = init["t_me_url"]
    on_url_ready(t_me_url)
    try:
        webbrowser.open(t_me_url)
    except Exception:
        logger.debug("webbrowser.open ishlamadi (manual link kerak)")

    elapsed = 0.0
    while elapsed < MAX_POLL_DURATION_SECONDS:
        if is_cancelled is not None and is_cancelled():
            return {"error": "Foydalanuvchi tomonidan bekor qilindi"}

        status = await poll_connect_status(server_url, token)
        if status is None:
            return {"error": "Token muddati o'tdi yoki yo'q"}
        if status.get("ready"):
            user_id = int(status["user_id"])
            if on_status:
                on_status(f"✅ Foydalanuvchi {user_id} aniqlandi, ulanmoqda…")
            claim = await claim_connect(server_url, token)
            if not claim.get("ok"):
                return {"error": claim.get("error", "claim muvaffaqiyatsiz")}
            claim["api_url"] = server_url
            return claim

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        elapsed += POLL_INTERVAL_SECONDS

    return {"error": "Vaqt tugadi (5 daqiqa)"}
