"""Structured logging — JSON formatter + secret filter.

`SecretFilter` LogRecord da bo'lishi mumkin bo'lgan bot tokeni / api hash kabi
ma'lumotlarni regex orqali topib `***` ga almashtiradi.
"""

from __future__ import annotations

import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

try:
    from pythonjsonlogger.jsonlogger import JsonFormatter
except ImportError:  # pragma: no cover
    JsonFormatter = None  # type: ignore[assignment, misc]


_LOGGER_NAME = "girgitton"

# Bot token: 10+ raqam : 35+ char
_BOT_TOKEN_RE = re.compile(r"\d{6,12}:[A-Za-z0-9_-]{30,}")
# API hash: 32 hex
_API_HASH_RE = re.compile(r"\b[a-f0-9]{32}\b")


class SecretFilter(logging.Filter):
    """LogRecord matnidan tokenlarni `***` bilan almashtiradi."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:  # pragma: no cover
            return True

        cleaned = _BOT_TOKEN_RE.sub("***bot_token***", msg)
        cleaned = _API_HASH_RE.sub("***api_hash***", cleaned)

        if cleaned != msg:
            record.msg = cleaned
            record.args = ()
        return True


def _make_text_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _make_json_formatter() -> logging.Formatter:
    if JsonFormatter is None:
        return _make_text_formatter()
    return JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "ts", "levelname": "level"},
    )


def setup_logging(
    *,
    level: str = "INFO",
    json: bool = True,
    log_dir: Path | None = None,
    file_name: str = "girgitton.log",
) -> logging.Logger:
    """Logger ni sozlaydi.

    Konsol + faylga (RotatingFileHandler 10 MB × 5) yozadi.
    """
    formatter = _make_json_formatter() if json else _make_text_formatter()
    secret_filter = SecretFilter()

    # Reconfigure stdout for UTF-8 on Windows
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:  # pragma: no cover
                pass

    handlers: list[logging.Handler] = []

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    console.addFilter(secret_filter)
    handlers.append(console)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / file_name,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(secret_filter)
        handlers.append(file_handler)

    root = logging.getLogger()
    root.setLevel(level.upper())
    # Eski handlerlarni tozalaymiz
    for h in list(root.handlers):
        root.removeHandler(h)
    for h in handlers:
        root.addHandler(h)

    return logging.getLogger(_LOGGER_NAME)


def get_logger(name: str | None = None) -> logging.Logger:
    """Modul-darajasidagi logger qaytaradi."""
    if not name:
        return logging.getLogger(_LOGGER_NAME)
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")


def log_safe_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Diagnostika dict'idan tokenlarni filtrlaydi."""
    out: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, str):
            cleaned = _BOT_TOKEN_RE.sub("***", v)
            cleaned = _API_HASH_RE.sub("***", cleaned)
            out[k] = cleaned
        else:
            out[k] = v
    return out
