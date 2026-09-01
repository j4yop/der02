"""Zone computation: orchestrate blast + thermal across a grid.

Given a fuel, tank volume, wind, and a bounding box, compute the hazard
zone records for each grid node.

The orchestrator hides three physical steps behind one interface:
    1. Generate a meter-accurate grid over the bounding box.
    2. For each grid node, compute the great-circle distance and
       bearing from the source, then apply the wind distortion model to
       get an effective distance.
    3. Compute the peak side-on overpressure (TNO blast) and the
       solid-flame thermal flux at that effective distance, and
       classify each into a severity band. The zone record's severity
       is the worst of the two.

Energy / HRR derivation
-----------------------
The blast energy E is the total combustion energy of the participating
vapor cloud. For the MVP we use the textbook assumption that 100 % of
the fuel mass in the tank participates (which gives an upper bound on
the actual energy released in a partial-cloud explosion):

    mass_kg = volume_m3 × vapor_density_kg_m3
    E_J = mass_kg × LHV_kJ_kg × 1000 × combustion_efficiency

The combustion efficiency defaults to 0.4 (typical for a partially
confined vapor cloud explosion, per CCPS Ch. 4 and TNO Green Book
Ch. 6).

The thermal HRR assumes the same mass burns in a pool/jet fire:

    Q_kW = mass_kg × LHV_kJ_kg × 1000 / burn_duration_s

Burn duration uses a simple fixed-ceiling estimate of 10 minutes
(600 s); site-specific data overrides this when available.

Thermal model
-------------
Uses the **solid-flame view-factor model** (Nusselt analog integration
in `der02.thermal.solid_flame_flux`) rather than the simpler
point-source approximation. Flame geometry is computed from the
heat release rate via Heskestad's correlation (flame height) and the
tank diameter (cylinder base). Flame temperature and emissivity come
from the Fuel dataclass.

References
----------
- CCPS *Guidelines for Chemical Process Quantitative Risk Analysis*
  2nd ed. (2000) — chapter 4 (combustion efficiency, blast) and
  chapter 2 (thermal radiation, flame emissivity).
- TNO Green Book / CPR 14E 3rd ed. (2005) — vapor cloud energy scaling.
- Heskestad, G. (1984). "Engineering relations for fire plumes."
  Fire Technology 20(1), 31–43.
- Incropera et al. *Principles of Heat and Mass Transfer* — Nusselt
  analog for view-factor integration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from pyproj import Geod

from .blast import blast_overpressure
from .fuels import Fuel
from .thermal import flame_height_heskestad, solid_flame_flux
from .thresholds import classify_blast, classify_thermal
from .wind import bearing_from_source, effective_distance


@dataclass(frozen=True)
class ZoneRecord:
    """A single point on the hazard-zone grid."""

    lat: float
    lon: float
    severity: str  # "lethal" | "danger" | "caution" | "safe"
    blast_pa: float  # peak side-on overpressure at this point, Pa
    thermal_kw_m2: float  # radiative heat flux at this point, kW/m²
    distance_m: float  # real distance from source, m


@dataclass(frozen=True)
class WindConfig:
    """Wind specification for zone computation."""

    speed_m_s: float
    from_direction_deg: float  # degrees clockwise from North


@dataclass(frozen=True)
class BBox:
    """Bounding box of the computation region (decimal degrees)."""

    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


# Default combustion efficiency for vapor cloud explosions.
DEFAULT_COMBUSTION_EFFICIENCY: float = 0.4

# Default burn duration in seconds for thermal radiation computation.
DEFAULT_BURN_DURATION_S: float = 600.0

# Default tank dimensions for solid-flame geometry (used when caller
# doesn't supply them).
DEFAULT_TANK_DIAMETER_M: float = 10.0
DEFAULT_TANK_HEIGHT_M: float = 10.0

# Default atmospheric transmissivity (clean upper bound).
DEFAULT_TRANSMISSIVITY: float = 1.0


def _grid_nodes(bbox: BBox, resolution_m: float) -> list[tuple[float, float]]:
    """Generate (lat, lon) grid nodes over a bounding box at given meter
    resolution. Uses pyproj.Geod for meter-accurate spacing."""
    if resolution_m <= 0:
        raise ValueError(f"resolution_m must be > 0, got {resolution_m}")

    geod = Geod(ellps="WGS84")
    _, _, dx_m = geod.inv(bbox.min_lon, bbox.min_lat, bbox.max_lon, bbox.min_lat)
    _, _, dy_m = geod.inv(bbox.min_lon, bbox.min_lat, bbox.min_lon, bbox.max_lat)

    n_x = max(1, int(dx_m / resolution_m) + 1)
    n_y = max(1, int(dy_m / resolution_m) + 1)

    nodes: list[tuple[float, float]] = []
    for j in range(n_y):
        frac_y = j / max(1, n_y - 1) if n_y > 1 else 0.5
        lat = bbox.min_lat + frac_y * (bbox.max_lat - bbox.min_lat)
        for i in range(n_x):
            frac_x = i / max(1, n_x - 1) if n_x > 1 else 0.5
            lon = bbox.min_lon + frac_x * (bbox.max_lon - bbox.min_lon)
            nodes.append((lat, lon))
    return nodes


def _great_circle_distance_m(
    source_lat: float, source_lon: float, lat: float, lon: float
) -> float:
    geod = Geod(ellps="WGS84")
    _, _, d_m = geod.inv(source_lon, source_lat, lon, lat)
    return d_m


def _severity_worst(blast_pa: float, thermal_kw_m2: float) -> str:
    """Return the worse of blast and thermal severity at a point."""
    order = {"safe": 0, "caution": 1, "danger": 2, "lethal": 3}
    b = classify_blast(blast_pa)
    t = classify_thermal(thermal_kw_m2)
    return b if order[b] >= order[t] else t


def _tank_diameter_from_volume(volume_m3: float) -> float:
    """Estimate a cylindrical tank diameter (m) from volume assuming
    height equals diameter. Used as a default when the caller doesn't
    supply tank dimensions.
    """
    if volume_m3 <= 0:
        return DEFAULT_TANK_DIAMETER_M
    # V = π · (D/2)² · H, with H = D → V = π · D³/4 → D = (4V/π)^(1/3).
    return (4.0 * volume_m3 / math.pi) ** (1.0 / 3.0)


def compute_zones(
    fuel: Fuel,
    volume_m3: float,
    source_lat: float,
    source_lon: float,
    bbox: BBox,
    wind: WindConfig,
    resolution_m: float = 50.0,
    combustion_efficiency: float = DEFAULT_COMBUSTION_EFFICIENCY,
    burn_duration_s: float = DEFAULT_BURN_DURATION_S,
    tank_diameter_m: float | None = None,
    tank_height_m: float | None = None,
    transmissivity: float = DEFAULT_TRANSMISSIVITY,
) -> list[ZoneRecord]:
    """Compute hazard zones over a grid.

    Parameters
    ----------
    fuel
        The fuel substance (from `der02.fuels`).
    volume_m3
        Tank volume in cubic metres. For gases stored under pressure, use
        the *equivalent liquid* volume (i.e. mass ÷ liquid density).
    source_lat, source_lon
        Tank location, decimal degrees.
    bbox
        Bounding box of the region to model.
    wind
        Wind configuration (speed and from-direction).
    resolution_m
        Grid spacing, metres. Default 50 m.
    combustion_efficiency
        Fraction of fuel energy participating in the blast, dimensionless
        ∈ (0, 1]. Default 0.4 (TNO / CCPS typical).
    burn_duration_s
        Burn duration for thermal HRR computation, seconds. Default 600.
    tank_diameter_m
        Cylindrical tank diameter, m. If None, derived from volume.
    tank_height_m
        Cylindrical tank height, m. If None, equals tank_diameter_m.
    transmissivity
        Atmospheric transmissivity, dimensionless ∈ (0, 1]. Default 1.0.

    Returns
    -------
    list[ZoneRecord]
        One record per grid node.
    """
    if volume_m3 <= 0:
        raise ValueError(f"volume_m3 must be > 0, got {volume_m3}")
    if not 0 < combustion_efficiency <= 1:
        raise ValueError(
            f"combustion_efficiency must be in (0, 1], got {combustion_efficiency}"
        )
    if burn_duration_s <= 0:
        raise ValueError(f"burn_duration_s must be > 0, got {burn_duration_s}")
    if not 0 < transmissivity <= 1:
        raise ValueError(
            f"transmissivity must be in (0, 1], got {transmissivity}"
        )

    mass_kg = volume_m3 * fuel.vapor_density_kg_m3

    energy_joules = (
        mass_kg
        * fuel.lhv_kj_kg
        * 1000.0
        * combustion_efficiency
    )

    heat_release_rate_kw = (
        mass_kg
        * fuel.lhv_kj_kg
        * 1000.0
        / burn_duration_s
    )

    if tank_diameter_m is None:
        tank_diameter_m = _tank_diameter_from_volume(volume_m3)
    if tank_height_m is None:
        tank_height_m = tank_diameter_m
    if tank_diameter_m <= 0 or tank_height_m <= 0:
        raise ValueError(
            f"tank_diameter_m and tank_height_m must be > 0, "
            f"got {tank_diameter_m}, {tank_height_m}"
        )

    flame_height_m = flame_height_heskestad(
        heat_release_rate_kw=heat_release_rate_kw,
        pool_diameter_m=tank_diameter_m,
    )
    flame_height_m = max(flame_height_m, 1.0)
    flame_diameter_m = tank_diameter_m

    nodes = _grid_nodes(bbox, resolution_m)
    records: list[ZoneRecord] = []
    for lat, lon in nodes:
        distance_m = _great_circle_distance_m(source_lat, source_lon, lat, lon)
        bearing = bearing_from_source(source_lat, source_lon, lat, lon)

        distance_for_wind = max(distance_m, resolution_m / 2.0)

        eff_d = effective_distance(
            distance_m=distance_for_wind,
            bearing_to_receptor_deg=bearing,
            wind_from_direction_deg=wind.from_direction_deg,
            wind_speed_m_s=wind.speed_m_s,
        )

        eff_d_clamped = max(0.1, eff_d)

        blast_pa = blast_overpressure(
            distance_m=eff_d_clamped, energy_joules=energy_joules
        )
        thermal_kw_m2 = solid_flame_flux(
            distance_m=eff_d_clamped,
            flame_height_m=flame_height_m,
            flame_diameter_m=flame_diameter_m,
            flame_temperature_k=fuel.flame_temperature_k,
            emissivity=fuel.emissivity,
            transmissivity=transmissivity,
        )

        severity = _severity_worst(blast_pa, thermal_kw_m2)
        records.append(
            ZoneRecord(
                lat=lat,
                lon=lon,
                severity=severity,
                blast_pa=blast_pa,
                thermal_kw_m2=thermal_kw_m2,
                distance_m=distance_m,
            )
        )
    return records


__all__ = [
    "ZoneRecord",
    "WindConfig",
    "BBox",
    "compute_zones",
    "DEFAULT_COMBUSTION_EFFICIENCY",
    "DEFAULT_BURN_DURATION_S",
    "DEFAULT_TANK_DIAMETER_M",
    "DEFAULT_TANK_HEIGHT_M",
    "DEFAULT_TRANSMISSIVITY",
]
