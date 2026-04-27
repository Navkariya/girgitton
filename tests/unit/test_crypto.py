"""HMACSigner va Fernet helperlari testlari."""

from __future__ import annotations

import time

import pytest

from girgitton.core.errors import AuthError
from girgitton.shared.crypto import (
    HMACSigner,
    decrypt_blob,
    encrypt_blob,
    generate_fernet_key,
    generate_pair_code,
)


def test_hmac_sign_and_verify() -> None:
    signer = HMACSigner("supersecret")
    body = b'{"user_id":1}'
    signed = signer.sign(body)
    signer.verify(body, signed.signature, signed.timestamp)


def test_hmac_wrong_signature() -> None:
    signer = HMACSigner("k")
    body = b"x"
    signed = signer.sign(body)
    with pytest.raises(AuthError):
        signer.verify(body, "deadbeef", signed.timestamp)


def test_hmac_tampered_body() -> None:
    signer = HMACSigner("k")
    signed = signer.sign(b"original")
    with pytest.raises(AuthError):
        signer.verify(b"tampered", signed.signature, signed.timestamp)


def test_hmac_timestamp_skew() -> None:
    signer = HMACSigner("k")
    body = b"x"
    old_ts = int(time.time()) - 9999
    signed = signer.sign(body, timestamp=old_ts)
    with pytest.raises(AuthError):
        signer.verify(body, signed.signature, old_ts)


def test_hmac_empty_secret_rejected() -> None:
    with pytest.raises(ValueError):
        HMACSigner("")


def test_fernet_roundtrip() -> None:
    key = generate_fernet_key()
    blob = encrypt_blob(b"hello", key)
    assert decrypt_blob(blob, key) == b"hello"


def test_fernet_wrong_key() -> None:
    k1 = generate_fernet_key()
    k2 = generate_fernet_key()
    blob = encrypt_blob(b"x", k1)
    with pytest.raises(AuthError):
        decrypt_blob(blob, k2)


def test_pair_code_format() -> None:
    code = generate_pair_code()
    assert len(code) == 6
    assert "0" not in code  # ambiguous chars excluded
    assert "O" not in code
    assert "1" not in code
    assert "I" not in code


def test_pair_code_unique() -> None:
    codes = {generate_pair_code() for _ in range(50)}
    assert len(codes) > 40  # juda kam to'qnashuv
