"""Domen modellari — frozen dataclasslar (immutable DTO)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class PairCode:
    """Pair code va unga bog'langan guruh ma'lumotlari."""

    code: str
    group_id: int
    group_title: str
    user_id: int
    expires_at: float

    def is_expired(self, now: float | None = None) -> bool:
        return (now or time.time()) >= self.expires_at

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "group_id": self.group_id,
            "group_title": self.group_title,
            "user_id": self.user_id,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PairCode:
        return cls(
            code=str(data["code"]),
            group_id=int(data["group_id"]),  # type: ignore[arg-type]
            group_title=str(data.get("group_title", "")),
            user_id=int(data["user_id"]),  # type: ignore[arg-type]
            expires_at=float(data["expires_at"]),  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class ActiveGroup:
    """Faollashtirilgan guruh."""

    id: int
    title: str

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "title": self.title}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ActiveGroup:
        return cls(
            id=int(data["id"]),  # type: ignore[arg-type]
            title=str(data.get("title", "")),
        )


@dataclass(frozen=True, slots=True)
class AppStatus:
    """Desktop App tomonidan yuboriladigan progress holati."""

    user_id: int
    chat_id: int
    batch: int
    total: int
    speed: float
    timestamp: float = field(default_factory=time.time)

    @property
    def progress_pct(self) -> int:
        return int(self.batch / self.total * 100) if self.total else 0

    def to_dict(self) -> dict[str, object]:
        return {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "batch": self.batch,
            "total": self.total,
            "speed": round(self.speed, 3),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AppStatus:
        return cls(
            user_id=int(data["user_id"]),  # type: ignore[arg-type]
            chat_id=int(data.get("chat_id", 0)),  # type: ignore[arg-type]
            batch=int(data.get("batch", 0)),  # type: ignore[arg-type]
            total=int(data.get("total", 0)),  # type: ignore[arg-type]
            speed=float(data.get("speed", 0.0)),  # type: ignore[arg-type]
            timestamp=float(data.get("timestamp", time.time())),  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class MediaBatch:
    """5 talik media bo'lagi."""

    idx: int
    files: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not self.files:
            raise ValueError("MediaBatch bo'sh bo'lmasligi kerak")

    @property
    def size(self) -> int:
        return len(self.files)

    @property
    def total_bytes(self) -> int:
        return sum(p.stat().st_size for p in self.files if p.exists())

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(p.name for p in self.files)
