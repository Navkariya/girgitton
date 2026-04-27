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

from girgitton.core.constants import DELAY_BETWEEN_STEPS
from girgitton.core.errors import UploadError

if TYPE_CHECKING:
    from pathlib import Path

    from girgitton.core.models import MediaBatch

logger = logging.getLogger(__name__)

NotifyFn = Callable[[str], Awaitable[None]]


async def upload_files_once(client: object, files: tuple[Path, ...]) -> list[object]:
    """Fayllarni Telegramga BIR MARTA yuklaydi va InputFile ro'yxatini qaytaradi.

    Telethon'da `client.upload_file()` async metod — InputFile yoki InputFileBig
    qaytaradi. Bu obyekt bir necha marta `send_file` da ishlatilishi mumkin.
    """
    uploaded: list[object] = []
    for path in files:
        if not path.exists():
            raise UploadError(f"Fayl topilmadi: {path}")
        # Telethon TelegramClient.upload_file str path qabul qiladi
        result = await client.upload_file(str(path))  # type: ignore[attr-defined]
        uploaded.append(result)
    return uploaded


async def send_album_pair(
    client: object,
    chat_id: int,
    batch: MediaBatch,
    total_batches: int,
    *,
    delay_between_steps: float = DELAY_BETWEEN_STEPS,
) -> None:
    """Bir batch uchun media+document album yuboradi.

    Order:
      A) media album (preview)         force_document=False
      B) DELAY_BETWEEN_STEPS pauza
      C) document album (fayl)         force_document=True
    """
    n = batch.size
    media_caption = f"📸 Qism {batch.idx}/{total_batches} — Media ({n} ta)"
    doc_caption = f"📁 Qism {batch.idx}/{total_batches} — Documents ({n} ta)"

    logger.info("Batch %d/%d: yuklash boshlanmoqda", batch.idx, total_batches)
    uploaded = await upload_files_once(client, batch.files)

    # ─── A: media album ────────────────────────────────────────────────
    captions = [media_caption] + [""] * (n - 1)
    await client.send_file(  # type: ignore[attr-defined]
        chat_id,
        uploaded,
        caption=captions,
        force_document=False,
    )
    logger.debug("Batch %d: media album OK", batch.idx)

    await asyncio.sleep(delay_between_steps)

    # ─── B: document album ─────────────────────────────────────────────
    captions = [doc_caption] + [""] * (n - 1)
    await client.send_file(  # type: ignore[attr-defined]
        chat_id,
        uploaded,
        caption=captions,
        force_document=True,
    )
    logger.info("Batch %d/%d: document album OK ✓", batch.idx, total_batches)


def chunked_paths(files: list[Path], size: int) -> list[list[Path]]:
    """Yordamchi: `files` ni `size` o'lchamli ro'yxatlarga ajratadi."""
    return [files[i : i + size] for i in range(0, len(files), size)]
