"""Redis storage adapteri (redis-py asyncio)."""

from __future__ import annotations

import logging
from typing import Any

import redis.asyncio as aioredis

from girgitton.core.errors import StorageError

logger = logging.getLogger(__name__)


class RedisStorage:
    """`StorageRepository` ga mos Redis adapteri."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._client: aioredis.Redis | None = None

    async def init(self) -> None:
        try:
            self._client = aioredis.from_url(self._url, decode_responses=True)
            await self._client.ping()
            logger.info("Redis storage ulandi")
        except Exception as exc:
            raise StorageError(f"Redis ulanib bo'lmadi: {exc}") from exc

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def _c(self) -> aioredis.Redis:
        if self._client is None:
            raise StorageError("Redis ulanmagan — init() chaqirilmadi")
        return self._client

    # ─── K/V ────────────────────────────────────────────────────────────────

    async def get(self, key: str) -> str | None:
        result: Any = await self._c.get(key)
        return None if result is None else str(result)

    async def set(self, key: str, value: str, *, ttl: int | None = None) -> None:
        if ttl is not None:
            await self._c.setex(key, ttl, value)
        else:
            await self._c.set(key, value)

    async def delete(self, key: str) -> None:
        await self._c.delete(key)

    async def getdel(self, key: str) -> str | None:
        result: Any = await self._c.getdel(key)
        return None if result is None else str(result)

    # ─── Hash ───────────────────────────────────────────────────────────────

    async def hset(self, key: str, field: str, value: str) -> None:
        await self._c.hset(key, field, value)

    async def hget(self, key: str, field: str) -> str | None:
        result: Any = await self._c.hget(key, field)
        return None if result is None else str(result)

    async def hdel(self, key: str, field: str) -> None:
        await self._c.hdel(key, field)

    async def hgetall(self, key: str) -> dict[str, str]:
        result: Any = await self._c.hgetall(key)
        return {str(k): str(v) for k, v in (result or {}).items()}

    # ─── Set ────────────────────────────────────────────────────────────────

    async def sadd(self, key: str, *members: str) -> None:
        if members:
            await self._c.sadd(key, *members)

    async def srem(self, key: str, *members: str) -> None:
        if members:
            await self._c.srem(key, *members)

    async def smembers(self, key: str) -> set[str]:
        result: Any = await self._c.smembers(key)
        return {str(m) for m in (result or set())}

    # ─── Counter ────────────────────────────────────────────────────────────

    async def incr_with_ttl(self, key: str, ttl: int) -> int:
        async with self._c.pipeline(transaction=True) as pipe:
            await pipe.incr(key)
            await pipe.expire(key, ttl, nx=True)  # NX: faqat TTL yo'q bo'lsa
            results = await pipe.execute()
        return int(results[0])
