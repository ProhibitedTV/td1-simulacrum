"""Observer Continuity reference calculations.

The initial implementation intentionally uses only transparent, standard
terrestrial calculations. Higher-precision astronomy and ephemerides can be
added later behind explicit accuracy contracts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

WGS84_A_M = 6_378_137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)
J2000_JD = 2_451_545.0


@dataclass(frozen=True, slots=True)
class ObserverState:
    timestamp: datetime
    latitude_deg: float
    longitude_deg: float
    altitude_m: float = 0.0

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude_deg <= 90.0:
            raise ValueError("latitude must be in -90..+90 degrees")
        if not -180.0 <= self.longitude_deg <= 180.0:
            raise ValueError("longitude must be in -180..+180 degrees")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")

    @property
    def utc(self) -> datetime:
        return self.timestamp.astimezone(UTC)

    def ecef_m(self) -> tuple[float, float, float]:
        return geodetic_to_ecef(self.latitude_deg, self.longitude_deg, self.altitude_m)

    def julian_date_utc(self) -> float:
        return julian_date_utc(self.utc)

    def approximate_earth_rotation_angle_rad(self) -> float:
        return approximate_earth_rotation_angle_utc(self.utc)

    def snapshot(self) -> dict[str, object]:
        x, y, z = self.ecef_m()
        return {
            "timestamp_utc": self.utc.isoformat(),
            "latitude_deg": self.latitude_deg,
            "longitude_deg": self.longitude_deg,
            "altitude_m": self.altitude_m,
            "ecef_m": [x, y, z],
            "julian_date_utc": self.julian_date_utc(),
            "earth_rotation_angle_rad_approx": self.approximate_earth_rotation_angle_rad(),
        }


def geodetic_to_ecef(
    latitude_deg: float,
    longitude_deg: float,
    altitude_m: float = 0.0,
) -> tuple[float, float, float]:
    """Convert WGS-84 geodetic coordinates to Earth-centered Earth-fixed meters."""
    if not -90.0 <= latitude_deg <= 90.0:
        raise ValueError("latitude must be in -90..+90 degrees")
    if not -180.0 <= longitude_deg <= 180.0:
        raise ValueError("longitude must be in -180..+180 degrees")

    lat = math.radians(latitude_deg)
    lon = math.radians(longitude_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    radius = WGS84_A_M / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)

    x = (radius + altitude_m) * cos_lat * math.cos(lon)
    y = (radius + altitude_m) * cos_lat * math.sin(lon)
    z = (radius * (1.0 - WGS84_E2) + altitude_m) * sin_lat
    return x, y, z


def julian_date_utc(timestamp: datetime) -> float:
    """Return Julian Date using UTC civil time.

    This is sufficient for the emulator's initial terrestrial continuity layer.
    Precision astronomy will require explicit treatment of UT1, TT/TDB, leap
    seconds, Earth orientation parameters, and ephemeris time scales.
    """
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    utc = timestamp.astimezone(UTC)
    unix_seconds = utc.timestamp()
    return unix_seconds / 86_400.0 + 2_440_587.5


def approximate_earth_rotation_angle_utc(timestamp: datetime) -> float:
    """Approximate Earth Rotation Angle using UTC as a proxy for UT1.

    This is intentionally labeled approximate. Once Observer Continuity targets
    precision navigation, UT1-UTC and Earth orientation parameters must be
    supplied rather than silently assumed.
    """
    jd = julian_date_utc(timestamp)
    turns = 0.7790572732640 + 1.00273781191135448 * (jd - J2000_JD)
    return math.tau * (turns % 1.0)
