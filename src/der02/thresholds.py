"""Severity classification for blast overpressure and thermal radiation.

Thresholds sourced from CCPS *Guidelines for Chemical Process Quantitative
Risk Analysis* (2nd ed., 2000). Every band carries a citation in its source.
"""

from __future__ import annotations

from typing import Final

# Blast overpressure severity bands.
#
# Source: CCPS *Guidelines for Chemical Process Quantitative Risk Analysis*
# 2nd ed. (2000), Chapter 4 "Overpressure Damage Criteria". The bands below
# are the standard "lethal / dangerous / caution" thresholds used in PHAST,
# EFFECTS, and ALOHA.
#
# - > 100 kPa (1.0 bar): reinforced concrete damage, ~100% fatality at impact.
# - > 30 kPa (0.3 bar): eardrum rupture, some fatalities, brick walls fail.
# - > 10 kPa (0.1 bar): minor injuries, glass shatters, light injuries.
# - <= 10 kPa: generally safe for people outdoors.
BLAST_BANDS: Final[tuple[tuple[float, str], ...]] = (
    (100_000.0, "lethal"),
    (30_000.0, "danger"),
    (10_000.0, "caution"),
)

# Thermal radiation severity bands.
#
# Source: CCPS *Guidelines for Chemical Process Quantitative Risk Analysis*
# 2nd ed. (2000), Chapter 2 "Thermal Radiation". Standard "lethal / dangerous
# / caution" thresholds used across the consequence-modeling literature
# (Eisenberg, Mudan, TNO).
#
# - > 37.5 kW/m^2: unsurvivable in seconds, equipment damage.
# - > 12.5 kW/m^2: second-degree burns in ~30 s, wood ignition with prolonged
#   exposure, fatalities likely without shelter.
# - > 4 kW/m^2: pain within seconds, first-degree burns with prolonged
#   exposure; the standard "evacuate" threshold.
# - <= 4 kW/m^2: generally safe for people outdoors.
THERMAL_BANDS: Final[tuple[tuple[float, str], ...]] = (
    (37.5, "lethal"),
    (12.5, "danger"),
    (4.0, "caution"),
)


def classify_blast(overpressure_pa: float) -> str:
    """Classify blast overpressure into a severity band.

    >>> classify_blast(150_000)
    'lethal'
    >>> classify_blast(50_000)
    'danger'
    >>> classify_blast(15_000)
    'caution'
    >>> classify_blast(5_000)
    'safe'
    """
    for threshold, severity in BLAST_BANDS:
        if overpressure_pa > threshold:
            return severity
    return "safe"


def classify_thermal(flux_kw_m2: float) -> str:
    """Classify thermal radiation flux into a severity band.

    >>> classify_thermal(50.0)
    'lethal'
    >>> classify_thermal(20.0)
    'danger'
    >>> classify_thermal(6.0)
    'caution'
    >>> classify_thermal(1.0)
    'safe'
    """
    for threshold, severity in THERMAL_BANDS:
        if flux_kw_m2 > threshold:
            return severity
    return "safe"


__all__ = [
    "BLAST_BANDS",
    "THERMAL_BANDS",
    "classify_blast",
    "classify_thermal",
]
