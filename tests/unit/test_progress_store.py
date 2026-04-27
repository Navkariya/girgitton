"""Lokal progress saqlovchi testlari."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from girgitton.app import progress_store
from girgitton.app.progress_store import GroupProgress

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def isolated_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Progress fayl yo'lini tmp ga yo'naltiradi."""
    monkeypatch.setattr(progress_store, "_PROGRESS_PATH", tmp_path / "progress.json")
    return tmp_path


def test_load_empty_when_no_file() -> None:
    assert progress_store.load_all() == {}


def test_save_and_load_roundtrip() -> None:
    p = GroupProgress(
        group_id=-1001,
        folder="/tmp/foo",
        folder_hash="abc123",
        completed_batches=3,
        total_batches=10,
    )
    progress_store.save_progress(p)
    loaded = progress_store.load_all()
    assert loaded == {-1001: p}


def test_multiple_groups_in_one_file() -> None:
    p1 = GroupProgress(-100, "/a", "h1", 1, 5)
    p2 = GroupProgress(-200, "/b", "h2", 2, 10)
    progress_store.save_progress(p1)
    progress_store.save_progress(p2)
    loaded = progress_store.load_all()
    assert loaded == {-100: p1, -200: p2}


def test_clear_group_keeps_others() -> None:
    progress_store.save_progress(GroupProgress(-100, "/a", "h", 1, 5))
    progress_store.save_progress(GroupProgress(-200, "/b", "h", 2, 5))
    progress_store.clear_group(-100)
    assert set(progress_store.load_all().keys()) == {-200}


def test_clear_group_last_deletes_file(isolated_path: Path) -> None:
    progress_store.save_progress(GroupProgress(-100, "/a", "h", 1, 5))
    progress_store.clear_group(-100)
    assert not (isolated_path / "progress.json").exists()


def test_clear_all() -> None:
    progress_store.save_progress(GroupProgress(-100, "/a", "h", 1, 5))
    progress_store.save_progress(GroupProgress(-200, "/b", "h", 2, 10))
    progress_store.clear_all()
    assert progress_store.load_all() == {}


def test_has_resumable_true() -> None:
    progress_store.save_progress(GroupProgress(-100, "/a", "h", 3, 10))
    assert progress_store.has_resumable() is True


def test_has_resumable_false_when_done() -> None:
    progress_store.save_progress(GroupProgress(-100, "/a", "h", 10, 10))
    assert progress_store.has_resumable() is False


def test_has_resumable_false_when_empty() -> None:
    assert progress_store.has_resumable() is False


def test_summarize_with_data() -> None:
    progress_store.save_progress(GroupProgress(-100, "/a", "h", 3, 10))
    s = progress_store.summarize()
    assert "-100" in s
    assert "3/10" in s


def test_summarize_empty() -> None:
    assert "yo'q" in progress_store.summarize().lower()


def test_group_progress_remaining() -> None:
    p = GroupProgress(-100, "/a", "h", 3, 10)
    assert p.remaining == 7
    assert not p.is_done


def test_group_progress_done() -> None:
    p = GroupProgress(-100, "/a", "h", 10, 10)
    assert p.remaining == 0
    assert p.is_done


def test_folder_signature_changes_with_files(tmp_path: Path) -> None:
    folder = tmp_path / "f"
    folder.mkdir()
    sig_empty = progress_store.folder_signature(folder)
    (folder / "a.jpg").write_bytes(b"x")
    sig_one = progress_store.folder_signature(folder)
    assert sig_empty != sig_one
    (folder / "b.jpg").write_bytes(b"y")
    sig_two = progress_store.folder_signature(folder)
    assert sig_one != sig_two


def test_folder_signature_missing_dir() -> None:
    sig = progress_store.folder_signature("/nonexistent/__never__")
    assert isinstance(sig, str) and len(sig) == 16


def test_corrupt_progress_returns_empty(isolated_path: Path) -> None:
    (isolated_path / "progress.json").write_text("not_json{", encoding="utf-8")
    assert progress_store.load_all() == {}
