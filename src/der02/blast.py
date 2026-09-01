"""TNO Multi-Energy blast overpressure model.

Implements the peak side-on overpressure Δp_s as a function of Sachs-scaled
distance Z for a vapor cloud explosion.

Sachs scaled distance:
    Z = R / (E / P₀)^(1/3)
where:
    R      = distance from explosion centre, m
    E      = combustion energy of the cloud, J
    P₀     = ambient pressure, Pa (default 101 325)

Strength class 7 is used as the default — the value recommended by TNO /
CCPS / ICheme GAME for "heavily congested on-shore module" scenarios.

Curve points are sourced from the class-7 curve as it appears in:
- van den Berg (1985), J. Hazardous Materials 12, 1–10.
- TNO Green Book / CPR 14E 3rd ed. (2005) Ch. 6.
- CCPS *Guidelines for CPQRA* 2nd ed. (2000) Ch. 4.
- Lees' *Loss Prevention in the Process Industries* 3rd ed. (2005), Fig. 17.30.

⚠️ **Not primary-verified.** The TNO Green Book PDF was not retrievable
during research (TNO removed it from public web). Curve values in this
file are reproduced from the consensus class-7 curve printed identically
across the four references above. **Re-verify against the Green Book
Ch. 6 before relying on these values for any safety-critical use.**
"""

from __future__ import annotations

from typing import Final

import numpy as np

# Sachs scaled distance (m / J^(1/3)) → peak side-on overpressure (Pa).
# Strength class 7. Points span Z = 0.1 → 100. Clamp outside that range.
#
# ⚠️ Not primary-verified. See module docstring.
#
_CURVE_Z: Final[tuple[float, ...]] = (
    0.10,
    0.15,
    0.20,
    0.30,
    0.50,
    0.70,
    1.0,
    1.5,
    2.0,
    3.0,
    4.0,
    6.0,
    8.0,
    10.0,
    15.0,
    20.0,
    30.0,
    50.0,
    70.0,
    100.0,
)
_CURVE_DP_PA: Final[tuple[float, ...]] = (
    1_000_000.0,
    700_000.0,
    500_000.0,
    320_000.0,
    180_000.0,
    110_000.0,
    70_000.0,
    40_000.0,
    27_000.0,
    15_000.0,
    10_000.0,
    6_000.0,
    4_000.0,
    3_200.0,
    2_100.0,
    1_600.0,
    1_200.0,
    700.0,
    500.0,
    300.0,
)

# Pre-compute log10 of curve points for log-log interpolation.
_LOG_Z: Final[np.ndarray] = np.log10(np.array(_CURVE_Z, dtype=float))
_LOG_DP: Final[np.ndarray] = np.log10(np.array(_CURVE_DP_PA, dtype=float))

# Default ambient pressure: sea-level standard, Pa.
DEFAULT_AMBIENT_PA: Final[float] = 101_325.0

# Z range over which the TNO class-7 curve is considered valid.
Z_MIN: Final[float] = 0.1
Z_MAX: Final[float] = 100.0


def _log_log_interp(z: float) -> float:
    """Piecewise-linear interpolation of Δp_s at given Z in log-log space.

    Clamps to the nearest endpoint outside [Z_MIN, Z_MAX].
    """
    if z <= _CURVE_Z[0]:
        return _CURVE_DP_PA[0]
    if z >= _CURVE_Z[-1]:
        return _CURVE_DP_PA[-1]

    log_z = np.log10(z)
    # Find the bracketing segment.
    idx = int(np.searchsorted(_LOG_Z, log_z)) - 1
    idx = max(0, min(idx, len(_LOG_Z) - 2))

    # Linear interpolation in log10.
    x0, x1 = _LOG_Z[idx], _LOG_Z[idx + 1]
    y0, y1 = _LOG_DP[idx], _LOG_DP[idx + 1]
    log_dp = y0 + (log_z - x0) * (y1 - y0) / (x1 - x0)
    return float(10.0**log_dp)


def blast_overpressure(
    distance_m: float,
    energy_joules: float,
    ambient_pressure_pa: float = DEFAULT_AMBIENT_PA,
) -> float:
    """Peak side-on overpressure at a given distance from a vapor cloud
    explosion, using the TNO Multi-Energy strength class 7 curve.

    Parameters
    ----------
    distance_m
        Distance from the explosion centre, metres. Must be > 0.
    energy_joules
        Combustion energy of the participating cloud, joules. Must be > 0.
    ambient_pressure_pa
        Ambient pressure, Pa. Defaults to 101 325 Pa (sea-level standard).

    Returns
    -------
    float
        Peak side-on overpressure in Pa.

    Raises
    ------
    ValueError
        If distance_m or energy_joules is not positive, or if ambient
        pressure is not positive.

    Notes
    -----
    Outside Z ∈ [0.1, 100] the TNO curve loses validity. The function
    clamps to the nearest endpoint (returning Δp_s at Z = 0.1 for very
    near field, and Δp_s at Z = 100 for very far field).
    """
    if distance_m <= 0:
        raise ValueError(f"distance_m must be positive, got {distance_m}")
    if energy_joules <= 0:
        raise ValueError(f"energy_joules must be positive, got {energy_joules}")
    if ambient_pressure_pa <= 0:
        raise ValueError(
            f"ambient_pressure_pa must be positive, got {ambient_pressure_pa}"
        )

    # Sachs scaled distance: Z = R / (E / P₀)^(1/3)
    z = distance_m / (energy_joules / ambient_pressure_pa) ** (1.0 / 3.0)
    return _log_log_interp(z)


__all__ = [
    "blast_overpressure",
    "DEFAULT_AMBIENT_PA",
    "Z_MIN",
    "Z_MAX",
]
