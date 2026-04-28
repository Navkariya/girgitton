"""Settings — muhitdan o'qiladigan konfiguratsiya (12-factor).

`SecretStr` repr'da har doim "***" ko'rsatadi — log/exception oqishidan himoya.
`Settings.load()` `.env` ni avtomatik yuklab oladi (faqat bir marta).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, Final

from dotenv import load_dotenv

from girgitton.core.constants import (
    APP_POLL_INTERVAL_SECONDS,
    DEFAULT_HTTP_PORT,
    DEFAULT_WORKERS,
    DELAY_BETWEEN_BATCHES,
    DELAY_BETWEEN_STEPS,
    LAST_BATCH_SPEED_THRESHOLD_MB_S,
    ROTATE_AFTER_N_BATCHES,
    ROTATE_AFTER_SECONDS,
    SPEED_DROP_THRESHOLD_MB_S,
    THROTTLE_SPEED_LIMIT_MB_S,
    THROTTLE_WAIT_SECONDS,
    UPLOAD_PARALLELISM_PER_BATCH,
)
from girgitton.core.errors import ConfigError

if TYPE_CHECKING:
    from pathlib import Path

_DEFAULT_SESSION_NAME: Final[str] = "girgitton_session"


class SecretStr:
    """Sirli matn obyekti — repr/str qaytarganda '***' ko'rsatadi.

    `.get()` metodi orqali real qiymatga kirish mumkin (logga yozish kerak emas).
    """

    __slots__ = ("_value",)

    def __init__(self, value: str | None) -> None:
        self._value = value or ""

    def get(self) -> str:
        return self._value

    def __bool__(self) -> bool:
        return bool(self._value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SecretStr):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return "SecretStr('***')"

    def __str__(self) -> str:
        return "***"


def _strip_comment(value: str) -> str:
    """`'5567 #neo'` → `'5567'`."""
    return value.split("#", 1)[0].strip()


def _env_str(name: str, default: str = "") -> str:
    return _strip_comment(os.getenv(name, default))


def _env_int(name: str, default: int) -> int:
    raw = _env_str(name, str(default))
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} musbat butun son bo'lishi kerak (got {raw!r})") from exc


def _env_float(name: str, default: float) -> float:
    raw = _env_str(name, str(default))
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} float bo'lishi kerak (got {raw!r})") from exc


def _env_bool(name: str, default: bool) -> bool:
    raw = _env_str(name, str(default)).lower()
    return raw in {"1", "true", "yes", "on"}


def _parse_id_set(raw: str) -> frozenset[int]:
    items: set[int] = set()
    for chunk in raw.split(","):
        clean = _strip_comment(chunk)
        if clean.isdigit():
            items.add(int(clean))
    return frozenset(items)


@dataclass(frozen=True)
class Settings:
    """Loyiha sozlamalari (immutable)."""

    # ─── Telegram ───────────────────────────────────────────────────────────
    api_id: int
    api_hash: SecretStr
    bot_token: SecretStr
    session_name: str = _DEFAULT_SESSION_NAME

    # ─── Ruxsatlar ──────────────────────────────────────────────────────────
    owner_id: int = 0
    group_id: int = 0
    allowed_users: frozenset[int] = field(default_factory=frozenset)

    # ─── HTTP API ───────────────────────────────────────────────────────────
    api_secret: SecretStr = field(default_factory=lambda: SecretStr(""))
    public_domain: str = ""
    http_port: int = DEFAULT_HTTP_PORT

    # ─── Storage ────────────────────────────────────────────────────────────
    redis_url: str | None = None

    # ─── Upload ─────────────────────────────────────────────────────────────
    upload_workers: int = DEFAULT_WORKERS
    upload_parallelism: int = UPLOAD_PARALLELISM_PER_BATCH
    rotate_after_n_batches: int = ROTATE_AFTER_N_BATCHES
    rotate_after_seconds: int = ROTATE_AFTER_SECONDS
    speed_drop_threshold: float = SPEED_DROP_THRESHOLD_MB_S
    last_batch_speed_threshold: float = LAST_BATCH_SPEED_THRESHOLD_MB_S
    throttle_speed_limit: float = THROTTLE_SPEED_LIMIT_MB_S
    throttle_wait_seconds: int = THROTTLE_WAIT_SECONDS
    delay_between_steps: float = DELAY_BETWEEN_STEPS
    delay_between_batches: float = DELAY_BETWEEN_BATCHES
    poll_interval_seconds: float = APP_POLL_INTERVAL_SECONDS

    # ─── Logging ────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_json: bool = True

    # ─── Lifecycle ──────────────────────────────────────────────────────────

    @classmethod
    def load(cls, env_file: Path | str | None = None) -> Settings:
        """Muhitdan o'qiydi (`.env` avtomatik yuklanadi)."""
        if env_file is not None:
            load_dotenv(env_file, override=True)
        else:
            load_dotenv(override=False)

        owner = _env_int("OWNER_ID", 0)
        group = _env_str("GROUP_ID")
        group_id = int(group) if group.lstrip("-").isdigit() else 0

        return cls(
            api_id=_env_int("API_ID", 0),
            api_hash=SecretStr(_env_str("API_HASH")),
            bot_token=SecretStr(_env_str("BOT_TOKEN")),
            owner_id=owner,
            group_id=group_id,
            allowed_users=_parse_id_set(_env_str("ALLOWED_USERS")),
            api_secret=SecretStr(_env_str("API_SECRET")),
            public_domain=_env_str("RAILWAY_PUBLIC_DOMAIN"),
            http_port=_env_int("PORT", DEFAULT_HTTP_PORT),
            redis_url=_env_str("REDIS_URL") or None,
            upload_workers=_env_int("UPLOAD_WORKERS", DEFAULT_WORKERS),
            upload_parallelism=_env_int("UPLOAD_PARALLELISM", UPLOAD_PARALLELISM_PER_BATCH),
            rotate_after_n_batches=_env_int("ROTATE_AFTER_N_BATCHES", ROTATE_AFTER_N_BATCHES),
            rotate_after_seconds=_env_int("ROTATE_AFTER_SECONDS", ROTATE_AFTER_SECONDS),
            speed_drop_threshold=_env_float("SPEED_DROP_THRESHOLD", SPEED_DROP_THRESHOLD_MB_S),
            last_batch_speed_threshold=_env_float(
                "LAST_BATCH_SPEED_THRESHOLD", LAST_BATCH_SPEED_THRESHOLD_MB_S
            ),
            throttle_speed_limit=_env_float("THROTTLE_SPEED_LIMIT", THROTTLE_SPEED_LIMIT_MB_S),
            throttle_wait_seconds=_env_int("THROTTLE_WAIT_SECONDS", THROTTLE_WAIT_SECONDS),
            delay_between_steps=_env_float("DELAY_BETWEEN_STEPS", DELAY_BETWEEN_STEPS),
            delay_between_batches=_env_float("DELAY_BETWEEN_BATCHES", DELAY_BETWEEN_BATCHES),
            log_level=_env_str("LOG_LEVEL", "INFO").upper() or "INFO",
            log_json=_env_bool("LOG_JSON", True),
        )

    def validate(self) -> None:
        """Majburiy maydonlarni tekshiradi."""
        if not self.api_id:
            raise ConfigError("API_ID sozlanmagan")
        if not self.api_hash:
            raise ConfigError("API_HASH sozlanmagan")
        if not self.bot_token:
            raise ConfigError("BOT_TOKEN sozlanmagan")
        if not self.api_secret:
            raise ConfigError(
                "API_SECRET sozlanmagan — "
                "`python -c 'import secrets; print(secrets.token_hex(32))'`"
            )

    def public_url(self) -> str:
        """Tashqi URL (Railway domeni yoki localhost)."""
        if self.public_domain:
            return f"https://{self.public_domain}"
        return f"http://localhost:{self.http_port}"

    def to_safe_dict(self) -> dict[str, Any]:
        """Sirlarsiz ko'rinish (log/diagnostika uchun)."""
        out: dict[str, Any] = {}
        for f in fields(self):
            v = getattr(self, f.name)
            out[f.name] = "***" if isinstance(v, SecretStr) else v
        return out
