"""ConfigStore Fernet shifrlash testlari (keyring mocked → fayl fallback)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from girgitton.app import config_store

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def isolated_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Test sandbox: data dir ni tmp_path bilan almashtiradi va keyringni o'chiradi."""
    from girgitton.core import app_paths

    monkeypatch.setattr(app_paths, "_cached_data_dir", tmp_path)

    # Keyringni har doim xato qaytaruvchi qilamiz → fayl fallback ishlaydi
    import sys

    monkeypatch.setitem(sys.modules, "keyring", None)
    return tmp_path


def test_save_and_load_roundtrip(isolated_store: Path) -> None:
    payload = {
        "api_id": 12345,
        "api_hash": "abcdef",
        "bot_token": "11:bot",
        "groups": [{"id": -1001, "title": "Test"}],
    }
    config_store.save(payload)
    loaded = config_store.load()
    assert loaded == payload


def test_load_missing_returns_none(isolated_store: Path) -> None:
    assert config_store.load() is None


def test_clear_removes_file(isolated_store: Path) -> None:
    config_store.save({"x": 1})
    assert (isolated_store / "credentials.enc").exists()
    config_store.clear()
    assert not (isolated_store / "credentials.enc").exists()


def test_update_merges(isolated_store: Path) -> None:
    config_store.save({"a": 1, "b": 2})
    config_store.update({"b": 99, "c": 3})
    loaded = config_store.load()
    assert loaded == {"a": 1, "b": 99, "c": 3}


def test_get_default(isolated_store: Path) -> None:
    config_store.save({"a": 1})
    assert config_store.get("a") == 1
    assert config_store.get("missing", "default") == "default"


def test_blob_is_actually_encrypted(isolated_store: Path) -> None:
    config_store.save({"secret_token": "supersecret_value_12345"})
    raw = (isolated_store / "credentials.enc").read_bytes()
    assert b"supersecret_value_12345" not in raw  # ciphertext, not plaintext
