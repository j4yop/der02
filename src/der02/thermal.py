"""Thermal radiation model: point-source approximation.

For a flame releasing total heat at rate Q (kW), the radiative heat flux
received by a ground point at distance R from the flame centre is:

    I = τ · Q_rad / (4π · R²)

where:
    τ      atmospheric transmissivity (default 1.0; site-specific
           correction factors for humidity and CO₂ are out of scope for
           the MVP)
    Q_rad  radiative fraction of the heat release rate (default = Q,
           i.e. assume all heat radiates; in reality liquid-hydrocarbon
           pool fires radiate 20–40 % of HRR)

This is the standard far-field point-source approximation, valid when
the receptor distance R is large compared to the flame size. It is the
upper-bound estimate used in ALOHA and in CCPS Chapter 2 siting
calculations.

Solid-flame view-factor model
-----------------------------
The full CCPS / Mudan / Shokri-Beyler solid-flame view-factor formulation
is deferred. It requires flame geometry (height, diameter) that we do
not yet compute from the facility description. Ticket 05 ships the
point-source model only; the solid-flame model lands with the flame
height sub-model in a later ticket.

References
----------
- CCPS *Guidelines for Chemical Process Quantitative Risk Analysis*
  2nd ed. (2000), Chapter 2 — thermal radiation criteria.
- EPA / NOAA ALOHA user's manual — point-source thermal radiation.
"""

from __future__ import annotations

# Stefan-Boltzmann constant in kW / m² / K⁴. Kept here for completeness
# (not currently used by the point-source model, but documented in case
# the solid-flame model is added later).
STEFAN_BOLTZMANN_KW: float = 5.6704e-11

# Default atmospheric transmissivity. Real value depends on humidity,
# CO₂ concentration, and path length. We default to 1.0 (no
# transmissivity loss) for a clean upper bound; the caller can pass a
# measured value when site data is available.
DEFAULT_TRANSMISSIVITY: float = 1.0

# Default radiative fraction. In reality liquid-hydrocarbon pool fires
# radiate 20–40 % of HRR (CCPS Ch. 2). We default to 1.0 (all heat
# radiates) as a clean upper bound; the caller can pass a measured
# fraction for tighter estimates.
DEFAULT_RADIATIVE_FRACTION: float = 1.0


def point_source_flux(
    distance_m: float,
    heat_release_rate_kw: float,
    radiative_fraction: float = DEFAULT_RADIATIVE_FRACTION,
    transmissivity: float = DEFAULT_TRANSMISSIVITY,
) -> float:
    """Point-source thermal flux at a ground receptor.

    I = τ · χ · Q / (4π · R²)

    where χ is the radiative fraction of the heat release rate.

    Parameters
    ----------
    distance_m
        Horizontal distance from the flame centre to the receptor, m.
    heat_release_rate_kw
        Total heat release rate of the fire, kW.
    radiative_fraction
        Dimensionless ∈ (0, 1]. Defaults to 1.0 (upper bound).
    transmissivity
        Dimensionless ∈ (0, 1]. Defaults to 1.0 (no atmospheric loss).

    Returns
    -------
    float
        Radiative heat flux in kW/m².

    Raises
    ------
    ValueError
        On non-positive distance or heat release rate, or invalid
        fraction / transmissivity.
    """
    if distance_m <= 0:
        raise ValueError(f"distance_m must be positive, got {distance_m}")
    if heat_release_rate_kw <= 0:
        raise ValueError(
            f"heat_release_rate_kw must be positive, got {heat_release_rate_kw}"
        )
    if not 0 < radiative_fraction <= 1:
        raise ValueError(
            f"radiative_fraction must be in (0, 1], got {radiative_fraction}"
        )
    if not 0 < transmissivity <= 1:
        raise ValueError(
            f"transmissivity must be in (0, 1], got {transmissivity}"
        )

    q_rad = radiative_fraction * heat_release_rate_kw
    return transmissivity * q_rad / (4.0 * 3.141592653589793 * distance_m**2)


__all__ = [
    "point_source_flux",
    "STEFAN_BOLTZMANN_KW",
    "DEFAULT_TRANSMISSIVITY",
    "DEFAULT_RADIATIVE_FRACTION",
]
