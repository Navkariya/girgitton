"""Global upload worker pool (3 worker by default).

Har worker o'z `TelegramClient` (bot session) ga ega bo'ladi va
`asyncio.Queue` orqali batchlarni oladi.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from girgitton.app.upload.batch import send_album_pair
from girgitton.app.upload.rate_limit import (
    FloodWaitRetry,
    RotationPolicy,
    SpeedTracker,
    ThrottleCallback,
    now_monotonic,
    wait_with_callback,
)
from girgitton.core.constants import MAX_WORKERS

if TYPE_CHECKING:
    from telethon import TelegramClient

    from girgitton.core.models import MediaBatch


logger = logging.getLogger(__name__)

NotifyFn = Callable[[str], Awaitable[None]]
ClientFactory = Callable[[int], "TelegramClient"]


@dataclass(slots=True)
class _UploadTask:
    batch: MediaBatch
    chat_id: int
    total_batches: int
    future: asyncio.Future[bool] = field(default_factory=asyncio.Future)


@dataclass(slots=True)
class WorkerPoolConfig:
    workers: int = 3
    policy: RotationPolicy = field(default_factory=RotationPolicy)
    bot_token: str = ""


class GlobalWorkerPool:
    """Bir necha worker uchun batch queue va session boshqaruvi."""

    def __init__(
        self,
        config: WorkerPoolConfig,
        *,
        client_factory: ClientFactory,
    ) -> None:
        self._config = config
        self._n = max(1, min(config.workers, MAX_WORKERS))
        self._client_factory = client_factory
        self._clients: list[TelegramClient] = []
        self._queue: asyncio.Queue[_UploadTask | None] = asyncio.Queue()
        self._tasks: list[asyncio.Task[None]] = []
        self._stop_flag = [False]

    @property
    def stop_flag(self) -> list[bool]:
        return self._stop_flag

    async def start(self) -> None:
        for i in range(self._n):
            client = self._client_factory(i)
            await client.start(bot_token=self._config.bot_token)  # type: ignore[attr-defined]
            self._clients.append(client)
            logger.info("W%d ulandi", i)

    async def stop(self) -> None:
        # Workerlarga sentinel yuborish
        for _ in range(self._n):
            await self._queue.put(None)
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        for c in self._clients:
            with suppress(Exception):
                await c.disconnect()  # type: ignore[attr-defined]
        self._clients.clear()
        self._tasks.clear()

    def submit(self, batch: MediaBatch, chat_id: int, total_batches: int) -> asyncio.Future[bool]:
        task = _UploadTask(batch=batch, chat_id=chat_id, total_batches=total_batches)
        self._queue.put_nowait(task)
        return task.future

    def request_stop(self) -> None:
        self._stop_flag[0] = True

    def run(
        self,
        *,
        notify: NotifyFn,
        on_throttle: ThrottleCallback | None = None,
    ) -> None:
        for i in range(self._n):
            self._tasks.append(asyncio.create_task(self._worker(i, notify, on_throttle)))

    # ─── Worker loop ─────────────────────────────────────────────────────────

    async def _worker(
        self,
        worker_id: int,
        notify: NotifyFn,
        on_throttle: ThrottleCallback | None,
    ) -> None:
        client = self._clients[worker_id]
        tracker = SpeedTracker(window=3)
        flood_retry = FloodWaitRetry(max_retries=3)
        batches_done = 0
        rotation_started = now_monotonic()

        while True:
            item = await self._queue.get()
            if item is None:
                self._queue.task_done()
                return

            if self._stop_flag[0]:
                if not item.future.done():
                    item.future.set_result(False)
                self._queue.task_done()
                continue

            # ─── Sessiya rotatsiyasi ─────────────────────────────────────────
            elapsed = now_monotonic() - rotation_started
            if self._config.policy.should_rotate(
                batches_done=batches_done,
                time_elapsed=elapsed,
                tracker=tracker,
            ):
                await self._rotate(worker_id, client, notify)
                tracker.reset()
                rotation_started = now_monotonic()

            # ─── Yuklash + ikki marta yuborish ───────────────────────────────
            t0 = time.perf_counter()
            mb = item.batch.total_bytes / 1_048_576
            ok = True
            try:
                await flood_retry.execute(
                    lambda: send_album_pair(client, item.chat_id, item.batch, item.total_batches),
                    notify=notify,
                )
            except Exception:
                logger.exception("W%d batch %d xatoligi", worker_id, item.batch.idx)
                await notify(f"⚠️ W{worker_id} batch {item.batch.idx} xatolik")
                ok = False

            elapsed_secs = max(time.perf_counter() - t0, 0.001)
            speed = tracker.record(mb, elapsed_secs)
            batches_done += 1

            await notify(
                f"✓ W{worker_id} qism {item.batch.idx}/{item.total_batches} — "
                f"{mb:.1f} MB / {elapsed_secs:.1f}s = {speed:.2f} MB/s"
            )

            # ─── Throttle aniqlash ───────────────────────────────────────────
            if self._config.policy.should_throttle(last_speed=speed):
                logger.warning("W%d throttle: %.3f MB/s", worker_id, speed)
                await wait_with_callback(
                    self._config.policy.throttle_wait_seconds, on_throttle, speed
                )
                await self._rotate(worker_id, client, notify)
                tracker.reset()
                rotation_started = now_monotonic()

            if not item.future.done():
                item.future.set_result(ok)
            self._queue.task_done()

    async def _rotate(self, worker_id: int, client: TelegramClient, notify: NotifyFn) -> None:
        logger.info("W%d sessiyani yangilamoqda", worker_id)
        await notify(f"🔄 W{worker_id} sessiya yangilanmoqda")
        with suppress(Exception):
            await client.disconnect()  # type: ignore[attr-defined]
        await asyncio.sleep(2)
        with suppress(Exception):
            await client.start(bot_token=self._config.bot_token)  # type: ignore[attr-defined]
