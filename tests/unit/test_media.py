"""Media skaner va batch utilitlari testlari."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from girgitton.core.models import MediaBatch
from girgitton.shared.media import (
    MediaScanError,
    file_sha256,
    make_batches,
    scan_media_folder,
)

if TYPE_CHECKING:
    from pathlib import Path


def _create_files(folder: Path, names: list[str]) -> None:
    for name in names:
        (folder / name).write_bytes(b"x")


def test_scan_skips_non_media(tmp_path: Path) -> None:
    _create_files(tmp_path, ["a.jpg", "b.txt", "c.mp4", "ignore.zip"])
    files = scan_media_folder(tmp_path)
    assert {p.name for p in files} == {"a.jpg", "c.mp4"}


def test_scan_sorted_by_name(tmp_path: Path) -> None:
    _create_files(tmp_path, ["c.jpg", "a.jpg", "b.jpg"])
    files = scan_media_folder(tmp_path)
    assert [p.name for p in files] == ["a.jpg", "b.jpg", "c.jpg"]


def test_scan_skips_hidden(tmp_path: Path) -> None:
    _create_files(tmp_path, ["a.jpg", ".secret.jpg"])
    assert [p.name for p in scan_media_folder(tmp_path)] == ["a.jpg"]


def test_scan_missing_folder() -> None:
    with pytest.raises(MediaScanError):
        scan_media_folder("/nonexistent/__never__")


def test_scan_recursive(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    _create_files(tmp_path, ["a.jpg"])
    _create_files(sub, ["b.jpg"])
    flat = scan_media_folder(tmp_path)
    deep = scan_media_folder(tmp_path, recursive=True)
    assert {p.name for p in flat} == {"a.jpg"}
    assert {p.name for p in deep} == {"a.jpg", "b.jpg"}


def test_make_batches_5_per_chunk(tmp_path: Path) -> None:
    files = [tmp_path / f"f{i}.jpg" for i in range(12)]
    for f in files:
        f.write_bytes(b"x")
    batches = make_batches(files, batch_size=5)
    assert len(batches) == 3
    assert all(isinstance(b, MediaBatch) for b in batches)
    assert batches[0].size == 5
    assert batches[2].size == 2


def test_make_batches_idx_starts_from_1(tmp_path: Path) -> None:
    files = [tmp_path / f"f{i}.jpg" for i in range(7)]
    for f in files:
        f.write_bytes(b"x")
    batches = make_batches(files, batch_size=5)
    assert batches[0].idx == 1
    assert batches[1].idx == 2


def test_file_sha256_deterministic(tmp_path: Path) -> None:
    f = tmp_path / "x.jpg"
    f.write_bytes(b"hello")
    assert file_sha256(f) == file_sha256(f)
