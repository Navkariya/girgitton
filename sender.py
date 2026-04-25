"""
Media fayllarni Telegram guruhiga yuborish logikasi.

Har bir 5 talik qism uchun qat'iy tartib:
  1. Avval 5 ta fayl MEDIA ALBUM sifatida (preview ko'rinishida)
  2. Keyin xuddi o'sha 5 ta fayl DOCUMENT ALBUM sifatida (fayl ko'rinishida)
"""

import asyncio
import logging
from pathlib import Path
from typing import Awaitable, Callable, List

from telethon import TelegramClient

from config import BATCH_SIZE, DELAY_BETWEEN_BATCHES, DELAY_BETWEEN_STEPS
from helpers import chunked

logger = logging.getLogger("girgitton")


async def _send_album(
    client: TelegramClient,
    chat_id: int,
    files: List[Path],
    force_document: bool,
    caption: str,
) -> None:
    """
    Bir album (media yoki document) yuboradi.
    force_document=False  → media preview (rasm/video ko'rinishi)
    force_document=True   → document/fayl ko'rinishi
    """
    file_paths = [str(f) for f in files]

    # Caption faqat birinchi faylga qo'yiladi (Telegram chegarasi)
    captions: List[str] = [caption] + [""] * (len(files) - 1)

    await client.send_file(
        chat_id,
        file_paths,
        captions=captions,
        force_document=force_document,
    )


async def send_all_media(
    client: TelegramClient,
    chat_id: int,
    media_files: List[Path],
    notify: Callable[[str], Awaitable[None]],
    stop_flag: "list[bool]",
) -> None:
    """
    Barcha media fayllarni qismlar bo'yicha yuboradi.

    stop_flag — [False] ro'yxati; tashqaridan True ga o'zgartirilsa to'xtaydi.
    """
    batches = chunked(media_files, BATCH_SIZE)
    total_batches = len(batches)
    total_files = len(media_files)

    logger.info(f"Yuborish boshlandi: {total_files} ta fayl, {total_batches} ta qism")

    for batch_idx, batch in enumerate(batches, start=1):
        if stop_flag[0]:
            await notify("🛑 Yuborish foydalanuvchi tomonidan to'xtatildi.")
            logger.info("Yuborish to'xtatildi.")
            return

        batch_names = ", ".join(f.name for f in batch)
        logger.info(f"Qism {batch_idx}/{total_batches}: {batch_names}")

        # ── 1-bosqich: Media album ────────────────────────────────────────
        logger.info(f"  → Media album yuborilmoqda ({len(batch)} ta fayl)")
        try:
            await _send_album(
                client,
                chat_id,
                batch,
                force_document=False,
                caption=f"📸 Qism {batch_idx}/{total_batches} — Media ({len(batch)} ta)",
            )
        except Exception as exc:
            logger.error(f"Media album xatolik (qism {batch_idx}): {exc}")
            await notify(f"⚠️ Qism {batch_idx} media album xatolik: {exc}")

        await asyncio.sleep(DELAY_BETWEEN_STEPS)

        if stop_flag[0]:
            await notify("🛑 Yuborish to'xtatildi.")
            return

        # ── 2-bosqich: Document album ─────────────────────────────────────
        logger.info(f"  → Document album yuborilmoqda ({len(batch)} ta fayl)")
        try:
            await _send_album(
                client,
                chat_id,
                batch,
                force_document=True,
                caption=f"📁 Qism {batch_idx}/{total_batches} — Documents ({len(batch)} ta)",
            )
        except Exception as exc:
            logger.error(f"Document album xatolik (qism {batch_idx}): {exc}")
            await notify(f"⚠️ Qism {batch_idx} document album xatolik: {exc}")

        logger.info(f"Qism {batch_idx}/{total_batches} tugadi ✓")

        # Keyingi qism oldidan pauza (flood limit himoyasi)
        if batch_idx < total_batches:
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)

    logger.info("Barcha fayllar yuborildi.")
