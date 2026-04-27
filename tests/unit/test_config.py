"""Settings va SecretStr testlari."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from girgitton.core.config import SecretStr, Settings
from girgitton.core.errors import ConfigError

if TYPE_CHECKING:
    from pathlib import Path


def _empty_env(tmp_path: Path) -> Path:
    """Test uchun bo'sh `.env` fayl yaratadi (real .env ni mahalliylashtirish)."""
    f = tmp_path / "empty.env"
    f.write_text("", encoding="utf-8")
    return f


def test_secret_str_repr_masks() -> None:
    s = SecretStr("super_secret_token")
    assert repr(s) == "SecretStr('***')"
    assert str(s) == "***"
    assert "super_secret_token" not in repr(s)


def test_secret_str_get_returns_real() -> None:
    s = SecretStr("real_value")
    assert s.get() == "real_value"


def test_secret_str_bool() -> None:
    assert not SecretStr("")
    assert SecretStr("x")


def test_settings_load_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("API_ID", "12345")
    monkeypatch.setenv("API_HASH", "deadbeefcafe1234deadbeefcafe1234")
    monkeypatch.setenv("BOT_TOKEN", "1234567890:abcdef")
    monkeypatch.setenv("OWNER_ID", "999  # me")
    monkeypatch.setenv("API_SECRET", "topsecret")
    monkeypatch.setenv("UPLOAD_WORKERS", "4")

    settings = Settings.load(env_file=_empty_env(tmp_path))
    settings.validate()

    assert settings.api_id == 12345
    assert settings.api_hash.get() == "deadbeefcafe1234deadbeefcafe1234"
    assert settings.owner_id == 999
    assert settings.upload_workers == 4


def test_settings_validate_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for key in ("API_ID", "API_HASH", "BOT_TOKEN", "API_SECRET"):
        monkeypatch.delenv(key, raising=False)

    s = Settings.load(env_file=_empty_env(tmp_path))
    with pytest.raises(ConfigError):
        s.validate()


def test_settings_to_safe_dict_masks_secrets(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("API_ID", "1")
    monkeypatch.setenv("API_HASH", "hash")
    monkeypatch.setenv("BOT_TOKEN", "tok")
    monkeypatch.setenv("API_SECRET", "secret")
    s = Settings.load(env_file=_empty_env(tmp_path))
    safe = s.to_safe_dict()
    assert safe["api_hash"] == "***"
    assert safe["bot_token"] == "***"
    assert safe["api_secret"] == "***"
