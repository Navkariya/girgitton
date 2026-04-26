"""
Storage abstraction — Redis (Railway) yoki JSON fayl (lokal).

REDIS_URL muhit o'zgaruvchisi mavjud bo'lsa Redis,
yo'q bo'lsa ~/.girgitton_config.json ga fallback.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("girgitton")

try:
    import redis.asyncio as aioredis
    _HAS_REDIS = True
except ImportError:
    aioredis = None  # type: ignore
    _HAS_REDIS = False

_redis = None
_CONFIG_FILE = Path.home() / ".girgitton_config.json"


async def init_storage() -> None:
    global _redis
    url = os.getenv("REDIS_URL")
    if url and _HAS_REDIS:
        try:
            _redis = aioredis.from_url(url, decode_responses=True)
            await _redis.ping()
            logger.info("Storage: Redis ulandi")
        except Exception as exc:
            logger.warning("Storage: Redis xato → JSON fallback: %s", exc)
            _redis = None
    else:
        logger.info("Storage: JSON fayl rejimi (%s)", _CONFIG_FILE)


def _folder_hash(folder: str) -> str:
    return hashlib.md5(folder.encode()).hexdigest()[:8]


# ── Progress ──────────────────────────────────────────────────────────────

async def save_progress(chat_id: int, folder: str, batch: int) -> None:
    if _redis:
        key = f"progress:{chat_id}:{_folder_hash(folder)}"
        await _redis.set(key, json.dumps({"folder": folder, "batch": batch}))
    else:
        _json_save_progress(chat_id, folder, batch)


async def load_progress(chat_id: int, folder: str) -> int:
    if _redis:
        key = f"progress:{chat_id}:{_folder_hash(folder)}"
        raw = await _redis.get(key)
        if raw:
            data = json.loads(raw)
            if data.get("folder") == folder:
                return int(data.get("batch", 0))
        return 0
    return _json_load_progress(chat_id, folder)


async def clear_progress(chat_id: int, folder: str) -> None:
    await save_progress(chat_id, folder, 0)


async def save_chat_folder(chat_id: int, folder: str) -> None:
    if _redis:
        await _redis.hset(f"chat:{chat_id}", "folder", folder)
    else:
        _json_save_chat_folder(chat_id, folder)


async def get_last_folder(chat_id: int) -> Optional[str]:
    if _redis:
        return await _redis.hget(f"chat:{chat_id}", "folder")
    return _json_get_last_folder(chat_id)


# ── Allowed users ──────────────────────────────────────────────────────────

async def add_allowed_user(user_id: int) -> None:
    if _redis:
        await _redis.sadd("allowed_users", str(user_id))
    else:
        _json_add_allowed(user_id)


async def remove_allowed_user(user_id: int) -> None:
    if _redis:
        await _redis.srem("allowed_users", str(user_id))
    else:
        _json_remove_allowed(user_id)


async def load_allowed_users() -> set[int]:
    if _redis:
        members = await _redis.smembers("allowed_users")
        return {int(m) for m in members}
    return _json_load_allowed()


# ── Pair Code ──────────────────────────────────────────────────────────────

async def save_pair_code(code: str, data: dict, ttl: int = 300) -> None:
    if _redis:
        await _redis.setex(f"pair_code:{code}", ttl, json.dumps(data))
    else:
        _json_save_pair_code(code, data, ttl)


async def consume_pair_code(code: str) -> Optional[dict]:
    """Kod ishlatilgach uni o'chirib yuboradi."""
    if _redis:
        raw = await _redis.getdel(f"pair_code:{code}")
        return json.loads(raw) if raw else None
    return _json_consume_pair_code(code)


# ── Active Groups ──────────────────────────────────────────────────────────

async def add_active_group(group_id: int, title: str) -> None:
    if _redis:
        await _redis.hset("active_groups", str(group_id), title)
    else:
        _json_add_active_group(group_id, title)


async def remove_active_group(group_id: int) -> None:
    if _redis:
        await _redis.hdel("active_groups", str(group_id))
    else:
        _json_remove_active_group(group_id)


async def get_active_groups() -> list[dict]:
    if _redis:
        groups = await _redis.hgetall("active_groups")
        return [{"id": int(gid), "title": title} for gid, title in groups.items()]
    return _json_get_active_groups()


# ── App status ─────────────────────────────────────────────────────────────

async def save_app_status(user_id: int, chat_id: int, data: dict) -> None:
    if _redis:
        key = f"status:{user_id}:{chat_id}"
        await _redis.setex(key, 300, json.dumps(data))


async def load_app_status(user_id: int, chat_id: int) -> Optional[dict]:
    if _redis:
        key = f"status:{user_id}:{chat_id}"
        raw = await _redis.get(key)
        return json.loads(raw) if raw else None
    return None


# ── JSON fallback ──────────────────────────────────────────────────────────

def _json_read() -> dict:
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _json_write(data: dict) -> None:
    try:
        _CONFIG_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Storage: JSON yozish xatosi: %s", exc)


def _json_save_progress(chat_id: int, folder: str, n: int) -> None:
    data = _json_read()
    data.setdefault("chats", {})[str(chat_id)] = {
        "last_folder": folder,
        "completed_batches": n,
    }
    _json_write(data)


def _json_load_progress(chat_id: int, folder: str) -> int:
    chat = _json_read().get("chats", {}).get(str(chat_id), {})
    if chat.get("last_folder") == folder:
        return int(chat.get("completed_batches", 0))
    return 0


def _json_save_chat_folder(chat_id: int, folder: str) -> None:
    data = _json_read()
    data.setdefault("chats", {}).setdefault(str(chat_id), {})["last_folder"] = folder
    _json_write(data)


def _json_get_last_folder(chat_id: int) -> Optional[str]:
    return _json_read().get("chats", {}).get(str(chat_id), {}).get("last_folder")


def _json_add_allowed(user_id: int) -> None:
    data = _json_read()
    users = set(data.get("allowed_users", []))
    users.add(user_id)
    data["allowed_users"] = list(users)
    _json_write(data)


def _json_remove_allowed(user_id: int) -> None:
    data = _json_read()
    users = set(data.get("allowed_users", []))
    users.discard(user_id)
    data["allowed_users"] = list(users)
    _json_write(data)


def _json_load_allowed() -> set[int]:
    return set(_json_read().get("allowed_users", []))


def _json_save_pair_code(code: str, data: dict, ttl: int) -> None:
    json_data = _json_read()
    json_data.setdefault("pair_codes", {})[code] = data
    _json_write(json_data)


def _json_consume_pair_code(code: str) -> Optional[dict]:
    json_data = _json_read()
    codes = json_data.get("pair_codes", {})
    if code in codes:
        data = codes.pop(code)
        _json_write(json_data)
        return data
    return None


def _json_add_active_group(group_id: int, title: str) -> None:
    json_data = _json_read()
    json_data.setdefault("active_groups", {})[str(group_id)] = title
    _json_write(json_data)


def _json_remove_active_group(group_id: int) -> None:
    json_data = _json_read()
    if str(group_id) in json_data.get("active_groups", {}):
        del json_data["active_groups"][str(group_id)]
        _json_write(json_data)


def _json_get_active_groups() -> list[dict]:
    json_data = _json_read()
    groups = json_data.get("active_groups", {})
    return [{"id": int(gid), "title": title} for gid, title in groups.items()]

