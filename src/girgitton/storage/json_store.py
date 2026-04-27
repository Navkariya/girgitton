"""JSON fayl storage adapteri (Redis bo'lmaganda fallback).

Atomik yozish: temp file → fsync → rename. asyncio.Lock har operatsiyani
seriallashtiradi, TTL chiquvchanlikka tegmaydi (lekin GET da tekshiradi).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from girgitton.core.errors import StorageError

logger = logging.getLogger(__name__)


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    """JSON ni temp fayl orqali atomik yozadi."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    with tmp.open("wb") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:  # pragma: no cover (Windows)
        pass


def _is_expired(entry: dict[str, Any]) -> bool:
    expires_at = entry.get("__exp")
    if expires_at is None:
        return False
    return time.time() >= float(expires_at)


class JSONStorage:
    """Lokal JSON fayl bilan ishlovchi `StorageRepository`."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._lock = asyncio.Lock()
        self._cache: dict[str, Any] | None = None

    async def init(self) -> None:
        try:
            self._read()
            logger.info("JSON storage: %s", self._path)
        except Exception as exc:
            raise StorageError(f"JSON storage ochib bo'lmadi: {exc}") from exc

    async def close(self) -> None:
        self._cache = None

    def _read(self) -> dict[str, Any]:
        if self._cache is not None:
            return self._cache
        if self._path.exists():
            try:
                self._cache = json.loads(self._path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning("Buzilgan JSON: %s — qayta yaratilmoqda", self._path)
                self._cache = {}
        else:
            self._cache = {}
        return self._cache

    def _write(self) -> None:
        if self._cache is not None:
            _atomic_write(self._path, self._cache)

    # ─── K/V ────────────────────────────────────────────────────────────────

    async def get(self, key: str) -> str | None:
        async with self._lock:
            data = self._read().get("kv", {})
            entry = data.get(key)
            if entry is None:
                return None
            if _is_expired(entry):
                data.pop(key, None)
                self._write()
                return None
            return str(entry["value"])

    async def set(self, key: str, value: str, *, ttl: int | None = None) -> None:
        async with self._lock:
            data = self._read()
            kv = data.setdefault("kv", {})
            entry: dict[str, Any] = {"value": value}
            if ttl is not None:
                entry["__exp"] = time.time() + ttl
            kv[key] = entry
            self._write()

    async def delete(self, key: str) -> None:
        async with self._lock:
            data = self._read()
            kv = data.get("kv", {})
            if key in kv:
                kv.pop(key, None)
                self._write()

    async def getdel(self, key: str) -> str | None:
        async with self._lock:
            data = self._read()
            kv = data.get("kv", {})
            entry = kv.pop(key, None)
            self._write()
            if entry is None or _is_expired(entry):
                return None
            return str(entry["value"])

    # ─── Hash ───────────────────────────────────────────────────────────────

    async def hset(self, key: str, field: str, value: str) -> None:
        async with self._lock:
            data = self._read()
            hashes = data.setdefault("hash", {})
            hashes.setdefault(key, {})[field] = value
            self._write()

    async def hget(self, key: str, field: str) -> str | None:
        async with self._lock:
            value = self._read().get("hash", {}).get(key, {}).get(field)
            return None if value is None else str(value)

    async def hdel(self, key: str, field: str) -> None:
        async with self._lock:
            data = self._read()
            hashes = data.get("hash", {}).get(key)
            if hashes is not None and field in hashes:
                hashes.pop(field, None)
                self._write()

    async def hgetall(self, key: str) -> dict[str, str]:
        async with self._lock:
            return {str(k): str(v) for k, v in self._read().get("hash", {}).get(key, {}).items()}

    # ─── Set ────────────────────────────────────────────────────────────────

    async def sadd(self, key: str, *members: str) -> None:
        if not members:
            return
        async with self._lock:
            data = self._read()
            sets = data.setdefault("set", {})
            current = set(sets.get(key, []))
            current.update(members)
            sets[key] = sorted(current)
            self._write()

    async def srem(self, key: str, *members: str) -> None:
        if not members:
            return
        async with self._lock:
            data = self._read()
            sets = data.get("set", {})
            current = set(sets.get(key, []))
            current.difference_update(members)
            if current:
                sets[key] = sorted(current)
            else:
                sets.pop(key, None)
            self._write()

    async def smembers(self, key: str) -> set[str]:
        async with self._lock:
            return {str(m) for m in self._read().get("set", {}).get(key, [])}

    # ─── Counter ────────────────────────────────────────────────────────────

    async def incr_with_ttl(self, key: str, ttl: int) -> int:
        async with self._lock:
            data = self._read()
            counters = data.setdefault("counter", {})
            entry = counters.get(key) or {}

            if entry and _is_expired(entry):
                entry = {}

            value = int(entry.get("value", 0)) + 1
            counters[key] = {
                "value": value,
                "__exp": entry.get("__exp", time.time() + ttl),
            }
            self._write()
            return value
