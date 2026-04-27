"""JSONStorage va shared.repositories testlari (v3.1 multi-tenant)."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import pytest

from girgitton.core.models import ActiveGroup, AppStatus
from girgitton.shared.repositories import (
    add_active_group,
    add_allowed_user,
    bind_connect_token,
    consume_connect_token,
    consume_resume_signal,
    consume_stop_signal,
    enroll_user,
    get_connect_token,
    hit_rate_limit,
    init_connect_token,
    is_enrolled,
    latest_app_status,
    list_active_groups,
    list_allowed_users,
    remove_active_group,
    remove_allowed_user,
    remove_group_from_all_owners,
    save_app_status,
    set_resume_signal,
    set_stop_signal,
)
from girgitton.storage.json_store import JSONStorage

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
async def storage(tmp_path: Path) -> JSONStorage:
    s = JSONStorage(tmp_path / "state.json")
    await s.init()
    return s


# ─── KV/Hash/Set primitives ─────────────────────────────────────────────────


async def test_kv_set_get(storage: JSONStorage) -> None:
    await storage.set("k", "v")
    assert await storage.get("k") == "v"


async def test_kv_ttl_expires(storage: JSONStorage) -> None:
    await storage.set("k", "v", ttl=1)
    assert await storage.get("k") == "v"
    await asyncio.sleep(1.1)
    assert await storage.get("k") is None


async def test_getdel_returns_and_removes(storage: JSONStorage) -> None:
    await storage.set("k", "v")
    assert await storage.getdel("k") == "v"
    assert await storage.get("k") is None


async def test_hash_ops(storage: JSONStorage) -> None:
    await storage.hset("g", "1", "first")
    await storage.hset("g", "2", "second")
    assert await storage.hget("g", "1") == "first"
    assert await storage.hgetall("g") == {"1": "first", "2": "second"}
    await storage.hdel("g", "1")
    assert await storage.hgetall("g") == {"2": "second"}


async def test_set_ops(storage: JSONStorage) -> None:
    await storage.sadd("acl", "1", "2", "3")
    assert await storage.smembers("acl") == {"1", "2", "3"}
    await storage.srem("acl", "2")
    assert await storage.smembers("acl") == {"1", "3"}


async def test_incr_with_ttl(storage: JSONStorage) -> None:
    assert await storage.incr_with_ttl("hits", ttl=60) == 1
    assert await storage.incr_with_ttl("hits", ttl=60) == 2
    assert await storage.incr_with_ttl("hits", ttl=60) == 3


async def test_incr_resets_after_ttl(storage: JSONStorage) -> None:
    assert await storage.incr_with_ttl("h", ttl=1) == 1
    await asyncio.sleep(1.1)
    assert await storage.incr_with_ttl("h", ttl=1) == 1


# ─── Connect token oqimi ────────────────────────────────────────────────────


async def test_connect_token_init_then_bind_then_consume(storage: JSONStorage) -> None:
    token = "abcd1234"
    await init_connect_token(storage, token, ttl=60)
    assert await get_connect_token(storage, token) is None

    ok = await bind_connect_token(storage, token, user_id=42, ttl=60)
    assert ok
    assert await get_connect_token(storage, token) == 42

    assert await consume_connect_token(storage, token) == 42
    assert await consume_connect_token(storage, token) is None  # one-time


async def test_bind_connect_token_unknown(storage: JSONStorage) -> None:
    ok = await bind_connect_token(storage, "missing_token", user_id=42)
    assert not ok


async def test_connect_token_expires(storage: JSONStorage) -> None:
    await init_connect_token(storage, "x", ttl=1)
    await asyncio.sleep(1.1)
    assert await get_connect_token(storage, "x") is None


# ─── Enrollment ─────────────────────────────────────────────────────────────


async def test_enroll_and_check(storage: JSONStorage) -> None:
    assert not await is_enrolled(storage, 1)
    await enroll_user(storage, 1)
    assert await is_enrolled(storage, 1)
    await enroll_user(storage, 1)  # idempotent
    assert await is_enrolled(storage, 1)


# ─── Active groups (per-owner) ──────────────────────────────────────────────


async def test_active_groups_per_owner_isolation(storage: JSONStorage) -> None:
    await add_active_group(storage, owner_id=1, group=ActiveGroup(-100, "Group X"))
    await add_active_group(storage, owner_id=1, group=ActiveGroup(-200, "Group Y"))
    await add_active_group(storage, owner_id=2, group=ActiveGroup(-300, "Group Z"))

    a = await list_active_groups(storage, owner_id=1)
    b = await list_active_groups(storage, owner_id=2)
    assert {g.id for g in a} == {-100, -200}
    assert {g.id for g in b} == {-300}


async def test_active_group_remove_only_for_one_owner(storage: JSONStorage) -> None:
    g = ActiveGroup(-100, "Shared")
    await add_active_group(storage, owner_id=1, group=g)
    await add_active_group(storage, owner_id=2, group=g)

    await remove_active_group(storage, owner_id=1, group_id=-100)
    assert await list_active_groups(storage, owner_id=1) == ()
    assert {gg.id for gg in await list_active_groups(storage, owner_id=2)} == {-100}


async def test_remove_group_from_all_owners(storage: JSONStorage) -> None:
    await enroll_user(storage, 1)
    await enroll_user(storage, 2)
    g = ActiveGroup(-100, "Shared")
    await add_active_group(storage, owner_id=1, group=g)
    await add_active_group(storage, owner_id=2, group=g)
    await add_active_group(storage, owner_id=2, group=ActiveGroup(-200, "Other"))

    await remove_group_from_all_owners(storage, group_id=-100)
    assert await list_active_groups(storage, owner_id=1) == ()
    assert {gg.id for gg in await list_active_groups(storage, owner_id=2)} == {-200}


# ─── ACL ────────────────────────────────────────────────────────────────────


async def test_allowed_users(storage: JSONStorage) -> None:
    await add_allowed_user(storage, 1)
    await add_allowed_user(storage, 2)
    assert await list_allowed_users(storage) == frozenset({1, 2})
    await remove_allowed_user(storage, 1)
    assert await list_allowed_users(storage) == frozenset({2})


# ─── App status ─────────────────────────────────────────────────────────────


async def test_app_status_roundtrip(storage: JSONStorage) -> None:
    s = AppStatus(user_id=10, chat_id=0, batch=3, total=10, speed=1.5)
    await save_app_status(storage, s)
    again = await latest_app_status(storage, 10)
    assert again is not None
    assert again.batch == 3
    assert again.progress_pct == 30


# ─── Stop signal ────────────────────────────────────────────────────────────


async def test_stop_signal(storage: JSONStorage) -> None:
    assert await consume_stop_signal(storage, 1) is False
    await set_stop_signal(storage, 1, ttl=10)
    assert await consume_stop_signal(storage, 1) is True
    assert await consume_stop_signal(storage, 1) is False


async def test_resume_signal(storage: JSONStorage) -> None:
    assert await consume_resume_signal(storage, 1) is False
    await set_resume_signal(storage, 1, ttl=10)
    assert await consume_resume_signal(storage, 1) is True
    assert await consume_resume_signal(storage, 1) is False  # one-time


async def test_stop_and_resume_independent(storage: JSONStorage) -> None:
    await set_stop_signal(storage, 1)
    await set_resume_signal(storage, 1)
    assert await consume_stop_signal(storage, 1) is True
    assert await consume_resume_signal(storage, 1) is True


# ─── Rate limit ─────────────────────────────────────────────────────────────


async def test_rate_limit(storage: JSONStorage) -> None:
    for expected in range(1, 4):
        assert await hit_rate_limit(storage, "user:1") == expected


# ─── Persistence ────────────────────────────────────────────────────────────


async def test_persistence_across_instances(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    s1 = JSONStorage(p)
    await s1.init()
    await s1.set("hello", "world")

    s2 = JSONStorage(p)
    await s2.init()
    assert await s2.get("hello") == "world"


async def test_atomic_write_recovers_corrupt(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    p.write_text("not_json{", encoding="utf-8")
    s = JSONStorage(p)
    await s.init()
    await s.set("k", "v")
    assert await s.get("k") == "v"
    json.loads(p.read_text(encoding="utf-8"))
