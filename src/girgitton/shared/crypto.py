"""HMAC-SHA256 imzolash + Fernet shifrlash.

`HMACSigner` har request uchun timestamp bilan imzo yaratadi va tekshiradi
(replay-protection: ±60s skew). `Fernet` lokal credentials.json shifrlash.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Final

from cryptography.fernet import Fernet, InvalidToken

from girgitton.core.constants import HMAC_TIMESTAMP_SKEW_SECONDS
from girgitton.core.errors import AuthError

_HEADER_SIGNATURE: Final[str] = "X-Signature"
_HEADER_TIMESTAMP: Final[str] = "X-Timestamp"


@dataclass(frozen=True, slots=True)
class SignedRequest:
    """Imzolangan so'rov maydonlari."""

    signature: str
    timestamp: int

    def headers(self) -> dict[str, str]:
        return {
            _HEADER_SIGNATURE: self.signature,
            _HEADER_TIMESTAMP: str(self.timestamp),
        }


class HMACSigner:
    """HMAC-SHA256 imzolash va tekshirish.

    Imzo formati: HMAC(secret, f"{timestamp}.{body_hex}")
    """

    __slots__ = ("_secret",)

    def __init__(self, secret: str) -> None:
        if not secret:
            raise ValueError("HMAC secret bo'sh bo'lmasligi kerak")
        self._secret = secret.encode("utf-8")

    def _payload(self, body: bytes, timestamp: int) -> bytes:
        return f"{timestamp}.".encode() + body

    def sign(self, body: bytes, timestamp: int | None = None) -> SignedRequest:
        ts = timestamp if timestamp is not None else int(time.time())
        digest = hmac.new(self._secret, self._payload(body, ts), hashlib.sha256).hexdigest()
        return SignedRequest(signature=digest, timestamp=ts)

    def verify(
        self,
        body: bytes,
        signature: str,
        timestamp: str | int,
        *,
        skew: int = HMAC_TIMESTAMP_SKEW_SECONDS,
    ) -> None:
        """Imzoni tekshiradi. Muvaffaqiyatsiz bo'lsa AuthError raise qiladi."""
        try:
            ts = int(timestamp)
        except (TypeError, ValueError) as exc:
            raise AuthError("X-Timestamp noto'g'ri") from exc

        now = int(time.time())
        if abs(now - ts) > skew:
            raise AuthError(f"Timestamp skew juda katta ({abs(now - ts)}s > {skew}s)")

        expected = hmac.new(self._secret, self._payload(body, ts), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise AuthError("Imzo to'g'ri kelmadi")


# ─── Fernet (lokal credentials shifrlash) ───────────────────────────────────


def generate_fernet_key() -> str:
    """Yangi Fernet kalitini base64 string sifatida qaytaradi."""
    return Fernet.generate_key().decode("ascii")


def encrypt_blob(data: bytes, key: str) -> bytes:
    """Berilgan kalit bilan ma'lumotni shifrlaydi."""
    return Fernet(key.encode("ascii")).encrypt(data)


def decrypt_blob(token: bytes, key: str) -> bytes:
    """Shifrlangan ma'lumotni ochadi.

    Raises:
        AuthError: agar kalit yoki token noto'g'ri bo'lsa.
    """
    try:
        return Fernet(key.encode("ascii")).decrypt(token)
    except InvalidToken as exc:
        raise AuthError("Fernet token yaroqsiz") from exc


# ─── Pair code generator ────────────────────────────────────────────────────


_PAIR_ALPHABET: Final[str] = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 0/O/1/I shubhasiz


def generate_pair_code(length: int = 6) -> str:
    """Cryptographically-strong pair code (alphabet O, 0, 1, I dan toza)."""
    return "".join(secrets.choice(_PAIR_ALPHABET) for _ in range(length))
