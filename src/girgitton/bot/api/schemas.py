"""Request/Response DTO sxemalari (light-weight, dataclass)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from girgitton.core.errors import GirgittonError

_TOKEN_RE = re.compile(r"^[a-zA-Z0-9]{8,64}$")


class SchemaError(GirgittonError):
    """Sxema validatsiyasi muvaffaqiyatsiz tugadi."""


@dataclass(frozen=True, slots=True)
class ConnectInitRequest:
    token: str

    @classmethod
    def parse(cls, raw: dict[str, object]) -> ConnectInitRequest:
        token = str(raw.get("token", "")).strip()
        if not _TOKEN_RE.match(token):
            raise SchemaError("`token` 8..64 alfanumerik belgi bo'lishi kerak")
        return cls(token=token)


@dataclass(frozen=True, slots=True)
class ConnectClaimRequest:
    token: str

    @classmethod
    def parse(cls, raw: dict[str, object]) -> ConnectClaimRequest:
        token = str(raw.get("token", "")).strip()
        if not _TOKEN_RE.match(token):
            raise SchemaError("`token` 8..64 alfanumerik belgi bo'lishi kerak")
        return cls(token=token)


@dataclass(frozen=True, slots=True)
class StatusRequest:
    user_id: int
    chat_id: int
    batch: int
    total: int
    speed: float

    @classmethod
    def parse(cls, raw: dict[str, object]) -> StatusRequest:
        try:
            return cls(
                user_id=int(raw["user_id"]),  # type: ignore[arg-type]
                chat_id=int(raw.get("chat_id", 0)),  # type: ignore[arg-type]
                batch=int(raw.get("batch", 0)),  # type: ignore[arg-type]
                total=int(raw.get("total", 0)),  # type: ignore[arg-type]
                speed=float(raw.get("speed", 0.0)),  # type: ignore[arg-type]
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SchemaError(f"Status DTO yaroqsiz: {exc}") from exc
