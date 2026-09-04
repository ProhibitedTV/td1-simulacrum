import math
from datetime import UTC, datetime

import pytest

from td1_simulacrum import ObserverState, geodetic_to_ecef, julian_date_utc


def test_wgs84_equator_origin() -> None:
    x, y, z = geodetic_to_ecef(0.0, 0.0, 0.0)
    assert x == pytest.approx(6_378_137.0, abs=1e-6)
    assert y == pytest.approx(0.0, abs=1e-9)
    assert z == pytest.approx(0.0, abs=1e-9)


def test_j2000_julian_date() -> None:
    timestamp = datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert julian_date_utc(timestamp) == pytest.approx(2_451_545.0)


def test_observer_snapshot_is_real_state_not_animation() -> None:
    state = ObserverState(
        timestamp=datetime(2026, 9, 4, 12, 0, tzinfo=UTC),
        latitude_deg=40.4233,
        longitude_deg=-104.7091,
        altitude_m=1420.0,
    )
    snapshot = state.snapshot()
    assert len(snapshot["ecef_m"]) == 3
    assert math.isfinite(snapshot["earth_rotation_angle_rad_approx"])


def test_observer_rejects_naive_time() -> None:
    with pytest.raises(ValueError):
        ObserverState(datetime(2026, 9, 4, 12, 0), 0.0, 0.0)
