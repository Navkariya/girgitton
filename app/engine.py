"""
Upload orkestratori — GUI va GlobalWorkerPool orasidagi ko'prik.

Vazifasi (v2.1 multi-group):
  1. Belgilangan guruhlar uchun media fayllarni skanerlaydi
  2. Barcha vazifalarni GlobalWorkerPool ga navbatma-navbat (round-robin) uzatadi
  3. Progress saqlanadi
  4. Tugagach notify() orqali GUI xabardor qilinadi
"""

import asyncio
import logging
from collections import deque
from typing import Awaitable, Callable, Optional

from app import app_config
from app.worker_pool import GlobalWorkerPool, ThrottleFn
from helpers import chunked, scan_media_files

logger = logging.getLogger("girgitton")

NotifyFn = Callable[[str], Awaitable[None]]
ProgressFn = Callable[[int, int, int, float], None]  # (group_id, done, total, speed_mb_s)


class UploadEngine:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._pool: Optional[GlobalWorkerPool] = None
        self._stop_flag: list[bool] = [False]

    def stop(self) -> None:
        self._stop_flag[0] = True

    async def run(
        self,
        group_folders: dict[int, str],
        notify: NotifyFn,
        on_progress: ProgressFn,
        on_throttle: Optional[ThrottleFn] = None,
    ) -> None:
        cfg = app_config.load()
        if not cfg:
            await notify("⚠️ Config topilmadi. Avval ulaning.")
            return

        api_id: int = int(cfg["api_id"])
        api_hash: str = cfg["api_hash"]
        bot_token: str = cfg["bot_token"]

        import config as srv_config

        self._stop_flag = [False]
        
        # Tayyorgarlik: har bir guruh uchun vazifalarni yig'ish
        tasks_by_group: dict[int, list[tuple]] = {}
        total_batches_all = 0
        
        for group_id, folder in group_folders.items():
            if not folder:
                continue
                
            logger.info("Media scan: G%s -> %s", group_id, folder)
            try:
                media_files = scan_media_files(folder)
            except Exception as exc:
                await notify(f"❌ Papka skanerlashda xatolik ({folder}): {exc}")
                continue

            if not media_files:
                await notify(f"ℹ️ {folder} da media topilmadi.")
                continue

            batches = chunked(media_files, srv_config.BATCH_SIZE)
            total = len(batches)
            
            # TODO: Progressni tiklash logika qo'shish mumkin
            offset = 0 
            
            tasks_by_group[group_id] = [
                (offset + i + 1, batch, total) for i, batch in enumerate(batches)
            ]
            total_batches_all += total

        if not tasks_by_group:
            await notify("Yuklash uchun hech narsa topilmadi.")
            return

        logger.info("WorkerPool yaratilmoqda: workers=%d", srv_config.UPLOAD_WORKERS)
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
            total_batches=total_batches_all,
            notify=notify,
            stop_flag=self._stop_flag,
            on_throttle=on_throttle,
        )

        await notify(f"▶️ Yuklash boshlandi (jami {total_batches_all} qism)")

        queues = {gid: deque(tasks) for gid, tasks in tasks_by_group.items()}
        futures_map: dict[asyncio.Future, tuple[int, int, int]] = {}
        dones_by_group = {gid: 0 for gid in group_folders.keys()}

        # Dastlabki vazifalarni qo'shish (har bir guruhdan 1 tadan)
        for gid in list(queues.keys()):
            if queues[gid]:
                batch_idx, batch, total = queues[gid].popleft()
                fut = pool.submit(batch_idx, batch, gid)
                futures_map[fut] = (gid, batch_idx, total)

        # Asosiy kuzatish sikli
        while futures_map:
            done, _ = await asyncio.wait(
                list(futures_map.keys()), 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for fut in done:
                gid, batch_idx, total = futures_map.pop(fut)
                
                try:
                    await fut
                    dones_by_group[gid] += 1
                    on_progress(gid, dones_by_group[gid], total, 0.0)
                except asyncio.CancelledError:
                    pass
                except Exception as exc:
                    logger.error("Vazifada kutilmagan xato: %s", exc)

                # Shu guruh uchun keyingi qismni yuborish (agar bo'lsa)
                if not self._stop_flag[0] and queues[gid]:
                    next_batch_idx, next_batch, next_total = queues[gid].popleft()
                    new_fut = pool.submit(next_batch_idx, next_batch, gid)
                    futures_map[new_fut] = (gid, next_batch_idx, next_total)

        await pool.stop()
        self._pool = None

        if self._stop_flag[0]:
            await notify("🛑 Yuklash to'xtatildi.")
        else:
            await notify("✅ Barcha vazifalar yakunlandi!")
