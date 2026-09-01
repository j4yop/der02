"""Zone computation: orchestrate blast + thermal across a grid.

Given a fuel, tank volume, wind, and a bounding box, compute the hazard
zone records for each grid node.

The orchestrator hides three physical steps behind one interface:
    1. Generate a meter-accurate grid over the bounding box.
    2. For each grid node, compute the great-circle distance and
       bearing from the source, then apply the wind distortion model to
       get an effective distance.
    3. Compute the peak side-on overpressure (TNO blast) and the
       point-source thermal flux at that effective distance, and
       classify each into a severity band. The zone record's severity is
       the worst of the two.

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

Burn duration is computed from a simple mass-burning-rate model: a
default 0.05 kg/(m²·s) for liquids, scaled by the tank surface area.
For the MVP we use a fixed 10-minute (600 s) burn duration as a simple
ceiling estimate; site-specific data overrides this when available.

References
----------
- CCPS *Guidelines for Chemical Process Quantitative Risk Analysis*
  2nd ed. (2000) — chapter 4 (combustion efficiency, blast) and
  chapter 2 (thermal radiation).
- TNO Green Book / CPR 14E 3rd ed. (2005) — vapor cloud energy scaling.
"""

from __future__ import annotations

from dataclasses import dataclass

from pyproj import Geod

from .blast import blast_overpressure
from .fuels import Fuel
from .thermal import point_source_flux
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
# Used to translate total combustion energy to a heat release rate (kW).
# 10 minutes is a common upper-bound for "rapid" pool fires; site-specific
# data overrides this.
DEFAULT_BURN_DURATION_S: float = 600.0


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

    # Total mass participating (upper bound: 100 % of tank contents).
    mass_kg = volume_m3 * fuel.vapor_density_kg_m3

    # Blast energy (J).
    energy_joules = (
        mass_kg
        * fuel.lhv_kj_kg
        * 1000.0
        * combustion_efficiency
    )

    # Thermal HRR (kW). Total combustion energy divided by burn duration.
    heat_release_rate_kw = (
        mass_kg
        * fuel.lhv_kj_kg
        * 1000.0
        / burn_duration_s
    )

    nodes = _grid_nodes(bbox, resolution_m)
    records: list[ZoneRecord] = []
    for lat, lon in nodes:
        distance_m = _great_circle_distance_m(source_lat, source_lon, lat, lon)
        bearing = bearing_from_source(source_lat, source_lon, lat, lon)

        # The source point itself is at distance 0 — clamp to half the
        # grid resolution so the wind model can be called.
        distance_for_wind = max(distance_m, resolution_m / 2.0)

        eff_d = effective_distance(
            distance_m=distance_for_wind,
            bearing_to_receptor_deg=bearing,
            wind_from_direction_deg=wind.from_direction_deg,
            wind_speed_m_s=wind.speed_m_s,
        )

        # Clamp effective distance to a sensible minimum so blast /
        # thermal calls don't divide by zero at the source point.
        eff_d_clamped = max(0.1, eff_d)

        blast_pa = blast_overpressure(distance_m=eff_d_clamped, energy_joules=energy_joules)
        thermal_kw_m2 = point_source_flux(
            distance_m=eff_d_clamped,
            heat_release_rate_kw=heat_release_rate_kw,
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
]
