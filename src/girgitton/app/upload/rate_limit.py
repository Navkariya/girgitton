"""Tezlik kuzatuvchi va Telethon FloodWait uchun yordamchilar."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from girgitton.core.constants import (
    ROTATE_AFTER_N_BATCHES,
    ROTATE_AFTER_SECONDS,
    SPEED_DROP_THRESHOLD_MB_S,
    THROTTLE_SPEED_LIMIT_MB_S,
    THROTTLE_WAIT_SECONDS,
)

logger = logging.getLogger(__name__)


class SpeedTracker:
    """Oxirgi N batch tezligini kuzatadi (MB/s)."""

    __slots__ = ("_history", "_window")

    def __init__(self, window: int = 3) -> None:
        self._window = max(1, window)
        self._history: deque[float] = deque(maxlen=self._window)

    def record(self, mb: float, seconds: float) -> float:
        speed = mb / seconds if seconds > 0 else 0.0
        self._history.append(speed)
        return speed

    @property
    def average(self) -> float:
        if not self._history:
            return float("inf")
        return sum(self._history) / len(self._history)

    @property
    def filled(self) -> bool:
        return len(self._history) >= self._window

    def reset(self) -> None:
        self._history.clear()


@dataclass(frozen=True, slots=True)
class RotationPolicy:
    """3 mezonli rotatsiya qoidasi."""

    rotate_after_n_batches: int = ROTATE_AFTER_N_BATCHES
    rotate_after_seconds: int = ROTATE_AFTER_SECONDS
    speed_drop_threshold: float = SPEED_DROP_THRESHOLD_MB_S
    throttle_speed_limit: float = THROTTLE_SPEED_LIMIT_MB_S
    throttle_wait_seconds: int = THROTTLE_WAIT_SECONDS

    def should_rotate(
        self, *, batches_done: int, time_elapsed: float, tracker: SpeedTracker
    ) -> bool:
        if batches_done > 0 and batches_done % self.rotate_after_n_batches == 0:
            return True
        if time_elapsed >= self.rotate_after_seconds:
            return True
        return bool(tracker.filled and tracker.average < self.speed_drop_threshold)

    def should_throttle(self, *, last_speed: float) -> bool:
        return last_speed > 0 and last_speed < self.throttle_speed_limit


ThrottleCallback = Callable[[float, int], Awaitable[None]]


async def wait_with_callback(
    seconds: int, callback: ThrottleCallback | None, last_speed: float
) -> None:
    """Throttle vaqtida callbackni chaqirib, kutadi."""
    if callback is not None:
        await callback(last_speed, seconds)
    else:
        logger.warning("Throttle: %ds kutilmoqda (tezlik=%.3f MB/s)", seconds, last_speed)
        await asyncio.sleep(seconds)


class FloodWaitRetry:
    """`telethon.errors.FloodWaitError` uchun retry helper."""

    __slots__ = ("_max_retries",)

    def __init__(self, max_retries: int = 3) -> None:
        self._max_retries = max_retries

    async def execute(
        self,
        coro_factory: Callable[[], Awaitable[None]],
        notify: Callable[[str], Awaitable[None]] | None = None,
    ) -> None:
        """`coro_factory()` ni FloodWait bilan avto-retry qiladi."""
        # Lazy import — telethon.errors deferred (test uchun)
        from telethon.errors import FloodWaitError as TelethonFloodWait

        attempt = 0
        last_exc: Exception | None = None
        while attempt <= self._max_retries:
            try:
                await coro_factory()
                return
            except TelethonFloodWait as exc:
                last_exc = exc
                wait_for = int(exc.seconds) + 5
                if notify is not None:
                    await notify(f"⏸ FloodWait: {wait_for}s kutilmoqda (urinish {attempt + 1})")
                logger.warning("FloodWait %ds (urinish %d)", wait_for, attempt + 1)
                await asyncio.sleep(wait_for)
                attempt += 1
        if last_exc:
            raise last_exc


def now_monotonic() -> float:
    return time.monotonic()
