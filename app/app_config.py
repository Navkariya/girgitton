"""
Desktop App lokal config saqlash va o'qish.

Config fayl: ~/.girgitton/credentials.json
Bu fayl faqat auto-pair yoki pair code orqali olingan credentials saqlaydi.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("girgitton")

_CONFIG_DIR = Path.home() / ".girgitton"
_CONFIG_DIR.mkdir(exist_ok=True)
_CONFIG_PATH = _CONFIG_DIR / "credentials.json"


def load() -> Optional[dict[str, Any]]:
    if not _CONFIG_PATH.exists():
        return None
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Config o'qib bo'lmadi: %s", exc)
        return None


def save(cfg: dict[str, Any]) -> None:
    try:
        _CONFIG_PATH.write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.error("Config saqlab bo'lmadi: %s", exc)
        raise


def clear() -> None:
    """Saqlangan credentials'larni o'chiradi (chiqish / unpair uchun)."""
    if _CONFIG_PATH.exists():
        try:
            _CONFIG_PATH.unlink()
        except Exception as exc:
            logger.warning("Credentials o'chirib bo'lmadi: %s", exc)


def get(key: str, default: Any = None) -> Any:
    cfg = load()
    return cfg.get(key, default) if cfg else default


def set_display_name(name: str) -> None:
    cfg = load() or {}
    cfg["display_name"] = name
    save(cfg)


def set_last_folder(folder: str) -> None:
    cfg = load() or {}
    cfg["last_folder"] = folder
    save(cfg)
