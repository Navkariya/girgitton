"""5-batch yuborish: bitta upload, ikki marta send (media + document).

Markaziy strategiya:
  1. Har 5 ta fayl uchun `client.upload_file()` BIR MARTA bajariladi
  2. Olingan `InputFile` ro'yxatlari `send_file` ichida ikki marta ishlatiladi:
     - force_document=False (media album / preview)
     - force_document=True  (document album / fayl)
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from girgitton.core.constants import DELAY_BETWEEN_STEPS, UPLOAD_PARALLELISM_PER_BATCH
from girgitton.core.errors import UploadError

if TYPE_CHECKING:
    from pathlib import Path

    from girgitton.core.models import MediaBatch

logger = logging.getLogger(__name__)

NotifyFn = Callable[[str], Awaitable[None]]

_UPLOAD_PART_SIZE_KB = 512  # Telethon default 64 KB → 512 KB (8x kam round-trip)


async def upload_files_once(
    client: object,
    files: tuple[Path, ...],
    *,
    parallelism: int = UPLOAD_PARALLELISM_PER_BATCH,
    part_size_kb: int = _UPLOAD_PART_SIZE_KB,
) -> list[object]:
    """Fayllarni Telegramga PARALLEL yuklaydi va InputFile ro'yxatini qaytaradi.

    Optimizatsiyalar:
    - `parallelism` ta fayl bir vaqtda (`asyncio.Semaphore`) — sequential upload'dan
      3-5× tezroq.
    - `part_size_kb=512` — Telethon default 64 KB → 512 KB. Har fayl uchun 8× kam
      HTTP round-trip — katta fayllarda eng sezilarli yutuq.
    """
    if not files:
        return []

    for path in files:
        if not path.exists():
            raise UploadError(f"Fayl topilmadi: {path}")

    sem = asyncio.Semaphore(max(1, parallelism))

    async def _upload_one(path: Path) -> object:
        async with sem:
            return await client.upload_file(  # type: ignore[attr-defined]
                str(path),
                part_size_kb=part_size_kb,
            )

    return list(await asyncio.gather(*(_upload_one(p) for p in files)))


async def send_album_pair(
    client: object,
    chat_id: int,
    batch: MediaBatch,
    total_batches: int,
    *,
    delay_between_steps: float = DELAY_BETWEEN_STEPS,
    upload_parallelism: int = UPLOAD_PARALLELISM_PER_BATCH,
) -> None:
    """Bir batch uchun media+document album yuboradi.

    Order:
      A) media album (preview)         force_document=False
      B) DELAY_BETWEEN_STEPS pauza
      C) document album (fayl)         force_document=True
    """
    n = batch.size
    # Telegram'da hech qanday caption matni qoldirmaymiz (toza media album)
    blank_captions = [""] * n

    logger.info("Batch %d/%d: yuklash boshlanmoqda (parallel)", batch.idx, total_batches)
    uploaded = await upload_files_once(client, batch.files, parallelism=upload_parallelism)

    # ─── A: media album (preview) — captionsiz ────────────────────────
    await client.send_file(  # type: ignore[attr-defined]
        chat_id,
        uploaded,
        caption=blank_captions,
        force_document=False,
    )
    logger.debug("Batch %d: media album OK", batch.idx)

    await asyncio.sleep(delay_between_steps)

    # ─── B: document album (fayl) — captionsiz ────────────────────────
    await client.send_file(  # type: ignore[attr-defined]
        chat_id,
        uploaded,
        caption=blank_captions,
        force_document=True,
    )
    logger.info("Batch %d/%d: document album OK ✓", batch.idx, total_batches)


def chunked_paths(files: list[Path], size: int) -> list[list[Path]]:
    """Yordamchi: `files` ni `size` o'lchamli ro'yxatlarga ajratadi."""
    return [files[i : i + size] for i in range(0, len(files), size)]
