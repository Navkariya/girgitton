"""Lokal progress saqlovchi (resume uchun).

Har batch tugagach `save_progress(group_id, folder, completed_idx, total)` chaqiriladi.
Yuklash to'liq tugaganda `clear_all()` — fayl o'chiriladi.

Fayl: ~/.girgitton/progress.json (atomic write, plain JSON — sirli ma'lumot yo'q).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_PROGRESS_PATH = Path.home() / ".girgitton" / "progress.json"
_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class GroupProgress:
    """Bitta guruh uchun saqlangan progress."""

    group_id: int
    folder: str
    folder_hash: str
    completed_batches: int
    total_batches: int

    @property
    def remaining(self) -> int:
        return max(0, self.total_batches - self.completed_batches)

    @property
    def is_done(self) -> bool:
        return self.completed_batches >= self.total_batches

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> GroupProgress:
        return cls(
            group_id=int(data["group_id"]),  # type: ignore[arg-type]
            folder=str(data.get("folder", "")),
            folder_hash=str(data.get("folder_hash", "")),
            completed_batches=int(data.get("completed_batches", 0)),  # type: ignore[arg-type]
            total_batches=int(data.get("total_batches", 0)),  # type: ignore[arg-type]
        )


def folder_signature(folder: Path | str) -> str:
    """Papka tarkibining qisqa hash'i (resume da papka o'zgarganini aniqlash)."""
    p = Path(folder)
    parts: list[str] = []
    if p.exists() and p.is_dir():
        for f in sorted(p.iterdir()):
            if f.is_file():
                parts.append(f"{f.name}:{f.stat().st_size}")
    blob = "|".join(parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def _atomic_write(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    with tmp.open("wb") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:  # pragma: no cover
        pass


def _read() -> dict[str, GroupProgress]:
    if not _PROGRESS_PATH.exists():
        return {}
    try:
        raw = json.loads(_PROGRESS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("progress.json buzilgan: %s", exc)
        return {}
    out: dict[str, GroupProgress] = {}
    for gid_str, item in raw.items():
        try:
            out[gid_str] = GroupProgress.from_dict(item)
        except (KeyError, TypeError, ValueError):
            continue
    return out


def load_all() -> dict[int, GroupProgress]:
    with _LOCK:
        data = _read()
    return {int(k): v for k, v in data.items() if k.lstrip("-").isdigit()}


def save_progress(progress: GroupProgress) -> None:
    """Bitta guruh progressini yangilaydi (atomik)."""
    with _LOCK:
        existing = _read()
        existing[str(progress.group_id)] = progress
        _atomic_write(_PROGRESS_PATH, {k: v.to_dict() for k, v in existing.items()})


def clear_group(group_id: int) -> None:
    with _LOCK:
        existing = _read()
        if str(group_id) in existing:
            del existing[str(group_id)]
            if existing:
                _atomic_write(_PROGRESS_PATH, {k: v.to_dict() for k, v in existing.items()})
            else:
                _delete_file()


def clear_all() -> None:
    with _LOCK:
        _delete_file()


def _delete_file() -> None:
    if _PROGRESS_PATH.exists():
        try:
            _PROGRESS_PATH.unlink()
        except OSError as exc:
            logger.warning("progress.json o'chirib bo'lmadi: %s", exc)


def has_resumable() -> bool:
    """Resume qilish mumkin bo'lgan progress bor-yo'qligini tekshiradi."""
    progress = load_all()
    return any(not p.is_done for p in progress.values())


def summarize() -> str:
    """Bot/UI uchun qisqa matn (X/Y batch tugagan)."""
    progress = load_all()
    if not progress:
        return "Saqlangan progress yo'q"
    lines: list[str] = []
    for p in progress.values():
        if not p.is_done:
            lines.append(
                f"• Guruh `{p.group_id}` — {p.completed_batches}/{p.total_batches} ({p.folder})"
            )
    return "\n".join(lines) if lines else "Tugatilmagan ish yo'q"
