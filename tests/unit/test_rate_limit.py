"""SpeedTracker va RotationPolicy testlari."""

from __future__ import annotations

from girgitton.app.upload.rate_limit import RotationPolicy, SpeedTracker


def test_speed_tracker_average() -> None:
    t = SpeedTracker(window=3)
    t.record(mb=10.0, seconds=10.0)  # 1 MB/s
    t.record(mb=20.0, seconds=10.0)  # 2 MB/s
    assert 1.4 < t.average < 1.6


def test_speed_tracker_window_trims() -> None:
    t = SpeedTracker(window=2)
    t.record(mb=1.0, seconds=10.0)  # 0.1 MB/s
    t.record(mb=10.0, seconds=10.0)  # 1.0 MB/s
    t.record(mb=20.0, seconds=10.0)  # 2.0 MB/s
    # Faqat oxirgi 2: (1.0 + 2.0)/2 = 1.5
    assert t.average == 1.5


def test_speed_tracker_filled() -> None:
    t = SpeedTracker(window=3)
    assert not t.filled
    for _ in range(3):
        t.record(mb=1.0, seconds=1.0)
    assert t.filled


def test_rotation_policy_count() -> None:
    p = RotationPolicy(rotate_after_n_batches=5, rotate_after_seconds=999)
    t = SpeedTracker(window=3)
    assert p.should_rotate(batches_done=5, time_elapsed=1, tracker=t)
    assert not p.should_rotate(batches_done=4, time_elapsed=1, tracker=t)


def test_rotation_policy_time() -> None:
    p = RotationPolicy(rotate_after_n_batches=999, rotate_after_seconds=10)
    t = SpeedTracker(window=3)
    assert p.should_rotate(batches_done=1, time_elapsed=11, tracker=t)
    assert not p.should_rotate(batches_done=1, time_elapsed=5, tracker=t)


def test_rotation_policy_speed_drop() -> None:
    p = RotationPolicy(
        rotate_after_n_batches=999, rotate_after_seconds=999, speed_drop_threshold=0.5
    )
    t = SpeedTracker(window=2)
    t.record(mb=0.1, seconds=10)  # 0.01 MB/s
    t.record(mb=0.1, seconds=10)
    assert p.should_rotate(batches_done=2, time_elapsed=1, tracker=t)


def test_should_throttle() -> None:
    p = RotationPolicy(throttle_speed_limit=0.05)
    assert p.should_throttle(last_speed=0.01)
    assert not p.should_throttle(last_speed=1.0)
    assert not p.should_throttle(last_speed=0.0)  # noma'lum: throttle deb hisoblamaymiz
