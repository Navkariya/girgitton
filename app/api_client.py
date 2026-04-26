"""
Railway Mini API bilan HMAC-signed HTTP aloqa va xavfsiz pairing.

Funksiyalar:
  - auto_pair()  — localhost orqali avtomatik ulanish (GET /auto-pair)
  - pair(code)   — kod yordamida ulanish (POST /pair)
  - start_polling() — har 5 soniyada progress yuborish (POST /status) va task kutish (GET /task)
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
    if not secret:
        return ""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


async def auto_pair(server_url: str = "http://127.0.0.1:8080") -> dict[str, Any]:
    """Lokal serverdan credentials olish."""
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(f"{server_url}/auto-pair", timeout=5) as resp:
                data = await resp.json()
                if data.get("ok"):
                    # Qo'shimcha saqlash oson bo'lishi uchun api_url qo'shamiz
                    data["api_url"] = server_url
                    return data
                return {"error": data.get("error", "Noma'lum xatolik")}
    except Exception as exc:
        return {"error": f"Ulanib bo'lmadi: {exc}"}


async def pair(server_url: str, code: str) -> dict[str, Any]:
    """Pair code orqali serverdan credentials olish."""
    url = server_url.rstrip("/")
    payload = json.dumps({"code": code}).encode()
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.post(
                f"{url}/pair",
                data=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            ) as resp:
                data = await resp.json()
                if data.get("ok"):
                    data["api_url"] = url
                    # Formatni auto-pair bilan bir xil qilamiz (groups ro'yxati)
                    if "group" in data:
                        data["groups"] = [data["group"]]
                    return data
                return {"error": data.get("error", "Kod yaroqsiz yoki muddati o'tgan")}
    except Exception as exc:
        return {"error": f"Serverga ulanib bo'lmadi: {exc}"}


class APIClient:
    def __init__(
        self,
        api_url: str,
        api_secret: str,
        user_id: int,
    ) -> None:
        self._url = api_url.rstrip("/")
        self._secret = api_secret
        self._user_id = user_id
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._stop_callback: Optional[Any] = None
        self._status: dict = {}

    async def _open_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _headers(self, body: bytes) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._secret:
            headers["X-Signature"] = _sign(body, self._secret)
        return headers

    def set_stop_callback(self, cb: Any) -> None:
        """Stop signali kelganda chaqiriladigan callback."""
        self._stop_callback = cb

    def update_status(self, batch: int, total: int, speed: float, current_group: int = 0) -> None:
        self._status = {
            "user_id": self._user_id,
            "batch": batch,
            "total": total,
            "speed": round(speed, 3),
        }
        if current_group:
            self._status["chat_id"] = current_group

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
        params = {"user_id": str(self._user_id)}
        headers = self._headers(body)
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
