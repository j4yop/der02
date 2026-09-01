"""Wind distortion: adjust hazard-zone geometry for prevailing wind.

Wind elongates the downwind hazard zone (smoke, vapour, blast, thermal
plume all travel with the wind) and compresses the upwind zone.

For the MVP we use a simple heuristic documented in CCPS *Guidelines for
Chemical Process Quantitative Risk Analysis* 2nd ed. (2000) and in the
TNO dispersion literature. The distortion multiplies the *effective
distance* at which a hazard is observed:

    effective_distance = real_distance × stretch(θ, u)

where θ is the bearing from the source to the receptor (degrees,
0 = North, clockwise) and u is wind speed (m/s). The stretch factor
varies between a downwind multiplier < 1 (receptor appears "closer" in
hazard terms) and an upwind multiplier > 1 (receptor appears "farther").

Reference form (CCPS Section 2.x dispersion correction, simplified):

    stretch(θ, u) = 1 / (1 + κ · u · cos(θ − φ))

where:
    κ      wind-coupling constant (≈ 0.1 s/m is a typical MVP value;
           the literature uses values from 0.05 to 0.20 depending on
           stability class — see CCPS Table 2.x)
    φ      wind-from direction (degrees from North, clockwise)

For pure downwind (θ − φ = 0): cos = 1, stretch < 1 (effective distance
shorter than real — zone extends further).
For pure upwind (θ − φ = 180°): cos = −1, stretch > 1.
For pure crosswind (θ − φ = 90° or 270°): cos = 0, stretch = 1 (no
distortion).
At zero wind: stretch = 1 regardless of θ.

This module exports `effective_distance(...)` which returns the
distance to use for hazard-zone classification after wind adjustment.

Notes
-----
This is a **simplified** model. Real consequence modeling uses the
Britoil/EPA heavy-gas dispersion formulations or ALOHA's Gaussian
plume for neutrally-buoyant vapours. Those require atmospheric
stability class (Pasquill A–F) and are out of scope for the MVP.
"""

from __future__ import annotations

import math

# Default wind-coupling constant. κ ≈ 0.1 s/m gives a 50 % elongation
# at u = 10 m/s downwind, which is in the ballpark of ALOHA's default
# distance-multiplier behaviour. Site-specific tuning is out of scope.
DEFAULT_WIND_COUPLING: float = 0.1  # s/m


def effective_distance(
    distance_m: float,
    bearing_to_receptor_deg: float,
    wind_from_direction_deg: float,
    wind_speed_m_s: float,
    wind_coupling: float = DEFAULT_WIND_COUPLING,
) -> float:
    """Effective distance after wind distortion.

    Computes the distance to use when classifying a hazard at a receptor
    located at `distance_m` from the source, given the prevailing wind.

    Downwind receptors appear closer (effective distance shorter);
    upwind receptors appear farther (effective distance longer);
    crosswind receptors see no distortion.

    Parameters
    ----------
    distance_m
        Real horizontal distance from source to receptor, m. > 0.
    bearing_to_receptor_deg
        Bearing from source to receptor, degrees clockwise from North.
        Convention: 0 = N, 90 = E, 180 = S, 270 = W.
    wind_from_direction_deg
        Direction the wind is coming FROM, degrees clockwise from North.
        0 = wind from North (blowing south).
    wind_speed_m_s
        Wind speed, m/s. ≥ 0.
    wind_coupling
        Wind-coupling constant, s/m. Defaults to 0.1 (CCPS-simplified).

    Returns
    -------
    float
        Effective distance in metres. Clamped to a small positive
        minimum to prevent divide-by-zero pathologies at strong wind.

    Raises
    ------
    ValueError
        On non-positive distance, negative wind speed, or non-positive
        wind coupling.
    """
    if distance_m <= 0:
        raise ValueError(f"distance_m must be positive, got {distance_m}")
    if wind_speed_m_s < 0:
        raise ValueError(f"wind_speed_m_s must be ≥ 0, got {wind_speed_m_s}")
    if wind_coupling <= 0:
        raise ValueError(f"wind_coupling must be > 0, got {wind_coupling}")

    # Wind *blow* direction (where the wind is going) is opposite the
    # "wind-from" direction. The receptor is downwind when its bearing
    # aligns with the blow direction.
    blow_direction = (wind_from_direction_deg + 180.0) % 360.0
    # Angle between bearing and blow direction: 0 = downwind, ±180 = upwind.
    angle_diff = (bearing_to_receptor_deg - blow_direction) % 360.0
    if angle_diff > 180.0:
        angle_diff -= 360.0  # now in (-180, 180]; 0 = downwind, ±180 = upwind
    cos_term = math.cos(math.radians(angle_diff))

    if wind_speed_m_s == 0.0 or cos_term == 0.0:
        return distance_m

    denominator = 1.0 + wind_coupling * wind_speed_m_s * cos_term
    if denominator <= 0.0:
        # Strong upwind case: clamp stretch at 10× (the zone is "infinitely
        # far" upwind — we cap at a finite long-distance asymptote).
        return 10.0 * distance_m
    if denominator < 0.1:
        # Avoid pathological near-zero denominators that produce huge values.
        denominator = 0.1

    stretch = 1.0 / denominator
    stretch = max(0.1, min(stretch, 10.0))
    return stretch * distance_m


def bearing_from_source(
    source_lat: float,
    source_lon: float,
    receptor_lat: float,
    receptor_lon: float,
) -> float:
    """Initial bearing from source to receptor, degrees clockwise from
    North.

    Uses the spherical-law-of-cosines form for simplicity. Accurate
    enough at the meter-scale distances used in the MVP (distortions
    of a degree or two are below the precision of the wind model).

    Parameters
    ----------
    source_lat, source_lon
        Source point, decimal degrees.
    receptor_lat, receptor_lon
        Receptor point, decimal degrees.

    Returns
    -------
    float
        Bearing in degrees, ∈ [0, 360).
    """
    phi1 = math.radians(source_lat)
    phi2 = math.radians(receptor_lat)
    d_lambda = math.radians(receptor_lon - source_lon)

    y = math.sin(d_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda)
    bearing_rad = math.atan2(y, x)
    return math.degrees(bearing_rad) % 360.0


__all__ = [
    "effective_distance",
    "bearing_from_source",
    "DEFAULT_WIND_COUPLING",
]
