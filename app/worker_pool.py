"""
GlobalWorkerPool — barcha chatlar uchun bitta umumiy upload pool.

Xususiyatlar:
  - MAX 5 worker (bot token sessiyasi)
  - asyncio.Queue orqali vazifalar taqsimlanadi
  - 3 mezonli rotation: qism soni YOKI vaqt YOKI tezlik pasayishi
  - Akkaunt throttle aniqlash: 30 daqiqa avtokutish
"""

import asyncio
import logging
import time
from contextlib import suppress
from pathlib import Path
from typing import Awaitable, Callable, Optional

from telethon import TelegramClient

logger = logging.getLogger("girgitton")

# Rotation parametrlari (config.py dan olinadi agar mavjud bo'lsa)
_ROTATE_AFTER_N_BATCHES: int = 15
_ROTATE_AFTER_SECONDS: int = 300
_SPEED_DROP_THRESHOLD: float = 0.10
_THROTTLE_SPEED_LIMIT: float = 0.05
_THROTTLE_WAIT_SECONDS: int = 1800

NotifyFn = Callable[[str], Awaitable[None]]
ThrottleFn = Callable[[float, int], Awaitable[None]]  # (speed, wait_seconds)


class _UploadTask:
    __slots__ = ("batch_idx", "batch", "chat_id", "future")

    def __init__(
        self,
        batch_idx: int,
        batch: list[Path],
        chat_id: int,
        future: asyncio.Future,
    ) -> None:
        self.batch_idx = batch_idx
        self.batch = batch
        self.chat_id = chat_id
        self.future = future


async def _reconnect(client: TelegramClient, label: str, bot_token: str) -> None:
    try:
        await client.disconnect()
        await asyncio.sleep(3)
        await client.start(bot_token=bot_token)
        logger.info("%s: sessiya yangilandi (fresh bandwidth)", label)
    except Exception as exc:
        logger.warning("%s: reconnect xatosi: %s — davom etiladi", label, exc)
        with suppress(Exception):
            await client.start(bot_token=bot_token)


async def _upload_batch_files(
    client: TelegramClient,
    worker_id: int,
    batch_idx: int,
    batch: list[Path],
    chat_id: int,
    total_batches: int,
    notify: NotifyFn,
    stop_flag: list[bool],
) -> bool:
    """Bitta qismni (media + document album) yuboradi. True = muvaffaqiyat."""
    from config import DELAY_BETWEEN_STEPS

    if stop_flag[0]:
        return False

    batch_names = ", ".join(f.name for f in batch)
    logger.info("W%d Qism %d/%d: %s", worker_id, batch_idx, total_batches, batch_names)
    await notify(f"⏳ W{worker_id} Qism {batch_idx}/{total_batches} yuklanmoqda ({len(batch)} fayl)...")

    file_paths = [str(f) for f in batch]
    media_caption = f"📸 Qism {batch_idx}/{total_batches} — Media ({len(batch)} ta)"
    doc_caption = f"📁 Qism {batch_idx}/{total_batches} — Documents ({len(batch)} ta)"

    try:
        await client.send_file(
            chat_id,
            file_paths,
            caption=[media_caption] + [""] * (len(batch) - 1),
            force_document=False,
        )
    except Exception as exc:
        logger.error("W%d media album xatolik (qism %d): %s", worker_id, batch_idx, exc)
        await notify(f"⚠️ W{worker_id} Qism {batch_idx} media: {exc}")

    await asyncio.sleep(DELAY_BETWEEN_STEPS)

    if stop_flag[0]:
        return False

    try:
        await client.send_file(
            chat_id,
            file_paths,
            caption=[doc_caption] + [""] * (len(batch) - 1),
            force_document=True,
        )
    except Exception as exc:
        logger.error("W%d document album xatolik (qism %d): %s", worker_id, batch_idx, exc)
        await notify(f"⚠️ W{worker_id} Qism {batch_idx} documents: {exc}")

    logger.info("W%d Qism %d tugadi ✓", worker_id, batch_idx)
    return True


