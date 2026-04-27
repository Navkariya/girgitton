"""Domen-uslubdagi storage operatsiyalari (multi-tenant: per-owner).

`v3.1`: `pair_code` o'chirildi, o'rniga `connect_token` (token-based App
ulanishi). `active_groups` har user uchun alohida (multi-tenant izolyatsiya).
"""

from __future__ import annotations

import json
import logging
import time

from girgitton.core.constants import APP_STATUS_TTL_SECONDS
from girgitton.core.models import ActiveGroup, AppStatus
from girgitton.storage.base import StorageRepository

logger = logging.getLogger(__name__)

_KEY_CONNECT_TOKEN_PREFIX = "connect_token"  # noqa: S105 — storage key prefix, parol emas
_KEY_ACTIVE_GROUPS_PREFIX = "active_groups"  # active_groups:<owner_id>
_KEY_ALLOWED_USERS = "allowed_users"
_KEY_ENROLLED_USERS = "enrolled_users"
_KEY_APP_STATUS_PREFIX = "app_status"
_KEY_RATE_LIMIT_PREFIX = "rate_limit"

CONNECT_TOKEN_TTL_SECONDS = 300  # 5 daqiqa


# ─── Connect tokens (App ↔ Bot ulanish oqimi) ───────────────────────────────


async def init_connect_token(
    storage: StorageRepository,
    token: str,
    *,
    ttl: int = CONNECT_TOKEN_TTL_SECONDS,
) -> None:
    """App connect oqimini boshlaydi: token saqlanadi, user_id hali yo'q."""
    payload = json.dumps({"user_id": None, "created_at": time.time()})
    await storage.set(f"{_KEY_CONNECT_TOKEN_PREFIX}:{token}", payload, ttl=ttl)


async def bind_connect_token(
    storage: StorageRepository,
    token: str,
    user_id: int,
    *,
    ttl: int = CONNECT_TOKEN_TTL_SECONDS,
) -> bool:
    """Bot tomonidan: token mavjud bo'lsa, unga user_id biriktiradi.

    Returns:
        True — token mavjud va biriktirildi; False — token yo'q yoki muddat tugagan.
    """
    raw = await storage.get(f"{_KEY_CONNECT_TOKEN_PREFIX}:{token}")
    if not raw:
        return False
    payload = json.dumps({"user_id": int(user_id), "created_at": time.time()})
    await storage.set(f"{_KEY_CONNECT_TOKEN_PREFIX}:{token}", payload, ttl=ttl)
    return True


async def get_connect_token(storage: StorageRepository, token: str) -> int | None:
    """Token holatini o'qiydi (poll). user_id qaytaradi yoki None (hali biriktirilmagan)."""
    raw = await storage.get(f"{_KEY_CONNECT_TOKEN_PREFIX}:{token}")
    if not raw:
        return None
    try:
        data = json.loads(raw)
        uid = data.get("user_id")
        return int(uid) if uid else None
    except (ValueError, KeyError):
        return None


async def consume_connect_token(storage: StorageRepository, token: str) -> int | None:
    """Tokenni claim qiladi (atomik o'qib o'chiradi). user_id qaytaradi yoki None."""
    raw = await storage.getdel(f"{_KEY_CONNECT_TOKEN_PREFIX}:{token}")
    if not raw:
        return None
    try:
        data = json.loads(raw)
        uid = data.get("user_id")
        return int(uid) if uid else None
    except (ValueError, KeyError):
        return None


# ─── Enrollment (/start yuborganlar) ────────────────────────────────────────


async def enroll_user(storage: StorageRepository, user_id: int) -> None:
    await storage.sadd(_KEY_ENROLLED_USERS, str(user_id))


async def is_enrolled(storage: StorageRepository, user_id: int) -> bool:
    members = await storage.smembers(_KEY_ENROLLED_USERS)
    return str(user_id) in members


# ─── Active groups (PER-OWNER) ──────────────────────────────────────────────


def _groups_key(owner_id: int) -> str:
    return f"{_KEY_ACTIVE_GROUPS_PREFIX}:{owner_id}"


