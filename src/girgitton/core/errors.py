"""Domen xatoliklari — barchasi GirgittonError dan meros."""

from __future__ import annotations


class GirgittonError(Exception):
    """Loyihaga xos asosiy istisno."""


class ConfigError(GirgittonError):
    """Konfiguratsiya yetishmayotgan yoki noto'g'ri."""


class AuthError(GirgittonError):
    """HMAC/imzo tekshiruvi muvaffaqiyatsiz tugadi."""


class PairCodeInvalidError(GirgittonError):
    """Pair code noto'g'ri yoki muddati o'tgan."""


class RateLimitError(GirgittonError):
    """Foydalanuvchi yoki IP ko'p so'rov yubordi."""


class FloodWaitError(GirgittonError):
    """Telegram throttle — kutiladigan vaqt seconds atributida."""

    def __init__(self, seconds: int, message: str | None = None) -> None:
        self.seconds = max(0, int(seconds))
        super().__init__(message or f"FloodWait: {self.seconds}s")


class StorageError(GirgittonError):
    """Storage backend xatoligi."""


class UploadError(GirgittonError):
    """Upload jarayonida bo'lgan xatolik."""
