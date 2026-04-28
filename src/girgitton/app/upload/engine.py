"""UploadEngine — GUI va GlobalWorkerPool orasidagi ko'prik.

Vazifasi:
  1. Har guruh uchun media fayllarni skanerlash
  2. Batchlarni round-robin tarzda WorkerPoolga uzatish
  3. Progress event'larini callbackka uzatish
  4. Stop flag respect
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from girgitton.app import progress_store
from girgitton.app.upload.rate_limit import RotationPolicy, ThrottleCallback
from girgitton.app.upload.worker_pool import (
    GlobalWorkerPool,
    NotifyFn,
    WorkerPoolConfig,
)
from girgitton.core.constants import BATCH_SIZE
from girgitton.shared.media import make_batches, scan_media_folder

if TYPE_CHECKING:
    from telethon import TelegramClient

    from girgitton.core.config import Settings
    from girgitton.core.models import MediaBatch


logger = logging.getLogger(__name__)

# (group_id, batches_done, total_batches, last_speed)
ProgressFn = Callable[[int, int, int, float], None]


def _default_client_factory(
    settings: Settings, session_dir: Path
) -> Callable[[int], TelegramClient]:
    """Har worker uchun alohida sessiya bilan robust TelegramClient yaratuvchi.

    Optimizatsiyalar (uzun yuklash uchun barqarorlik):
    - `flood_sleep_threshold=120` — 120s gacha FloodWait Telethon o'zi avtomatik kutadi
    - `request_retries=10`, `connection_retries=10` — tarmoq glitch'larida avto-retry
    - `retry_delay=2` — retry'lar orasi 2s
    - `auto_reconnect=True` — uzilishlardan keyin avto-tikla
    """
    from telethon import TelegramClient as _TC

    session_dir.mkdir(parents=True, exist_ok=True)

    def factory(idx: int) -> _TC:
        return _TC(
            str(session_dir / f"worker_{idx}"),
            api_id=settings.api_id,
            api_hash=settings.api_hash.get(),
            flood_sleep_threshold=120,
            request_retries=10,
            connection_retries=10,
            retry_delay=2,
            auto_reconnect=True,
        )

    return factory


class UploadEngine:
    """Yuklash orkestratori (1 ta yoki bir nechta guruh uchun)."""

    def __init__(
        self,
        settings: Settings,
        *,
        session_dir: Path | None = None,
        client_factory: Callable[[int], TelegramClient] | None = None,
    ) -> None:
        from girgitton.core import app_paths

        self._settings = settings
        self._session_dir = session_dir or app_paths.get_sessions_dir()
        self._client_factory = (
            client_factory
            if client_factory is not None
            else _default_client_factory(settings, self._session_dir)
        )
        self._pool: GlobalWorkerPool | None = None
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True
        if self._pool is not None:
            self._pool.request_stop()

    async def run(
        self,
        group_folders: dict[int, str | Path],
        notify: NotifyFn,
        on_progress: ProgressFn,
        on_throttle: ThrottleCallback | None = None,
        *,
        resume: bool = False,
    ) -> None:
        """Asosiy ish funksiyasi.

        Args:
            group_folders: {chat_id: folder_path}
            notify: GUI log funksiyasi
            on_progress: progress callback (group_id, done, total, speed)
            on_throttle: throttle dialog callback
            resume: True bo'lsa lokal `progress.json` dan davom ettiradi —
                    har guruh uchun saqlangan `completed_batches` dan keyingi
                    batchdan boshlanadi.
        """
        self._stop_requested = False

        saved = progress_store.load_all() if resume else {}

        # ─── Skaner: har guruh uchun batchlar ─────────────────────────────
        per_group_batches: dict[int, tuple[MediaBatch, ...]] = {}
        per_group_skipped: dict[int, int] = {}  # resume da o'tkazib yuborilganlar
        per_group_total: dict[int, int] = {}
        total_batches_all = 0
        for gid, folder in group_folders.items():
            if not folder:
                continue
            folder_path = Path(folder)
            try:
                files = scan_media_folder(folder_path)
            except Exception as exc:
                await notify(f"⚠️ Skaner xatoligi {folder}: {exc}")
                continue
            if not files:
                await notify(f"ℹ️ {folder}: media topilmadi")
                continue
            batches = make_batches(files, batch_size=BATCH_SIZE)
            total = len(batches)
            per_group_total[gid] = total

            skip = 0
            if resume and gid in saved:
                sp = saved[gid]
                # Faqat papka o'zgarmagan bo'lsa va total mos bo'lsa skip
                current_sig = progress_store.folder_signature(folder_path)
                if (
                    sp.folder == str(folder_path)
                    and sp.folder_hash == current_sig
                    and sp.total_batches == total
                    and 0 < sp.completed_batches < total
                ):
                    skip = sp.completed_batches
                    await notify(f"⏯ G{gid}: resume — {skip}/{total} batch o'tkazib yuboriladi")
                else:
                    await notify(
                        f"ℹ️ G{gid}: saqlangan progress mos kelmadi (papka o'zgargan?), "
                        f"yangidan boshlanadi"
                    )
                    progress_store.clear_group(gid)

            per_group_skipped[gid] = skip
            remaining_batches = batches[skip:]
            if not remaining_batches:
                await notify(f"✅ G{gid}: avval to'liq tugagan, o'tkazildi")
                progress_store.clear_group(gid)
                continue
            per_group_batches[gid] = remaining_batches
            total_batches_all += len(remaining_batches)
            await notify(
                f"📂 G{gid}: {len(files)} fayl → {total} batch jami "
                f"(qoldiq: {len(remaining_batches)})"
            )

        if not per_group_batches:
            await notify("Yuklash uchun ma'lumot yo'q.")
            return

        # ─── Worker pool ──────────────────────────────────────────────────
        policy = RotationPolicy(
            rotate_after_n_batches=self._settings.rotate_after_n_batches,
            rotate_after_seconds=self._settings.rotate_after_seconds,
            speed_drop_threshold=self._settings.speed_drop_threshold,
            last_batch_speed_threshold=self._settings.last_batch_speed_threshold,
            throttle_speed_limit=self._settings.throttle_speed_limit,
            throttle_wait_seconds=self._settings.throttle_wait_seconds,
        )
        config = WorkerPoolConfig(
            workers=self._settings.upload_workers,
            policy=policy,
            bot_token=self._settings.bot_token.get(),
            delay_between_steps=self._settings.delay_between_steps,
            delay_between_batches=self._settings.delay_between_batches,
            upload_parallelism=self._settings.upload_parallelism,
        )
        pool = GlobalWorkerPool(config, client_factory=self._client_factory)
        self._pool = pool

        await pool.start()
        pool.run(notify=notify, on_throttle=on_throttle)
        await notify(
            f"▶️ Boshlandi: {self._settings.upload_workers} worker, {total_batches_all} batch jami"
        )

        # ─── Sequential round-robin: w0 → w1 → w2 → w3 → w4 → w0 → ...
        # Bir vaqtda faqat 1 ta batch ishlanadi (Telegram'da tartib qat'iy).
        # Workerlar cycle bo'ladi — har biri navbatdagi batch'ni oladi (sessiya freshness).
        done_per_group = {gid: per_group_skipped.get(gid, 0) for gid in per_group_batches}

        # Round-robin interleave (multi-group fairness): G1[0], G2[0], G3[0], G1[1], ...
        all_tasks: list[tuple[int, object]] = []
        max_len = max(len(b) for b in per_group_batches.values())
        for i in range(max_len):
            for gid, batches in per_group_batches.items():
                if i < len(batches):
                    all_tasks.append((gid, batches[i]))

        await notify(
            f"📤 {len(all_tasks)} batch — {self._settings.upload_workers} worker "
            f"round-robin (w0 → w1 → ... → w0)"
        )

        worker_count = pool.worker_count
        for batch_idx, (gid, batch) in enumerate(all_tasks):
            if self._stop_requested:
                break

            worker_idx = batch_idx % worker_count
            await notify(f"⏳ Batch {batch_idx + 1}/{len(all_tasks)} → W{worker_idx}")

            fut = pool.submit(batch, gid, per_group_total[gid], worker_idx=worker_idx)
            try:
                ok = await fut
            except Exception:
                ok = False

            if ok:
                done_per_group[gid] += 1
                on_progress(gid, done_per_group[gid], per_group_total[gid], 0.0)
                folder_str = str(group_folders.get(gid, ""))
                save_task = asyncio.create_task(
                    asyncio.to_thread(
                        progress_store.save_progress,
                        progress_store.GroupProgress(
                            group_id=gid,
                            folder=folder_str,
                            folder_hash=progress_store.folder_signature(folder_str),
                            completed_batches=done_per_group[gid],
                            total_batches=per_group_total[gid],
                        ),
                    )
                )
                self._bg_tasks.add(save_task)
                save_task.add_done_callback(self._bg_tasks.discard)

        await pool.stop()
        self._pool = None

        if self._stop_requested:
            await notify(
                "🛑 Yuklash to'xtatildi. Saqlangan progress: keyingi safar `Davom ettirish`."
            )
            return

        # Hammasi tugadi — progressni tozalaymiz
        for gid, total in per_group_total.items():
            if done_per_group.get(gid, 0) >= total:
                progress_store.clear_group(gid)

        if not progress_store.has_resumable():
            progress_store.clear_all()
        await notify("✅ Barcha batchlar yakunlandi!")
