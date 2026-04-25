"""
Railway Mini API bilan HMAC-signed HTTP aloqa.

Har 5 soniyada:
  - POST /status — GUI progress ma'lumotlarini yuboradi
  - GET  /task   — stop buyrug'ini tekshiradi
"""

import asyncio
import hashlib
import hmac
import json
import logging
from typing import Any, Optional

import aiohttp

logger = logging.getLogger("girgitton")

_POLL_INTERVAL = 5.0


def _sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


class APIClient:
    def __init__(
        self,
        api_url: str,
        api_secret: str,
        user_id: int,
        chat_id: int,
        setup_token: str,
    ) -> None:
        self._url = api_url.rstrip("/")
        self._secret = api_secret
        self._user_id = user_id
        self._chat_id = chat_id
        self._setup_token = setup_token
        self._connected = False
        self._session: Optional[aiohttp.ClientSession] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._stop_callback: Optional[Any] = None
        self._status: dict = {}

    async def _open_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _headers(self, body: bytes) -> dict[str, str]:
        return {"X-Signature": _sign(body, self._secret), "Content-Type": "application/json"}

    async def connect(self) -> bool:
        """POST /connect — one-time token validate."""
        if not self._url:
            self._connected = True
            return True
        payload = json.dumps(
            {"setup_token": self._setup_token, "user_id": self._user_id, "chat_id": self._chat_id}
        ).encode()
        try:
            sess = await self._open_session()
            async with sess.post(
                f"{self._url}/connect",
                data=payload,
                headers=self._headers(payload),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                self._connected = data.get("ok", False)
                if not self._connected:
                    logger.warning("API /connect xatolik: %s", data)
                return self._connected
        except Exception as exc:
            logger.warning("API /connect ulanib bo'lmadi: %s", exc)
            return False

    def set_stop_callback(self, cb: Any) -> None:
        """Stop signali kelganda chaqiriladigan callback."""
        self._stop_callback = cb

    def update_status(self, batch: int, total: int, speed: float) -> None:
        self._status = {
            "user_id": self._user_id,
            "chat_id": self._chat_id,
            "batch": batch,
            "total": total,
            "speed": round(speed, 3),
        }

    async def _post_status(self) -> None:
        if not self._url or not self._status:
            return
        payload = json.dumps(self._status).encode()
        try:
            sess = await self._open_session()
            async with sess.post(
                f"{self._url}/status",
                data=payload,
                headers=self._headers(payload),
                timeout=aiohttp.ClientTimeout(total=5),
            ):
                pass
        except Exception as exc:
            logger.debug("API /status yuborib bo'lmadi: %s", exc)

    async def _get_task(self) -> Optional[str]:
        if not self._url:
            return None
        body = b""
        params = {"user_id": str(self._user_id), "chat_id": str(self._chat_id)}
        headers = {"X-Signature": _sign(body, self._secret)}
        try:
            sess = await self._open_session()
            async with sess.get(
                f"{self._url}/task",
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                data = await resp.json()
                return data.get("action")
        except Exception as exc:
            logger.debug("API /task xatolik: %s", exc)
            return None

    async def start_polling(self) -> None:
        self._poll_task = asyncio.ensure_future(self._poll_loop())

    async def stop_polling(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        if self._session and not self._session.closed:
            await self._session.close()

    async def _poll_loop(self) -> None:
        while True:
            await asyncio.sleep(_POLL_INTERVAL)
            await self._post_status()
            action = await self._get_task()
            if action == "stop" and self._stop_callback:
                logger.info("API: stop signali qabul qilindi")
                if asyncio.iscoroutinefunction(self._stop_callback):
                    await self._stop_callback()
                else:
                    self._stop_callback()
