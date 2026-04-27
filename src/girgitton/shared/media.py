"""Media fayl skaneri va batch utilitlari."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from girgitton.core.constants import BATCH_SIZE, MEDIA_EXTENSIONS
from girgitton.core.errors import GirgittonError
from girgitton.core.models import MediaBatch

if TYPE_CHECKING:
    from collections.abc import Iterable


class MediaScanError(GirgittonError):
    """Media papkani skanerlashda xatolik."""


def scan_media_folder(folder: Path | str, *, recursive: bool = False) -> tuple[Path, ...]:
    """Papkadagi media fayllarni topadi va nom bo'yicha tartiblaydi.

    Args:
        folder: skaner qilinadigan papka yo'li.
        recursive: ichki papkalarni ham qo'shish.

    Returns:
        Tartiblangan media fayllar tuple'i.

    Raises:
        MediaScanError: agar papka mavjud bo'lmasa yoki o'qib bo'lmasa.
    """
    path = Path(folder)
    if not path.exists():
        raise MediaScanError(f"Papka topilmadi: {path}")
    if not path.is_dir():
        raise MediaScanError(f"Bu fayl, papka emas: {path}")

    iterator = path.rglob("*") if recursive else path.iterdir()
    files = [
        p
        for p in iterator
        if p.is_file() and p.suffix.lower() in MEDIA_EXTENSIONS and not p.name.startswith(".")
    ]
    return tuple(sorted(files, key=lambda p: p.name.lower()))


def make_batches(
    files: Iterable[Path], batch_size: int = BATCH_SIZE, start_idx: int = 1
) -> tuple[MediaBatch, ...]:
    """Fayllarni `batch_size` o'lchamli MediaBatch tuple'iga ajratadi."""
    files_list = list(files)
    out: list[MediaBatch] = []
    for offset in range(0, len(files_list), batch_size):
        chunk = tuple(files_list[offset : offset + batch_size])
        if chunk:
            out.append(MediaBatch(idx=start_idx + (offset // batch_size), files=chunk))
    return tuple(out)


def file_sha256(path: Path, *, chunk_size: int = 65536) -> str:
    """Fayl uchun SHA-256 hash (resume / cache uchun)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()
