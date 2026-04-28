"""Loyihaning o'zgarmas konstantalari."""

from __future__ import annotations

from typing import Final

# ─── Media kengaytmalari ─────────────────────────────────────────────────────
IMAGE_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
)
VIDEO_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
)
MEDIA_EXTENSIONS: Final[frozenset[str]] = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

# ─── Yuborish parametrlari ───────────────────────────────────────────────────
BATCH_SIZE: Final[int] = 5  # bir albomda nechta fayl
DEFAULT_WORKERS: Final[int] = 3
MAX_WORKERS: Final[int] = 5  # Telethon bot session ban xavfidan himoya

DELAY_BETWEEN_STEPS: Final[float] = 0.3  # media album ↔ document album orasidagi
DELAY_BETWEEN_BATCHES: Final[float] = 1.0  # batchlar orasidagi pauza
UPLOAD_PARALLELISM_PER_BATCH: Final[int] = 5  # bir batch ichida fayllar parallel

# ─── Rotatsiya / Throttle ────────────────────────────────────────────────────
ROTATE_AFTER_N_BATCHES: Final[int] = 15
ROTATE_AFTER_SECONDS: Final[int] = 300
# Avg(3 batch) tezligi shu ostiga tushsa rotate (sekin trend)
SPEED_DROP_THRESHOLD_MB_S: Final[float] = 0.5
# Oxirgi BITTA batch tezligi shu ostida bo'lsa darhol rotate (v1/v2 ga o'xshash)
LAST_BATCH_SPEED_THRESHOLD_MB_S: Final[float] = 0.9
# Throttle (FATAL sekin tarmoq) — faqat haqiqatdan dead bo'lganda 30 daq kut
THROTTLE_SPEED_LIMIT_MB_S: Final[float] = 0.02
THROTTLE_WAIT_SECONDS: Final[int] = 1800  # 30 daqiqa

# ─── Pair code ───────────────────────────────────────────────────────────────
PAIR_CODE_LENGTH: Final[int] = 6
PAIR_CODE_TTL_SECONDS: Final[int] = 300  # 5 daqiqa
PAIR_BRUTE_FORCE_LIMIT: Final[int] = 10  # daqiqada urinishlar soni

# ─── HMAC ────────────────────────────────────────────────────────────────────
HMAC_TIMESTAMP_SKEW_SECONDS: Final[int] = 60  # ±60s

# ─── Polling ─────────────────────────────────────────────────────────────────
APP_POLL_INTERVAL_SECONDS: Final[float] = 5.0
APP_STATUS_TTL_SECONDS: Final[int] = 300

# ─── Network ─────────────────────────────────────────────────────────────────
DEFAULT_HTTP_PORT: Final[int] = 8080
HTTP_REQUEST_TIMEOUT_SECONDS: Final[float] = 10.0
HTTP_RATE_LIMIT_PER_MINUTE: Final[int] = 60
