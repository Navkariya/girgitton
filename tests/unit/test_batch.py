"""Batch yuborish (single-upload, dual-send) testlari — Telethon mocked."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from girgitton.app.upload.batch import send_album_pair, upload_files_once
from girgitton.core.models import MediaBatch

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def fake_files(tmp_path: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for i in range(5):
        f = tmp_path / f"f{i}.jpg"
        f.write_bytes(b"x" * 1024)
        files.append(f)
    return tuple(files)


async def test_upload_files_once_calls_upload_per_file(fake_files: tuple[Path, ...]) -> None:
    client = AsyncMock()
    client.upload_file.side_effect = [f"input_{i}" for i in range(5)]

    out = await upload_files_once(client, fake_files)

    assert client.upload_file.call_count == 5
    assert out == [f"input_{i}" for i in range(5)]


async def test_send_album_pair_uploads_once_sends_twice(fake_files: tuple[Path, ...]) -> None:
    client = AsyncMock()
    client.upload_file.side_effect = ["i0", "i1", "i2", "i3", "i4"]

    batch = MediaBatch(idx=1, files=fake_files)
    await send_album_pair(
        client, chat_id=42, batch=batch, total_batches=10, delay_between_steps=0.0
    )

    # Bitta upload, ikki marta send_file
    assert client.upload_file.call_count == 5
    assert client.send_file.await_count == 2

    # Birinchi chaqiriqda force_document=False (media)
    media_call = client.send_file.await_args_list[0]
    doc_call = client.send_file.await_args_list[1]

    assert media_call.kwargs["force_document"] is False
    assert doc_call.kwargs["force_document"] is True

    # Bir xil InputFile ro'yxati ikkala chaqiriqda ham ishlatilgan
    media_files = media_call.args[1]
    doc_files = doc_call.args[1]
    assert media_files == doc_files == ["i0", "i1", "i2", "i3", "i4"]


async def test_send_album_pair_blank_captions(fake_files: tuple[Path, ...]) -> None:
    """v3.2.4: Telegram'da hech qanday caption matni qoldirmaymiz."""
    client = AsyncMock()
    client.upload_file.side_effect = ["i0", "i1", "i2", "i3", "i4"]

    batch = MediaBatch(idx=2, files=fake_files)
    await send_album_pair(client, chat_id=1, batch=batch, total_batches=5, delay_between_steps=0.0)

    for call in client.send_file.await_args_list:
        captions = call.kwargs["caption"]
        assert all(c == "" for c in captions), "Hamma caption bo'sh bo'lishi kerak"
        assert len(captions) == 5