class GlobalWorkerPool:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        bot_token: str,
        workers: int = 3,
        rotate_after_n_batches: int = _ROTATE_AFTER_N_BATCHES,
        rotate_after_seconds: int = _ROTATE_AFTER_SECONDS,
        speed_drop_threshold: float = _SPEED_DROP_THRESHOLD,
        throttle_speed_limit: float = _THROTTLE_SPEED_LIMIT,
        throttle_wait_seconds: int = _THROTTLE_WAIT_SECONDS,
    ) -> None:
        self._api_id = api_id
        self._api_hash = api_hash
        self._bot_token = bot_token
        self._n_workers = min(workers, 5)  # Telegram ban xavfidan himoya

        self._rotate_after_n = rotate_after_n_batches
        self._rotate_after_s = rotate_after_seconds
        self._speed_drop = speed_drop_threshold
        self._throttle_limit = throttle_speed_limit
        self._throttle_wait = throttle_wait_seconds

        self._clients: list[TelegramClient] = []
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        # Session fayllarni ~/.girgitton/ ichida saqlash
        # (.exe dan ishga tushganda CWD yoziladigan joy bo'lmasligi mumkin)
        from pathlib import Path
        session_dir = Path.home() / ".girgitton"
        session_dir.mkdir(exist_ok=True)

        for i in range(self._n_workers):
            session_path = str(session_dir / f"worker_{i}")
            logger.info("W%d yaratilmoqda: session=%s", i, session_path)
            client = TelegramClient(
                session_path,
                self._api_id,
                self._api_hash,
            )
            try:
                await client.start(bot_token=self._bot_token)
                self._clients.append(client)
                logger.info("W%d ishga tushdi ✓", i)
            except Exception as exc:
                logger.error("W%d ishga tushirishda xatolik: %s", i, exc, exc_info=True)
                raise

    async def stop(self) -> None:
        for _ in self._clients:
            await self._queue.put(None)
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        for client in self._clients:
            with suppress(Exception):
                await client.disconnect()
        self._clients.clear()
        self._worker_tasks.clear()

    def submit(
        self,
        batch_idx: int,
        batch: list[Path],
        chat_id: int,
    ) -> asyncio.Future:
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._queue.put_nowait(_UploadTask(batch_idx, batch, chat_id, fut))
        return fut

    def run_workers(
        self,
        total_batches: int,
        notify: NotifyFn,
        stop_flag: list[bool],
        on_throttle: Optional[ThrottleFn] = None,
    ) -> None:
        for i in range(self._n_workers):
            task = asyncio.ensure_future(
                self._worker(i, total_batches, notify, stop_flag, on_throttle)
            )
            self._worker_tasks.append(task)

    async def _worker(
        self,
        worker_id: int,
        total_batches: int,
        notify: NotifyFn,
        stop_flag: list[bool],
        on_throttle: Optional[ThrottleFn],
    ) -> None:
        client = self._clients[worker_id]
        batches_done = 0
        speed_history: list[float] = []
        last_rotate = time.monotonic()

        while True:
            item: Optional[_UploadTask] = await self._queue.get()
            if item is None:
                self._queue.task_done()
                break

            if stop_flag[0]:
                if not item.future.done():
                    item.future.cancel()
                self._queue.task_done()
                continue

            # ── 3 mezonli rotation ──────────────────────────────────────────
            time_elapsed = time.monotonic() - last_rotate
            avg_speed = (
                sum(speed_history[-3:]) / min(len(speed_history), 3)
                if speed_history
                else 999.0
            )
            should_rotate = (
                (batches_done > 0 and batches_done % self._rotate_after_n == 0)
                or time_elapsed >= self._rotate_after_s
                or (len(speed_history) >= 3 and avg_speed < self._speed_drop)
            )

            if should_rotate and batches_done > 0:
                await _reconnect(client, f"W{worker_id}", self._bot_token)
                speed_history.clear()
                last_rotate = time.monotonic()

            # ── Upload ──────────────────────────────────────────────────────
            t0 = time.perf_counter()
            size_mb = sum(p.stat().st_size for p in item.batch) / 1_048_576

            ok = await _upload_batch_files(
                client,
                worker_id,
                item.batch_idx,
                item.batch,
                item.chat_id,
                total_batches,
                notify,
                stop_flag,
            )

            elapsed = time.perf_counter() - t0
            speed = size_mb / elapsed if elapsed > 0 else 0.0
            speed_history.append(speed)
            batches_done += 1

            # ── Throttle aniqlash ──────────────────────────────────────────
            if speed < self._throttle_limit and should_rotate:
                logger.warning(
                    "W%d throttle aniqlandi (speed=%.3f MB/s)", worker_id, speed
                )
                if on_throttle:
                    await on_throttle(speed, self._throttle_wait)
                else:
                    await notify(
                        f"⚠️ Telegram tezlikni chekladi ({speed:.2f} MB/s).\n"
                        f"{self._throttle_wait // 60} daqiqa kutilmoqda..."
                    )
                await asyncio.sleep(self._throttle_wait)
                await _reconnect(client, f"W{worker_id}", self._bot_token)
                last_rotate = time.monotonic()
                speed_history.clear()

            if not item.future.done():
                item.future.set_result(ok)
            self._queue.task_done()
