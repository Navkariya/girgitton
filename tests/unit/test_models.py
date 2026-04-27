"""Domen modellarining testlari."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from girgitton.core.models import ActiveGroup, AppStatus, MediaBatch, PairCode

if TYPE_CHECKING:
    from pathlib import Path


def test_pair_code_expiry() -> None:
    pc = PairCode(
        code="ABC123",
        group_id=42,
        group_title="Test",
        user_id=1,
        expires_at=time.time() - 1,
    )
    assert pc.is_expired()


def test_pair_code_roundtrip() -> None:
    pc = PairCode("X" * 6, 5, "G", 7, time.time() + 60)
    again = PairCode.from_dict(pc.to_dict())
    assert again == pc


def test_active_group_roundtrip() -> None:
    g = ActiveGroup(id=-100, title="My Group")
    assert ActiveGroup.from_dict(g.to_dict()) == g


def test_app_status_pct() -> None:
    s = AppStatus(user_id=1, chat_id=2, batch=3, total=10, speed=0.5)
    assert s.progress_pct == 30


def test_app_status_zero_total_pct() -> None:
    s = AppStatus(user_id=1, chat_id=2, batch=0, total=0, speed=0.0)
    assert s.progress_pct == 0


def test_media_batch_empty_raises() -> None:
    with pytest.raises(ValueError):
        MediaBatch(idx=1, files=())


def test_media_batch_size_and_names(tmp_path: Path) -> None:
    files: list[Path] = []
    for i in range(3):
        f = tmp_path / f"a_{i}.jpg"
        f.write_bytes(b"x")
        files.append(f)
    batch = MediaBatch(idx=1, files=tuple(files))
    assert batch.size == 3
    assert batch.names == ("a_0.jpg", "a_1.jpg", "a_2.jpg")
