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

from girgitton.core.errors import GirgittonError
from girgitton.shared.crypto import decrypt_blob, encrypt_blob, generate_fernet_key

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path.home() / ".girgitton"
_CONFIG_PATH = _CONFIG_DIR / "credentials.enc"
_KEY_PATH = _CONFIG_DIR / "credentials.key"
_KEYRING_SERVICE = "girgitton-desktop"
_KEYRING_USER = "credentials_fernet"


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
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if _KEY_PATH.exists():
        return _KEY_PATH.read_text(encoding="ascii").strip()

    new_key = generate_fernet_key()
    _KEY_PATH.write_text(new_key, encoding="ascii")
    _set_secure_perms(_KEY_PATH)
    return new_key


def load() -> dict[str, Any] | None:
    """Saqlangan credentialsni o'qiydi (yoki None)."""
    if not _CONFIG_PATH.exists():
        return None
    try:
        key = _load_or_create_key()
        decrypted = decrypt_blob(_CONFIG_PATH.read_bytes(), key)
        return json.loads(decrypted.decode("utf-8"))
    except Exception as exc:
        logger.warning("Credentials o'qib bo'lmadi: %s", exc)
        return None


def save(cfg: dict[str, Any]) -> None:
    """Credentialsni shifrlab saqlaydi."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    key = _load_or_create_key()
    blob = encrypt_blob(json.dumps(cfg, ensure_ascii=False).encode("utf-8"), key)
    _CONFIG_PATH.write_bytes(blob)
    _set_secure_perms(_CONFIG_PATH)


def clear() -> None:
    """Credentialsni o'chiradi (logout/unpair)."""
    if _CONFIG_PATH.exists():
        try:
            _CONFIG_PATH.unlink()
        except OSError as exc:
            logger.warning("Credentials o'chirib bo'lmadi: %s", exc)


def get(key: str, default: Any = None) -> Any:
    cfg = load()
    return cfg.get(key, default) if cfg else default


def update(updates: dict[str, Any]) -> None:
    cfg = load() or {}
    cfg.update(updates)
    save(cfg)
