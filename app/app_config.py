"""
Desktop App lokal config saqlash va o'qish.

Config fayl: ~/.girgitton_app.json
Bot /setup buyrug'i orqali olingan config.json import qilinadi.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("girgitton")

_CONFIG_PATH = Path.home() / ".girgitton_app.json"


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


def import_from_file(path: str) -> dict[str, Any]:
    """Bot /setup faylini parse qiladi va lokal saqlaydi."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"bot_token", "api_id", "api_hash", "api_url", "api_secret", "group_id", "setup_token"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Config faylida yetishmaydi: {missing}")
    save(data)
    return data


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
