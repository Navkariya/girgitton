"""
Yordamchi funksiyalar: logging, fayl skanerlash, list bo'lish.
"""

import logging
from pathlib import Path
from typing import List

from config import MEDIA_EXTENSIONS


def setup_logging() -> logging.Logger:
    """Logger ni sozlaydi — konsolga va faylga yozadi."""
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    handlers: list = [
        logging.StreamHandler(),
        logging.FileHandler("girgitton.log", encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)
    return logging.getLogger("girgitton")


def scan_media_files(folder: str) -> List[Path]:
    """
    Papkadagi barcha media fayllarni topadi.
    Fayl nomi bo'yicha o'sish tartibida saralaydi.
    Pastki papkalar hisobga olinmaydi.
    """
    folder_path = Path(folder)
    files = [
        f
        for f in folder_path.iterdir()
        if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS
    ]
    return sorted(files, key=lambda f: f.name.lower())


def chunked(lst: list, size: int) -> List[list]:
    """Ro'yxatni 'size' o'lchamli bo'laklarga ajratadi."""
    return [lst[i : i + size] for i in range(0, len(lst), size)]