async def add_active_group(
    storage: StorageRepository, owner_id: int, group: ActiveGroup
) -> None:
    """Guruhni shu owner uchun aktiv ro'yxatga qo'shadi."""
    await storage.hset(_groups_key(owner_id), str(group.id), group.title)


async def remove_active_group(
    storage: StorageRepository, owner_id: int, group_id: int
) -> None:
    """Guruhni shu owner ro'yxatidan olib tashlaydi."""
    await storage.hdel(_groups_key(owner_id), str(group_id))


async def list_active_groups(
    storage: StorageRepository, owner_id: int
) -> tuple[ActiveGroup, ...]:
    """Shu owner uchun aktiv guruhlar ro'yxati."""
    raw = await storage.hgetall(_groups_key(owner_id))
    return tuple(ActiveGroup(id=int(gid), title=title) for gid, title in raw.items())


async def remove_group_from_all_owners(
    storage: StorageRepository, group_id: int
) -> None:
    """Bot guruhdan o'chirilganida — barcha owner ro'yxatlaridan tozalaydi."""
    owners = await storage.smembers(_KEY_ENROLLED_USERS)
    for owner_str in owners:
        if owner_str.lstrip("-").isdigit():
            await storage.hdel(_groups_key(int(owner_str)), str(group_id))


# ─── ACL (allowed users) — bot-darajasidagi global ruxsat ───────────────────


async def add_allowed_user(storage: StorageRepository, user_id: int) -> None:
    await storage.sadd(_KEY_ALLOWED_USERS, str(user_id))


async def remove_allowed_user(storage: StorageRepository, user_id: int) -> None:
    await storage.srem(_KEY_ALLOWED_USERS, str(user_id))


async def list_allowed_users(storage: StorageRepository) -> frozenset[int]:
    members = await storage.smembers(_KEY_ALLOWED_USERS)
    return frozenset(int(m) for m in members if m.lstrip("-").isdigit())


# ─── App status (per user_id, chat_id) ──────────────────────────────────────


async def save_app_status(
    storage: StorageRepository,
    status: AppStatus,
    *,
    ttl: int = APP_STATUS_TTL_SECONDS,
) -> None:
    key = f"{_KEY_APP_STATUS_PREFIX}:{status.user_id}:{status.chat_id}"
    await storage.set(key, json.dumps(status.to_dict()), ttl=ttl)


async def load_app_status(
    storage: StorageRepository, user_id: int, chat_id: int = 0
) -> AppStatus | None:
    key = f"{_KEY_APP_STATUS_PREFIX}:{user_id}:{chat_id}"
    raw = await storage.get(key)
    if not raw:
        return None
    try:
        return AppStatus.from_dict(json.loads(raw))
    except (ValueError, KeyError):
        return None


async def latest_app_status(
    storage: StorageRepository, user_id: int
) -> AppStatus | None:
    return await load_app_status(storage, user_id, chat_id=0)


# ─── Rate limit / Brute force ───────────────────────────────────────────────


async def hit_rate_limit(
    storage: StorageRepository, key: str, *, window_seconds: int = 60
) -> int:
    full_key = f"{_KEY_RATE_LIMIT_PREFIX}:{key}"
    return await storage.incr_with_ttl(full_key, window_seconds)


# ─── App control signals (stop / resume) ────────────────────────────────────


async def set_stop_signal(
    storage: StorageRepository, user_id: int, *, ttl: int = 60
) -> None:
    await storage.set(f"stop:{user_id}", str(int(time.time())), ttl=ttl)


async def consume_stop_signal(storage: StorageRepository, user_id: int) -> bool:
    return (await storage.getdel(f"stop:{user_id}")) is not None


async def set_resume_signal(
    storage: StorageRepository, user_id: int, *, ttl: int = 60
) -> None:
    await storage.set(f"resume:{user_id}", str(int(time.time())), ttl=ttl)


async def consume_resume_signal(storage: StorageRepository, user_id: int) -> bool:
    return (await storage.getdel(f"resume:{user_id}")) is not None
