"""HTTP API integration testlari (v3.1 — connect token oqimi)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from aiohttp.test_utils import TestClient, TestServer

from girgitton.bot.api.server import build_app
from girgitton.core.config import SecretStr, Settings
from girgitton.core.models import ActiveGroup
from girgitton.shared.crypto import HMACSigner
from girgitton.shared.repositories import (
    add_active_group,
    bind_connect_token,
    init_connect_token,
    set_resume_signal,
    set_stop_signal,
)
from girgitton.storage.json_store import JSONStorage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from aiohttp import web

_API_SECRET = "test-secret-32-bytes-aaaaaaaaaaaa"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        api_id=12345,
        api_hash=SecretStr("a" * 32),
        bot_token=SecretStr("12345:abc"),
        owner_id=42,
        api_secret=SecretStr(_API_SECRET),
    )


@pytest.fixture
async def storage(tmp_path: Path) -> JSONStorage:
    s = JSONStorage(tmp_path / "state.json")
    await s.init()
    return s


@pytest.fixture
async def client(settings: Settings, storage: JSONStorage) -> AsyncIterator[TestClient]:
    app: web.Application = build_app(settings, storage)
    server = TestServer(app)
    async with TestClient(server) as c:
        yield c


def _signed_headers(body: bytes) -> dict[str, str]:
    signed = HMACSigner(_API_SECRET).sign(body)
    return signed.headers()


# ─── /health ─────────────────────────────────────────────────────────────────


async def test_health_no_auth(client: TestClient) -> None:
    resp = await client.get("/health")
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert body["version"].startswith("3.")


# ─── /connect-init ───────────────────────────────────────────────────────────


async def test_connect_init_returns_t_me_url(client: TestClient) -> None:
    resp = await client.post("/connect-init", json={"token": "abcd1234"})
    assert resp.status == 200
    data = await resp.json()
    assert data["ok"] is True
    assert data["t_me_url"].startswith("https://t.me/")
    assert "abcd1234" in data["t_me_url"]


async def test_connect_init_invalid_token(client: TestClient) -> None:
    resp = await client.post("/connect-init", json={"token": "x"})
    assert resp.status == 400


async def test_connect_init_bad_json(client: TestClient) -> None:
    resp = await client.post("/connect-init", data="{not json")
    assert resp.status == 400


# ─── /connect-status ─────────────────────────────────────────────────────────


async def test_connect_status_unbound(client: TestClient, storage: JSONStorage) -> None:
    await init_connect_token(storage, "abcd1234", ttl=60)
    resp = await client.get("/connect-status?token=abcd1234")
    assert resp.status == 200
    data = await resp.json()
    assert data["ready"] is False


async def test_connect_status_bound(client: TestClient, storage: JSONStorage) -> None:
    await init_connect_token(storage, "abcd1234", ttl=60)
    await bind_connect_token(storage, "abcd1234", user_id=99)

    resp = await client.get("/connect-status?token=abcd1234")
    assert resp.status == 200
    data = await resp.json()
    assert data["ready"] is True
    assert data["user_id"] == 99


async def test_connect_status_unknown_token(client: TestClient) -> None:
    resp = await client.get("/connect-status?token=missing00")
    assert resp.status == 404


async def test_connect_status_missing_token_param(client: TestClient) -> None:
    resp = await client.get("/connect-status")
    assert resp.status == 400


# ─── /connect-claim ──────────────────────────────────────────────────────────


async def test_connect_claim_returns_credentials(client: TestClient, storage: JSONStorage) -> None:
    await init_connect_token(storage, "abcd1234", ttl=60)
    await bind_connect_token(storage, "abcd1234", user_id=99)

    resp = await client.post("/connect-claim", json={"token": "abcd1234"})
    assert resp.status == 200
    data = await resp.json()
    assert data["ok"] is True
    assert data["user_id"] == 99
    assert data["credentials"]["api_id"] == 12345
    assert "api_secret" in data
    assert isinstance(data["groups"], list)


async def test_connect_claim_unbound_token(client: TestClient, storage: JSONStorage) -> None:
    await init_connect_token(storage, "abcd1234", ttl=60)
    resp = await client.post("/connect-claim", json={"token": "abcd1234"})
    assert resp.status == 403


async def test_connect_claim_one_time(client: TestClient, storage: JSONStorage) -> None:
    await init_connect_token(storage, "abcd1234", ttl=60)
    await bind_connect_token(storage, "abcd1234", user_id=99)

    r1 = await client.post("/connect-claim", json={"token": "abcd1234"})
    assert r1.status == 200
    r2 = await client.post("/connect-claim", json={"token": "abcd1234"})
    assert r2.status == 403


# ─── /groups (HMAC, per-owner) ──────────────────────────────────────────────


async def test_groups_requires_hmac(client: TestClient) -> None:
    resp = await client.get("/groups?user_id=42")
    assert resp.status == 401


async def test_groups_per_owner(client: TestClient, storage: JSONStorage) -> None:
    await add_active_group(storage, owner_id=1, group=ActiveGroup(-100, "X"))
    await add_active_group(storage, owner_id=1, group=ActiveGroup(-200, "Y"))
    await add_active_group(storage, owner_id=2, group=ActiveGroup(-300, "Z"))

    headers = _signed_headers(b"")
    r1 = await client.get("/groups?user_id=1", headers=headers)
    assert r1.status == 200
    d1 = await r1.json()
    assert {g["id"] for g in d1["groups"]} == {-100, -200}

    r2 = await client.get("/groups?user_id=2", headers=headers)
    d2 = await r2.json()
    assert {g["id"] for g in d2["groups"]} == {-300}


async def test_groups_missing_user_id(client: TestClient) -> None:
    headers = _signed_headers(b"")
    resp = await client.get("/groups", headers=headers)
    assert resp.status == 400


# ─── /status (HMAC) ─────────────────────────────────────────────────────────


async def test_status_requires_hmac(client: TestClient) -> None:
    body = json.dumps({"user_id": 42}).encode()
    resp = await client.post("/status", data=body, headers={"Content-Type": "application/json"})
    assert resp.status == 401


async def test_status_with_valid_hmac(client: TestClient) -> None:
    body = json.dumps(
        {"user_id": 42, "chat_id": -1001, "batch": 3, "total": 10, "speed": 1.2}
    ).encode()
    resp = await client.post(
        "/status",
        data=body,
        headers={**_signed_headers(body), "Content-Type": "application/json"},
    )
    assert resp.status == 200


async def test_status_bad_hmac(client: TestClient) -> None:
    body = json.dumps({"user_id": 42}).encode()
    resp = await client.post(
        "/status",
        data=body,
        headers={"X-Signature": "deadbeef", "X-Timestamp": "0"},
    )
    assert resp.status == 401


# ─── /task ──────────────────────────────────────────────────────────────────


async def test_task_requires_hmac(client: TestClient) -> None:
    resp = await client.get("/task?user_id=42")
    assert resp.status == 401


async def test_task_returns_action_none(client: TestClient) -> None:
    headers = _signed_headers(b"")
    resp = await client.get("/task?user_id=42", headers=headers)
    assert resp.status == 200
    data = await resp.json()
    assert data["action"] is None


async def test_task_returns_stop_action(client: TestClient, storage: JSONStorage) -> None:
    await set_stop_signal(storage, 42)
    headers = _signed_headers(b"")
    resp = await client.get("/task?user_id=42", headers=headers)
    data = await resp.json()
    assert data["action"] == "stop"


async def test_task_returns_resume_action(client: TestClient, storage: JSONStorage) -> None:
    await set_resume_signal(storage, 42)
    headers = _signed_headers(b"")
    resp = await client.get("/task?user_id=42", headers=headers)
    data = await resp.json()
    assert data["action"] == "resume"


async def test_task_stop_priority_over_resume(client: TestClient, storage: JSONStorage) -> None:
    """Agar ikkala signal bor bo'lsa, stop yuqori prioritetli."""
    await set_stop_signal(storage, 42)
    await set_resume_signal(storage, 42)
    headers = _signed_headers(b"")
    resp = await client.get("/task?user_id=42", headers=headers)
    data = await resp.json()
    assert data["action"] == "stop"


# ─── Eski /pair va /auto-pair endpointlari yo'q (4xx) ───────────────────────


async def test_legacy_pair_unavailable(client: TestClient) -> None:
    """Eski endpoint hech qachon credentials qaytarmasligi kerak."""
    resp = await client.post("/pair", json={"code": "ZZZ"})
    assert resp.status >= 400  # 401 (HMAC) yoki 404 (route yo'q) — ikkalasi ham OK


async def test_legacy_auto_pair_unavailable(client: TestClient) -> None:
    resp = await client.get("/auto-pair")
    assert resp.status >= 400
