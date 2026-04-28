"""Markazlashtirilgan ilova ma'lumotlari yo'li.

Tartib (yuqoridan pastga):
1. ENV `GIRGITTON_DATA_DIR` — installer yoki foydalanuvchi tomonidan o'rnatilgan
2. PyInstaller frozen .exe yonida `data/` subdir (installer pattern)
3. Fallback: `~/.girgitton/` (portable / dev)

Migratsiya: ilk marta yangi `data_dir` bo'sh va eski `~/.girgitton/` to'la bo'lsa,
fayllar avtomatik ko'chiriladi (foydalanuvchi qayta ulanishi shart emas).
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_LEGACY_HOME_DIR = Path.home() / ".girgitton"

# Migration ko'chiriladigan fayllar/papkalar
_MIGRATABLE_ITEMS = (
    "credentials.enc",
    "credentials.key",
    "state.json",
    "progress.json",
    "girgitton.log",
    "desktop_app.log",
    "sessions",  # papka (worker session fayllari)
)


def _candidate_from_frozen_exe() -> Path | None:
    """PyInstaller `--onedir` rejimida `.exe` yonida `data/` subdir."""
    if not getattr(sys, "frozen", False):
        return None
    exe_path = Path(sys.executable)
    exe_dir = exe_path.parent
    candidate = exe_dir / "data"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        # Yozish huquqini sinash (read-only Program Files'dan saqlanish)
        probe = candidate / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return candidate
    except OSError as exc:
        logger.debug("frozen exe yonida data/ yarata bo'lmadi: %s", exc)
        return None


_cached_data_dir: Path | None = None


def get_data_dir() -> Path:
    """Ilova data papkasini qaytaradi (mavjud bo'lmasa yaratadi).

    Birinchi chaqiruvdan so'ng natija kesh'lanadi.
    """
    global _cached_data_dir
    if _cached_data_dir is not None:
        return _cached_data_dir

    # 1) ENV
    env_dir = os.environ.get("GIRGITTON_DATA_DIR", "").strip()
    if env_dir:
        d = Path(env_dir)
        d.mkdir(parents=True, exist_ok=True)
        _cached_data_dir = d
        logger.info("Data dir (ENV): %s", d)
        _maybe_migrate(d)
        return d

    # 2) Frozen .exe yonida `data/`
    frozen = _candidate_from_frozen_exe()
    if frozen is not None:
        _cached_data_dir = frozen
        logger.info("Data dir (installed): %s", frozen)
        _maybe_migrate(frozen)
        return frozen

    # 3) Fallback: home (portable / dev)
    _LEGACY_HOME_DIR.mkdir(parents=True, exist_ok=True)
    _cached_data_dir = _LEGACY_HOME_DIR
    logger.info("Data dir (home fallback): %s", _LEGACY_HOME_DIR)
    return _LEGACY_HOME_DIR


def reset_cache() -> None:
    """Test maqsadlari uchun keshni tozalash."""
    global _cached_data_dir
    _cached_data_dir = None


# ─── Subdir helperlari (har modul shu funksiyalarni ishlatadi) ──────────────


def get_sessions_dir() -> Path:
    d = get_data_dir() / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_logs_dir() -> Path:
    return get_data_dir()


def get_credentials_path() -> Path:
    return get_data_dir() / "credentials.enc"


def get_credentials_key_path() -> Path:
    return get_data_dir() / "credentials.key"


def get_state_path() -> Path:
    return get_data_dir() / "state.json"


def get_progress_path() -> Path:
    return get_data_dir() / "progress.json"


# ─── Migration: eski lokatsiyadan yangiga ──────────────────────────────────


def _maybe_migrate(target: Path) -> None:
    """Yangi `target` bo'sh va eski `~/.girgitton/` to'la bo'lsa, ko'chiramiz.

    Eski papkani o'chirmaymiz — foydalanuvchi qaror qiladi (yoki uninstaller).
    """
    if target == _LEGACY_HOME_DIR:
        return  # bir xil joy
    if not _LEGACY_HOME_DIR.exists():
        return  # eski yo'q

    # Faqat target bo'sh bo'lsa (birinchi marta)
    has_existing = any((target / item).exists() for item in _MIGRATABLE_ITEMS)
    if has_existing:
        return  # allaqachon ko'chgan yoki ishlatilmoqda

    migrated = 0
    for item in _MIGRATABLE_ITEMS:
        src = _LEGACY_HOME_DIR / item
        if not src.exists():
            continue
        dst = target / item
        try:
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            migrated += 1
        except OSError as exc:
            logger.warning("Migration failed for %s: %s", item, exc)

    if migrated > 0:
        logger.info("Migrated %d items from %s → %s", migrated, _LEGACY_HOME_DIR, target)
