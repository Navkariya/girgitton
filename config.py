"""
Girgitton konfiguratsiyasi.
.env faylidan (Railway va lokal) sozlamalarni o'qiydi.
Desktop App uchun load_from_app_config() funksiyasi ham mavjud.
"""

import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("girgitton")


def _strip_comment(value: str) -> str:
    """'5567796386 #neo' → '5567796386'"""
    return value.split("#")[0].strip()


# ── Telegram API ──────────────────────────────────────────────────────────
API_ID: int = int(_strip_comment(os.getenv("API_ID", "0")) or "0")
API_HASH: str = _strip_comment(os.getenv("API_HASH", ""))
BOT_TOKEN: str = _strip_comment(os.getenv("BOT_TOKEN", ""))
SESSION_NAME: str = "girgitton_session"

# ── Ruxsatlar ─────────────────────────────────────────────────────────────
_raw_owner = _strip_comment(os.getenv("OWNER_ID", "0"))
OWNER_ID: int = int(_raw_owner) if _raw_owner.isdigit() else 0

_raw_group = _strip_comment(os.getenv("GROUP_ID", ""))
GROUP_ID: int = int(_raw_group) if _raw_group.lstrip("-").isdigit() else 0
CHAT_ID: int = GROUP_ID

_raw_allowed = _strip_comment(os.getenv("ALLOWED_USERS", ""))
ALLOWED_USERS: frozenset[int] = frozenset(
    int(part)
    for raw in _raw_allowed.split(",")
    if (part := _strip_comment(raw)).isdigit()
)

# ── Yuborish sozlamalari ──────────────────────────────────────────────────
BATCH_SIZE: int = 5
DELAY_BETWEEN_BATCHES: float = 2.0
DELAY_BETWEEN_STEPS: float = 1.0

# ── Upload Worker Pool ────────────────────────────────────────────────────
UPLOAD_WORKERS: int = int(os.getenv("UPLOAD_WORKERS", "3"))
ROTATE_AFTER_N_BATCHES: int = int(os.getenv("ROTATE_AFTER_N_BATCHES", "15"))
ROTATE_AFTER_SECONDS: int = int(os.getenv("ROTATE_AFTER_SECONDS", "300"))
SPEED_DROP_THRESHOLD: float = float(os.getenv("SPEED_DROP_THRESHOLD", "0.10"))
THROTTLE_SPEED_LIMIT: float = float(os.getenv("THROTTLE_SPEED_LIMIT", "0.05"))
THROTTLE_WAIT_SECONDS: int = int(os.getenv("THROTTLE_WAIT_SECONDS", "1800"))

# ── Media kengaytmalari ───────────────────────────────────────────────────
IMAGE_EXTENSIONS: frozenset = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp"})
VIDEO_EXTENSIONS: frozenset = frozenset({".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"})
MEDIA_EXTENSIONS: frozenset = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def load_from_app_config(cfg: dict[str, Any]) -> None:
    """Desktop App config.json dan sozlamalarni yuklaydi."""
    global API_ID, API_HASH, BOT_TOKEN, GROUP_ID, CHAT_ID, UPLOAD_WORKERS
    API_ID = cfg.get("api_id", API_ID)
    API_HASH = cfg.get("api_hash", API_HASH)
    BOT_TOKEN = cfg.get("bot_token", BOT_TOKEN)
    GROUP_ID = cfg.get("group_id", GROUP_ID)
    CHAT_ID = GROUP_ID
    UPLOAD_WORKERS = cfg.get("upload_workers", UPLOAD_WORKERS)


def validate() -> None:
    if not API_ID or not API_HASH:
        print("XATO: API_ID va API_HASH sozlanmagan!")
        sys.exit(1)
    if not BOT_TOKEN:
        print("XATO: BOT_TOKEN sozlanmagan!")
        sys.exit(1)
    if OWNER_ID == 0:
        logger.warning(
            "OWNER_ID sozlanmagan — guruhda BARCHA foydalanuvchilar "
            "buyruqlarni ishlatishi mumkin!"
        )
