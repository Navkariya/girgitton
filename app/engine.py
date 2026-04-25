"""
Upload orkestratori — GUI va WorkerPool orasidagi ko'prik.

Vazifasi:
  1. Media fayllarni skanerlaydi
  2. Oldingi progressni yuklaydi
  3. Qismlarni WorkerPool ga uzatadi
  4. Progress saqlanadi har qism tugagach
  5. Tugagach notify() orqali GUI xabardor qilinadi
"""

import asyncio
import logging
from typing import Awaitable, Callable, Optional

from app import app_config
from app.worker_pool import GlobalWorkerPool, ThrottleFn
from helpers import chunked, scan_media_files

logger = logging.getLogger("girgitton")

NotifyFn = Callable[[str], Awaitable[None]]
ProgressFn = Callable[[int, int, float], None]  # (done, total, speed_mb_s)


class UploadEngine:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._pool: Optional[GlobalWorkerPool] = None
        self._stop_flag: list[bool] = [False]

    def stop(self) -> None:
        self._stop_flag[0] = True

    async def run(
        self,
        folder: str,
        notify: NotifyFn,
        on_progress: ProgressFn,
        on_throttle: Optional[ThrottleFn] = None,
    ) -> None:
        cfg = app_config.load()
        if not cfg:
            await notify("⚠️ Config topilmadi. /setup qayta bajaring.")
            return

        api_id: int = int(cfg["api_id"])
        api_hash: str = cfg["api_hash"]
        bot_token: str = cfg["bot_token"]
        chat_id: int = int(cfg["group_id"])

        import config as srv_config

        self._stop_flag = [False]
        media_files = scan_media_files(folder)
        if not media_files:
            await notify("ℹ️ Papkada media fayl topilmadi.")
            return

        batches = chunked(media_files, srv_config.BATCH_SIZE)
        total = len(batches)

        start_batch = int(app_config.get("last_progress_batch") or 0)
        if start_batch > 0 and start_batch < total:
            await notify(f"ℹ️ Oldingi progress topildi: {start_batch}/{total}. Davom etilmoqda...")
            batches = batches[start_batch:]
            offset = start_batch
        else:
            offset = 0

        pool = GlobalWorkerPool(
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
            workers=srv_config.UPLOAD_WORKERS,
            rotate_after_n_batches=srv_config.ROTATE_AFTER_N_BATCHES,
            rotate_after_seconds=srv_config.ROTATE_AFTER_SECONDS,
            speed_drop_threshold=srv_config.SPEED_DROP_THRESHOLD,
            throttle_speed_limit=srv_config.THROTTLE_SPEED_LIMIT,
            throttle_wait_seconds=srv_config.THROTTLE_WAIT_SECONDS,
        )
        self._pool = pool

        await pool.start()
        pool.run_workers(
            total_batches=total + offset,
            notify=notify,
            stop_flag=self._stop_flag,
            on_throttle=on_throttle,
        )

        await notify(f"▶️ Yuklash boshlandi: {len(media_files)} ta fayl, {total} ta qism")
        app_config.set_last_folder(folder)

        futures: list[asyncio.Future] = []
        for i, batch in enumerate(batches):
            fut = pool.submit(
                batch_idx=offset + i + 1,
                batch=batch,
                chat_id=chat_id,
            )
            futures.append(fut)

        done_count = 0
        for i, fut in enumerate(futures):
            try:
                await fut
                done_count += 1
                # Progress callback
                speed = 0.0  # pool workers log haqiqiy tezlikni
                on_progress(offset + i + 1, total + offset, speed)
                # Progress saqlash
                cfg_data = app_config.load() or {}
                cfg_data["last_progress_batch"] = offset + i + 1
                app_config.save(cfg_data)
            except asyncio.CancelledError:
                pass

        await pool.stop()
        self._pool = None

        if self._stop_flag[0]:
            await notify("🛑 Yuklash to'xtatildi. Progress saqlandi.")
        else:
            cfg_data = app_config.load() or {}
            cfg_data["last_progress_batch"] = 0
            app_config.save(cfg_data)
            await notify(f"✅ Barcha {len(media_files)} ta fayl yuborildi!")
