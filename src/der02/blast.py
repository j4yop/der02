"""TNO Multi-Energy blast overpressure model.

Implements the peak side-on overpressure Δp_s as a function of Sachs-scaled
distance Z for a vapor cloud explosion, for any of the 10 TNO strength
classes (1 = unconfined deflagration, 10 = detonative).

Sachs scaled distance:
    Z = R / (E / P₀)^(1/3)
where:
    R      = distance from explosion centre, m
    E      = combustion energy of the cloud, J
    P₀     = ambient pressure, Pa (default 101 325)

Strength classes
----------------
The TNO Multi-Energy method classifies the explosion strength from
1 (unconfined, weak) to 10 (highly confined or detonative). Each class
has a different Sachs-scaled overpressure curve. The standard siting
class is 7, recommended for "heavily congested on-shore module" by
TNO / CCPS / ICheme GAME.

In this implementation:

- **Class 7** uses the consensus curve reproduced across van den Berg
  1985, TNO Green Book Ch. 6, CCPS *Guidelines for CPQRA* 2nd ed. Ch. 4,
  and Lees' *Loss Prevention* 3rd ed. Fig. 17.30.
- **Classes 1–6 and 8–10** are derived from the class-7 curve by a
  per-class amplitude scaling factor, with all points shifted by the
  same log10(factor). This produces the correct family-of-curves
  shape (same Z dependence, different peak pressures) but the exact
  per-class numbers are **not primary-verified**.

Class amplitude factors (peak pressure multiplier vs class 7):
    class  1: 1/100  (unconfined)
    class  2: 1/30
    class  3: 1/10
    class  4: 1/3
    class  5: 1/1.5
    class  6: 1/1.1
    class  7: 1.0     (default)
    class  8: 1.4
    class  9: 2.0
    class 10: 3.0     (detonative)

These factors approximate the standard TNO family-of-curves (per
Britoil/CCPS Ch. 4). **Not primary-verified.**

References
----------
- van den Berg (1985), J. Hazardous Materials 12, 1–10.
- TNO Green Book / CPR 14E 3rd ed. (2005) Ch. 6.
- CCPS *Guidelines for Chemical Process Quantitative Risk Analysis*
  2nd ed. (2000) Ch. 4.
- Lees' *Loss Prevention in the Process Industries* 3rd ed. (2005),
  Fig. 17.30.
- ICheme Hazards XXI paper (Cavanagh, Xu, Worthington, 2009).

⚠️ **Not primary-verified.** The TNO Green Book PDF was not retrievable
during research (TNO removed it from public web). Class-7 curve values
are reproduced from the consensus across the four references above;
classes 1–6 and 8–10 use derived amplitude factors. **Re-verify
against the Green Book Ch. 6 before relying on these values for any
operational use.**
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
_CURVE_DP_PA_CLASS_7: Final[tuple[float, ...]] = (
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

# Per-class amplitude factor (multiplier on class-7 curve).
# ⚠️ Not primary-verified. Approximate family-of-curves scaling
# consistent with CCPS Ch. 4 / TNO Green Book. Re-verify before
# operational use.
CLASS_AMPLITUDE_FACTORS: Final[dict[int, float]] = {
    1: 0.01,    # unconfined deflagration
    2: 0.033,
    3: 0.10,
    4: 0.33,
    5: 0.67,
    6: 0.91,
    7: 1.0,     # default — heavily congested module
    8: 1.4,
    9: 2.0,
    10: 3.0,    # highly confined / detonative
}

# Pre-compute log10 of curve points for log-log interpolation.
_LOG_Z: Final[np.ndarray] = np.log10(np.array(_CURVE_Z, dtype=float))
_LOG_DP_CLASS_7: Final[np.ndarray] = np.log10(
    np.array(_CURVE_DP_PA_CLASS_7, dtype=float)
)

# Default ambient pressure: sea-level standard, Pa.
DEFAULT_AMBIENT_PA: Final[float] = 101_325.0

# Default strength class.
DEFAULT_STRENGTH_CLASS: Final[int] = 7

# Z range over which the TNO class-7 curve is considered valid.
Z_MIN: Final[float] = 0.1
Z_MAX: Final[float] = 100.0


def _log_log_interp_class7(z: float) -> float:
    """Piecewise-linear interpolation of Δp_s at given Z in log-log space
    using the class-7 curve. Clamps to the nearest endpoint outside
    [Z_MIN, Z_MAX]."""
    if z <= _CURVE_Z[0]:
        return _CURVE_DP_PA_CLASS_7[0]
    if z >= _CURVE_Z[-1]:
        return _CURVE_DP_PA_CLASS_7[-1]

    log_z = np.log10(z)
    idx = int(np.searchsorted(_LOG_Z, log_z)) - 1
    idx = max(0, min(idx, len(_LOG_Z) - 2))

    x0, x1 = _LOG_Z[idx], _LOG_Z[idx + 1]
    y0, y1 = _LOG_DP_CLASS_7[idx], _LOG_DP_CLASS_7[idx + 1]
    log_dp = y0 + (log_z - x0) * (y1 - y0) / (x1 - x0)
    return float(10.0**log_dp)


def blast_overpressure(
    distance_m: float,
    energy_joules: float,
    ambient_pressure_pa: float = DEFAULT_AMBIENT_PA,
    strength_class: int = DEFAULT_STRENGTH_CLASS,
) -> float:
    """Peak side-on overpressure at a given distance from a vapor cloud
    explosion, using the TNO Multi-Energy method.

    Parameters
    ----------
    distance_m
        Distance from the explosion centre, metres. Must be > 0.
    energy_joules
        Combustion energy of the participating cloud, joules. Must be > 0.
    ambient_pressure_pa
        Ambient pressure, Pa. Defaults to 101 325 Pa (sea-level standard).
    strength_class
        TNO Multi-Energy strength class, 1 (weakest, unconfined
        deflagration) to 10 (strongest, detonative). Default 7 — the
        standard siting class for "heavily congested on-shore module"
        per TNO / CCPS / ICheme GAME.

    Returns
    -------
    float
        Peak side-on overpressure in Pa.

    Raises
    ------
    ValueError
        If distance_m or energy_joules is not positive, ambient pressure
        not positive, or strength_class is not in 1..10.
    """
    if distance_m <= 0:
        raise ValueError(f"distance_m must be positive, got {distance_m}")
    if energy_joules <= 0:
        raise ValueError(f"energy_joules must be positive, got {energy_joules}")
    if ambient_pressure_pa <= 0:
        raise ValueError(
            f"ambient_pressure_pa must be positive, got {ambient_pressure_pa}"
        )
    if strength_class not in CLASS_AMPLITUDE_FACTORS:
        raise ValueError(
            f"strength_class must be in 1..10, got {strength_class}"
        )

    # Sachs scaled distance: Z = R / (E / P₀)^(1/3)
    z = distance_m / (energy_joules / ambient_pressure_pa) ** (1.0 / 3.0)
    dp_class7 = _log_log_interp_class7(z)
    return dp_class7 * CLASS_AMPLITUDE_FACTORS[strength_class]


__all__ = [
    "blast_overpressure",
    "DEFAULT_AMBIENT_PA",
    "DEFAULT_STRENGTH_CLASS",
    "Z_MIN",
    "Z_MAX",
    "CLASS_AMPLITUDE_FACTORS",
]
