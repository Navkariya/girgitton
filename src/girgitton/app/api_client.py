"""Bot HTTP API klienti (HMAC imzolash + status polling)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp

from girgitton.core.constants import (
    APP_POLL_INTERVAL_SECONDS,
    HTTP_REQUEST_TIMEOUT_SECONDS,
)
from girgitton.shared.crypto import HMACSigner

logger = logging.getLogger(__name__)

StopCallback = Callable[[], Awaitable[None] | None]
ResumeCallback = Callable[[], Awaitable[None] | None]


async def fetch_groups(
    server_url: str, api_secret: str, user_id: int
) -> list[dict[str, Any]]:
    """`GET /groups?user_id=<>` (HMAC) — shu user'ning aktiv guruhlar ro'yxati."""
    url = f"{server_url.rstrip('/')}/groups?user_id={user_id}"
    body = b""
    headers: dict[str, str] = {}
    if api_secret:
        signed = HMACSigner(api_secret).sign(body)
        headers.update(signed.headers())

    timeout = aiohttp.ClientTimeout(total=HTTP_REQUEST_TIMEOUT_SECONDS)
    try:
        async with (
            aiohttp.ClientSession(timeout=timeout) as sess,
            sess.get(url, headers=headers) as resp,
        ):
            data = await resp.json()
            if data.get("ok"):
                groups = data.get("groups", [])
                return list(groups) if isinstance(groups, list) else []
            return []
    except Exception as exc:
        logger.debug("/groups xatoligi: %s", exc)
        return []


class APIClient:
    """Status yuborish va task polling klienti."""

    def __init__(
        self,
        api_url: str,
        api_secret: str,
        user_id: int,
        *,
        poll_interval: float = APP_POLL_INTERVAL_SECONDS,
    ) -> None:
        self._url = api_url.rstrip("/")
        self._signer = HMACSigner(api_secret) if api_secret else None
        self._user_id = user_id
        self._poll_interval = poll_interval
        self._session: aiohttp.ClientSession | None = None
        self._poll_task: asyncio.Task[None] | None = None
        self._stop_callback: StopCallback | None = None
        self._resume_callback: ResumeCallback | None = None
        self._status: dict[str, Any] = {}

    def set_stop_callback(self, cb: StopCallback) -> None:
        self._stop_callback = cb

    def set_resume_callback(self, cb: ResumeCallback) -> None:
        self._resume_callback = cb

    def update_status(
        self, batch: int, total: int, speed: float, *, current_group: int = 0
    ) -> None:
        self._status = {
            "user_id": self._user_id,
            "batch": batch,
            "total": total,
            "speed": round(speed, 3),
            "chat_id": current_group,
        }

    async def _open_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _headers(self, body: bytes) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._signer is not None:
            signed = self._signer.sign(body)
            headers.update(signed.headers())
        return headers

    async def post_status(self) -> None:
        if not self._url or not self._status:
            return
        body = json.dumps(self._status).encode()
        timeout = aiohttp.ClientTimeout(total=HTTP_REQUEST_TIMEOUT_SECONDS)
        try:
            sess = await self._open_session()
            async with sess.post(
                f"{self._url}/status",
                data=body,
                headers=self._headers(body),
                timeout=timeout,
            ) as resp:
                if resp.status >= 400:
                    logger.debug("API /status %s: %s", resp.status, await resp.text())
        except Exception as exc:
            logger.debug("API /status xatoligi: %s", exc)

    async def get_task(self) -> str | None:
        if not self._url:
            return None
        body = b""
        timeout = aiohttp.ClientTimeout(total=HTTP_REQUEST_TIMEOUT_SECONDS)
        try:
            sess = await self._open_session()
            async with sess.get(
                f"{self._url}/task",
                params={"user_id": str(self._user_id)},
                headers=self._headers(body),
                timeout=timeout,
            ) as resp:
                if resp.status >= 400:
                    return None
                data = await resp.json()
                action = data.get("action")
                return str(action) if action else None
        except Exception as exc:
            logger.debug("API /task xatoligi: %s", exc)
            return None

    async def start_polling(self) -> None:
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop_polling(self) -> None:
        if self._poll_task is not None:
            self._poll_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._poll_task
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def _poll_loop(self) -> None:
        while True:
            await asyncio.sleep(self._poll_interval)
            await self.post_status()
            action = await self.get_task()
            if action == "stop" and self._stop_callback is not None:
                logger.info("API: stop signali")
                result = self._stop_callback()
                if asyncio.iscoroutine(result):
                    await result
            elif action == "resume" and self._resume_callback is not None:
                logger.info("API: resume signali")
                result = self._resume_callback()
                if asyncio.iscoroutine(result):
                    await result
