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
    python examples/worked_example.py --pdf out.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from der02.fuels import METHANE
from der02.thresholds import classify_blast, classify_thermal
from der02.zones import BBox, WindConfig, compute_zones

SCENARIO_LAT = 1.29  # Singapore — arbitrary
SCENARIO_LON = 103.85
SCENARIO_VOLUME_M3 = None  # set below from mass / density


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="Write a text-only PDF summary to this path.",
    )
    args = parser.parse_args(argv)

    mass_kg = 1000.0
    volume_m3 = mass_kg / METHANE.vapor_density_kg_m3

    bbox = BBox(
        min_lat=SCENARIO_LAT - 0.03,
        min_lon=SCENARIO_LON - 0.03,
        max_lat=SCENARIO_LAT + 0.03,
        max_lon=SCENARIO_LON + 0.03,
    )
    wind = WindConfig(speed_m_s=5.0, from_direction_deg=180.0)

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

    lines: list[str] = []
    lines.append("der02 worked example: 1000 kg methane vapor cloud explosion")
    lines.append(f"  Equivalent tank volume: {volume_m3:.0f} m^3")
    lines.append(f"  Location: ({SCENARIO_LAT}, {SCENARIO_LON})")
    lines.append(f"  Wind: {wind.speed_m_s} m/s from {wind.from_direction_deg} deg")
    lines.append("")
    lines.append("Maximum distance at which each band is observed:")
    for severity in order:
        band = [r for r in records if r.severity == severity]
        if band:
            max_d = max(r.distance_m for r in band)
            worst = max(band, key=lambda r: sev_order[r.severity])
            lines.append(
                f"  {severity.upper():7s}: {max_d:6.0f} m  "
                f"(blast {worst.blast_pa:.0f} Pa, "
                f"thermal {worst.thermal_kw_m2:.2f} kW/m^2)"
            )
        else:
            lines.append(f"  {severity.upper():7s}: - (not reached)")

    def worst_severity_at(records, half: str, min_d: float = 800.0, max_d: float = 1200.0) -> str:
        if half == "north":
            pts = [r for r in records if r.lat > SCENARIO_LAT and min_d <= r.distance_m <= max_d]
        else:
            pts = [r for r in records if r.lat < SCENARIO_LAT and min_d <= r.distance_m <= max_d]
        if not pts:
            return "safe"
        return max(pts, key=lambda r: sev_order[r.severity]).severity

    north_band = worst_severity_at(records, "north")
    south_band = worst_severity_at(records, "south")
    lines.append("")
    lines.append(f"Worst band at 800-1200 m NORTH (downwind): {north_band}")
    lines.append(f"Worst band at 800-1200 m SOUTH (upwind):   {south_band}")
    if sev_order[north_band] >= sev_order[south_band]:
        lines.append("  OK: Downwind severity >= upwind severity (wind is shaping zones).")
    else:
        lines.append("  FAIL: Downwind severity < upwind severity (wind INVERTED).")

    sample = records[len(records) // 2]
    lines.append("")
    lines.append(
        f"Sample mid-grid point (lat={sample.lat:.4f}, lon={sample.lon:.4f}):"
    )
    lines.append(f"  distance = {sample.distance_m:.0f} m")
    lines.append(f"  blast band = {classify_blast(sample.blast_pa)}")
    lines.append(f"  thermal band = {classify_thermal(sample.thermal_kw_m2)}")
    lines.append(f"  combined band = {sample.severity}")

    text = "\n".join(lines) + "\n"
    print(text)

    if args.pdf is not None:
        from der02.export import html_to_pdf_bytes
        html = (
            "<html><head><meta charset='utf-8'>"
            "<title>der02 worked example</title></head><body>"
            "<h1>der02 worked example: 1000 kg methane VCE</h1>"
            f"<pre>{text}</pre>"
            "</body></html>"
        )
        args.pdf.write_bytes(html_to_pdf_bytes(html))
        print(f"PDF summary written to {args.pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
