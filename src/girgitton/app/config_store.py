"""Lokal Desktop App credentials saqlovi (Fernet shifrlangan).

Fayl: ~/.girgitton/credentials.enc
Fernet kalit: OS keyring (DPAPI/Keychain/SecretService) yoki
              ~/.girgitton/credentials.key (fallback, 0600)
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from girgitton.core import app_paths
from girgitton.core.errors import GirgittonError
from girgitton.shared.crypto import decrypt_blob, encrypt_blob, generate_fernet_key

logger = logging.getLogger(__name__)

_KEYRING_SERVICE = "girgitton-desktop"
_KEYRING_USER = "credentials_fernet"


def _config_dir() -> Path:
    return app_paths.get_data_dir()


def _config_path() -> Path:
    return app_paths.get_credentials_path()


def _key_path() -> Path:
    return app_paths.get_credentials_key_path()


class ConfigStoreError(GirgittonError):
    """Config saqlash/o'qishda xato."""


def _set_secure_perms(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:  # pragma: no cover (Windows)
        pass


def _load_or_create_key() -> str:
    """Fernet kalitni keyring/disk fallback bilan o'qiydi."""
    # 1) Keyring
    try:
        import keyring  # type: ignore[import-not-found]

        existing = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USER)
        if existing:
            return existing
        new_key = generate_fernet_key()
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USER, new_key)
        return new_key
    except Exception as exc:
        logger.debug("Keyring mavjud emas — fayl fallback: %s", exc)

    # 2) Disk fallback
    _config_dir().mkdir(parents=True, exist_ok=True)
    if _key_path().exists():
        return _key_path().read_text(encoding="ascii").strip()

    new_key = generate_fernet_key()
    _key_path().write_text(new_key, encoding="ascii")
    _set_secure_perms(_key_path())
    return new_key


def load() -> dict[str, Any] | None:
    """Saqlangan credentialsni o'qiydi (yoki None)."""
    if not _config_path().exists():
        return None
    try:
        key = _load_or_create_key()
        decrypted = decrypt_blob(_config_path().read_bytes(), key)
        return json.loads(decrypted.decode("utf-8"))
    except Exception as exc:
        logger.warning("Credentials o'qib bo'lmadi: %s", exc)
        return None


def save(cfg: dict[str, Any]) -> None:
    """Credentialsni shifrlab saqlaydi."""
    _config_dir().mkdir(parents=True, exist_ok=True)
    key = _load_or_create_key()
    blob = encrypt_blob(json.dumps(cfg, ensure_ascii=False).encode("utf-8"), key)
    _config_path().write_bytes(blob)
    _set_secure_perms(_config_path())


def clear() -> None:
    """Credentialsni o'chiradi (logout/unpair)."""
    if _config_path().exists():
        try:
            _config_path().unlink()
        except OSError as exc:
            logger.warning("Credentials o'chirib bo'lmadi: %s", exc)


def get(key: str, default: Any = None) -> Any:
    cfg = load()
    return cfg.get(key, default) if cfg else default


def update(updates: dict[str, Any]) -> None:
    cfg = load() or {}
    cfg.update(updates)
    save(cfg)
