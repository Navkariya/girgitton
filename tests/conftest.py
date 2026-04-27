"""Loyiha-darajasidagi pytest fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def _block_dotenv_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    """Default test runda chinakam `.env` fayli sirka kirmasligi uchun."""
    monkeypatch.setenv("DOTENV_DISABLED", "1")
    yield
