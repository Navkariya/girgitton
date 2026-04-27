"""Storage Repository Protocol — bot va app uchun yagona interfeys.

Adapter mustaqil bo'lib, Redis (asosiy) yoki JSON fayl (fallback) bilan
ishlay oladi.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageRepository(Protocol):
    """Asosiy storage interfeysi."""

    async def init(self) -> None:
        """Ulanishni tekshiradi (ping yoki fayl yaratish)."""
        ...

    async def close(self) -> None:
        """Ulanishni yopadi."""
        ...

    # ─── String K/V ─────────────────────────────────────────────────────────

    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, *, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def getdel(self, key: str) -> str | None:
        """Get + delete atomik (pair code uchun)."""
        ...

    # ─── Hash ───────────────────────────────────────────────────────────────

    async def hset(self, key: str, field: str, value: str) -> None: ...
    async def hget(self, key: str, field: str) -> str | None: ...
    async def hdel(self, key: str, field: str) -> None: ...
    async def hgetall(self, key: str) -> dict[str, str]: ...

    # ─── Set ────────────────────────────────────────────────────────────────

    async def sadd(self, key: str, *members: str) -> None: ...
    async def srem(self, key: str, *members: str) -> None: ...
    async def smembers(self, key: str) -> set[str]: ...

    # ─── Counter (rate limit) ───────────────────────────────────────────────

    async def incr_with_ttl(self, key: str, ttl: int) -> int:
        """Counter ni 1 ga oshiradi va TTL belgilaydi (yangi bo'lsa)."""
        ...
