"""Storage adapter tanlovchisi (Redis bor bo'lsa Redis, yo'q bo'lsa JSON)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from girgitton.core.errors import StorageError
from girgitton.storage.json_store import JSONStorage
from girgitton.storage.redis_store import RedisStorage

if TYPE_CHECKING:
    from girgitton.core.config import Settings
    from girgitton.storage.base import StorageRepository

logger = logging.getLogger(__name__)

_DEFAULT_JSON_PATH = Path.home() / ".girgitton" / "state.json"


async def build_storage(
    settings: Settings,
    *,
    json_path: Path | None = None,
    allow_fallback: bool = True,
) -> StorageRepository:
    """Konfiguratsiyaga qarab Redis yoki JSON adapter qaytaradi.

    Redis bo'lsa va init muvaffaqiyatli bo'lsa Redis. Aks holda (yoki
    `allow_fallback=False` bo'lganida xato) JSON.
    """
    target_path = json_path or _DEFAULT_JSON_PATH

    if settings.redis_url:
        store: StorageRepository = RedisStorage(settings.redis_url)
        try:
            await store.init()
            return store
        except StorageError as exc:
            if not allow_fallback:
                raise
            logger.warning("Redis muvaffaqiyatsiz, JSON fallback'ga o'tilmoqda: %s", exc)

    store = JSONStorage(target_path)
    await store.init()
    return store
