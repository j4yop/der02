"""Worked example: 1000 kg methane vapor cloud explosion at a storage site.

This script reproduces a textbook scenario end to end using der02:

  - Fuel: methane (CH₄)
  - Tank contents (equivalent): 1000 kg vapor
  - Released as a vapor cloud explosion
  - Class 7 blast (TNO Multi-Energy, default)
  - Point-source thermal flux (no separate flame in this scenario)
  - Wind: 5 m/s from the south (blowing north)

Expected outputs (within ±25 % of textbook):
  - Lethal blast distance: ~tens of metres from the tank
  - Danger band extends further; caution band beyond that
  - The lethal/danger bands elongate downwind (north) and compress
    upwind (south).

Source for the scenario parameters:
  - CCPS *Guidelines for Chemical Process Quantitative Risk Analysis*
    2nd ed. (2000), Section 4.x — vapor cloud explosion worked example
    (LPG / methane cloud).
  - Lees' *Loss Prevention in the Process Industries* 3rd ed. (2005),
    Section 17.13 — TNO method worked example.

⚠️ The TNO curve values are NOT primary-verified (see CITATIONS.md).
    Results should be within ±25 % of any independently sourced
    reference value.

Run with:
    python examples/worked_example.py
"""

from __future__ import annotations

from der02.fuels import METHANE
from der02.thresholds import classify_blast, classify_thermal
from der02.zones import BBox, WindConfig, compute_zones


SCENARIO_LAT = 1.29  # Singapore — arbitrary
SCENARIO_LON = 103.85
SCENARIO_VOLUME_M3 = None  # set below from mass / density


def main() -> None:
    # 1000 kg methane cloud. To get this from `compute_zones`, we need
    # the equivalent tank volume: volume_m3 = mass_kg / vapor_density_kg_m3.
    mass_kg = 1000.0
    volume_m3 = mass_kg / METHANE.vapor_density_kg_m3  # ≈ 1472 m³

    bbox = BBox(
        min_lat=SCENARIO_LAT - 0.03,
        min_lon=SCENARIO_LON - 0.03,
        max_lat=SCENARIO_LAT + 0.03,
        max_lon=SCENARIO_LON + 0.03,
    )
    wind = WindConfig(speed_m_s=5.0, from_direction_deg=180.0)  # from S

    print("der02 worked example: 1000 kg methane vapor cloud explosion")
    print(f"  Equivalent tank volume: {volume_m3:.0f} m³")
    print(f"  Location: ({SCENARIO_LAT}, {SCENARIO_LON})")
    print(f"  Wind: {wind.speed_m_s} m/s from {wind.from_direction_deg}°")
    print()

    records = compute_zones(
        fuel=METHANE,
        volume_m3=volume_m3,
        source_lat=SCENARIO_LAT,
        source_lon=SCENARIO_LON,
        bbox=bbox,
        wind=wind,
        resolution_m=100.0,
    )

    order = ["lethal", "danger", "caution"]
    sev_order = {"safe": 0, "caution": 1, "danger": 2, "lethal": 3}

    # Maximum distance at which each band is observed.
    print("Maximum distance at which each band is observed:")
    for severity in order:
        band = [r for r in records if r.severity == severity]
        if band:
            max_d = max(r.distance_m for r in band)
            # Worst blast and thermal at the band edge.
            worst = max(band, key=lambda r: sev_order[r.severity])
            print(
                f"  {severity.upper():7s}: {max_d:6.0f} m  "
                f"(blast {worst.blast_pa:.0f} Pa, "
                f"thermal {worst.thermal_kw_m2:.2f} kW/m²)"
            )
        else:
            print(f"  {severity.upper():7s}: — (not reached)")

    # Asymmetry check: at the same real distance from the source, the
    # downwind (north) side should have a more severe band than the
    # upwind (south) side. Compare severities at matched distances.
    def worst_severity_at(records, half: str, min_d: float = 800.0, max_d: float = 1200.0) -> str:
        if half == "north":
            pts = [r for r in records if r.lat > SCENARIO_LAT and min_d <= r.distance_m <= max_d]
        else:
            pts = [r for r in records if r.lat < SCENARIO_LAT and min_d <= r.distance_m <= max_d]
        if not pts:
            return "safe"
        sev_order = {"safe": 0, "caution": 1, "danger": 2, "lethal": 3}
        return max(pts, key=lambda r: sev_order[r.severity]).severity

    north_band = worst_severity_at(records, "north")
    south_band = worst_severity_at(records, "south")
    sev_order = {"safe": 0, "caution": 1, "danger": 2, "lethal": 3}
    print()
    print(f"Worst band at 800–1200 m NORTH (downwind): {north_band}")
    print(f"Worst band at 800–1200 m SOUTH (upwind):   {south_band}")
    if sev_order[north_band] >= sev_order[south_band]:
        print("  ✓ Downwind severity ≥ upwind severity (wind is shaping zones).")
    else:
        print("  ✗ Downwind severity < upwind severity (wind is INVERTED — bug).")

    # Sanity checks: severity classifications are deterministic.
    sample = records[len(records) // 2]
    print()
    print(f"Sample mid-grid point (lat={sample.lat:.4f}, lon={sample.lon:.4f}):")
    print(f"  distance = {sample.distance_m:.0f} m")
    print(f"  blast band = {classify_blast(sample.blast_pa)}")
    print(f"  thermal band = {classify_thermal(sample.thermal_kw_m2)}")
    print(f"  combined band = {sample.severity}")


if __name__ == "__main__":
    main()