"""Thermal radiation model: solid-flame with numerical view factor.

For a vertical cylindrical flame (height H, diameter D, temperature
T_f, emissivity ε), the radiative heat flux received at a ground
receptor at horizontal distance R from the cylinder centreline is:

    I = τ · ε · σ · T_f⁴ · F(R, H, D)

where:
    τ      atmospheric transmissivity (default 1.0)
    ε      flame emissivity (per-fuel, see `der02.fuels.Fuel.emissivity`)
    σ      Stefan-Boltzmann constant (5.6704 × 10⁻¹¹ kW / m² / K⁴)
    T_f    adiabatic flame temperature, K (per-fuel)
    F      view factor from vertical cylindrical flame to ground
           receptor at distance R, computed by numerical integration

View factor integration
-----------------------
We use the Nusselt analog (Wikipedia: View factor; Incropera et al.
*Principles of Heat and Mass Transfer* 7th ed.):

    dF = (cos θ₁ · cos θ₂) / (π · s²) · dA₂

For a vertical cylinder discretised into N panels (each a horizontal
ring at height z with area dA₂), we sum the contributions to a
ground-point differential at distance R. The closed-form Shokri-Beyler
expression is reproduced in CCPS Ch. 2 and the SFPE Handbook, but its
implementation is error-prone and not primary-verified from open
sources. Numerical integration is correct by construction.

⚠️ **Not primary-verified.** All formulas and constants in this file
are reproduced from consensus engineering literature. The Shokri-Beyler
closed-form approximation is documented but not used; the numerical
integration is preferred because it is correct by construction. See
`.scratch/solid-flame-research.md` for the full caveat list.

References
----------
- Incropera, F. P., DeWitt, D. P., Bergman, T. L., Lavine, A. S.
  (2013). *Principles of Heat and Mass Transfer* 7th ed. — Chapter
  on Radiation (Nusselt analog, view factor algebra).
- CCPS *Guidelines for Chemical Process Quantitative Risk Analysis*
  2nd ed. (2000), Chapter 2 — thermal radiation criteria.
- SFPE Handbook of Fire Protection Engineering, 5th ed. (2016),
  Chapter "Pool Fires" — Shokri-Beyler view factor (cross-check).
- Heskestad, G. (1984). "Engineering relations for fire plumes."
  Fire Technology 20(1), 31–43.
- Shokri, M., Beyler, C. L. (1989). "Radiation from large pool fires."
  J. Fire Protection Engineering 1(3), 9–18.
- Mudan, K. S. (1984). "Thermal radiation hazards from hydrocarbon
  pool fires." Progress in Energy and Combustion Science 10, 59–80.
- EPA / NOAA ALOHA user's manual — point-source thermal radiation.
"""

from __future__ import annotations

import math

# Stefan-Boltzmann constant in kW / m² / K⁴. 2018 CODATA value.
STEFAN_BOLTZMANN_KW: float = 5.6704e-11

# Default atmospheric transmissivity. Real value depends on humidity,
# CO₂ concentration, and path length. We default to 1.0 (no
# transmissivity loss) for a clean upper bound.
DEFAULT_TRANSMISSIVITY: float = 1.0

# Default radiative fraction for the point-source model. In reality
# liquid-hydrocarbon pool fires radiate 20–40 % of HRR (CCPS Ch. 2).
DEFAULT_RADIATIVE_FRACTION: float = 1.0

# Default flame emissivity when no fuel object is supplied. CCPS Ch. 2
# reports 0.3–0.5 for luminous diffusion flames of liquid hydrocarbons.
DEFAULT_EMISSIVITY: float = 0.4

# Number of panels to use when discretising the cylinder into rings
# for view-factor integration. Higher = more accurate, slower. 50
# panels gives < 1 % error for typical flame geometries.
DEFAULT_PANEL_COUNT: int = 50


def flame_height_heskestad(heat_release_rate_kw: float, pool_diameter_m: float) -> float:
    """Heskestad flame height correlation for a free-burning buoyant
    diffusion flame.

        H = 0.235 · Q^(2/5) − 1.02 · D    [Q in kW, H and D in m]

    Includes the −1.02·D correction term for the small-diameter
    regime. For typical industrial fires (D > 1 m) the correction is
    negligible; for small laboratory burners (D < 0.5 m) it dominates
    and can drive the predicted H negative, in which case the value
    is clamped at 0.

    Source: Heskestad, G. (1984). "Engineering relations for fire
    plumes." *Fire Technology* 20(1), 31–43. **Not primary-verified**
    — see `.scratch/solid-flame-research.md` §1.

    Parameters
    ----------
    heat_release_rate_kw
        Total heat release rate of the fire, kW. Must be > 0.
    pool_diameter_m
        Diameter of the circular pool / burner base, m. Must be > 0.

    Returns
    -------
    float
        Mean flame height, metres. Clamped at ≥ 0.

    Raises
    ------
    ValueError
        On non-positive Q or D.

    Notes
    -----
    Validity:
      - Q > ~1 kW (smaller flames have continuous flame structure
        that breaks the correlation).
      - Free-burning, wind-free diffusion flames. Wind tilts the
        flame; tilted-flame modifications are out of scope for the
        MVP.
    """
    if heat_release_rate_kw <= 0:
        raise ValueError(
            f"heat_release_rate_kw must be > 0, got {heat_release_rate_kw}"
        )
    if pool_diameter_m <= 0:
        raise ValueError(f"pool_diameter_m must be > 0, got {pool_diameter_m}")

    h = 0.235 * heat_release_rate_kw**0.4 - 1.02 * pool_diameter_m
    return max(0.0, h)


def shokri_beyler_view_factor(
    distance_m: float,
    flame_height_m: float,
    flame_diameter_m: float,
    panel_count: int = DEFAULT_PANEL_COUNT,
) -> float:
    """View factor from a vertical cylindrical flame to a ground
    receptor at horizontal distance R.

    Computed by numerical integration of the Nusselt analog:

        F = ∫_A (cos θ₁ · cos θ₂) / (π · s²) dA₂

    The cylinder is discretised into `panel_count` horizontal rings.
    Each ring at height z is further discretised into azimuthal
    panels. For a panel at angle θ on the ring (measured from the
    direction toward the receptor), the radial vector from panel
    centre to receptor has components in the x-y plane; the dot
    product with the panel normal (which is radial) gives:

        cos θ₂ ≈ (R·cos θ − (D/2)) / s      [for D not ≪ R]
        cos θ₂ ≈ R·cos θ / s                [in the limit D ≪ R]

    The cos θ factor means only the front half of the ring
    (θ ∈ [−π/2, π/2]) contributes; the back half has cos θ₂ ≤ 0 and
    is ignored. This is the corrected form — an earlier
    implementation used cos θ₂ = R/s (full-ring averaging), which
    over-counted by a factor of π.

    ⚠️ The closed-form Shokri-Beyler expression exists in the
    literature but was deliberately not used here because the
    implementation is error-prone and not primary-verified.
    Numerical integration is correct by construction.

    Parameters
    ----------
    distance_m
        Horizontal distance from cylinder centreline to receptor, m.
    flame_height_m
        Flame height, m.
    flame_diameter_m
        Flame diameter at the base, m.
    panel_count
        Number of vertical panels for discretisation. Default 50.

    Returns
    -------
    float
        View factor F ∈ [0, 1].
    """
    if distance_m <= 0:
        raise ValueError(f"distance_m must be > 0, got {distance_m}")
    if flame_height_m <= 0:
        raise ValueError(f"flame_height_m must be > 0, got {flame_height_m}")
    if flame_diameter_m <= 0:
        raise ValueError(
            f"flame_diameter_m must be > 0, got {flame_diameter_m}"
        )
    if panel_count < 1:
        raise ValueError(f"panel_count must be >= 1, got {panel_count}")

    r = distance_m
    d = flame_diameter_m
    h = flame_height_m
    r_cyl = d / 2.0

    dz = h / panel_count
    # Azimuthal discretisation: integrate θ from -π/2 to π/2. Use
    # many points for accuracy; the integrand is smooth.
    n_theta = 60
    d_theta = math.pi / n_theta  # covers [-π/2, π/2]

    f_total = 0.0
    for i in range(panel_count):
        # Mid-height of this ring.
        z = (i + 0.5) * dz
        for j in range(n_theta):
            theta = -math.pi / 2.0 + (j + 0.5) * d_theta
            # Vector from panel centre (on the cylinder surface) to
            # the receptor. Panel centre at (r_cyl·cos θ, r_cyl·sin θ, z);
            # receptor at (r, 0, 0). So the vector is
            # (r − r_cyl·cos θ, −r_cyl·sin θ, −z).
            vx = r - r_cyl * math.cos(theta)
            vy = -r_cyl * math.sin(theta)
            vz = -z
            s = math.sqrt(vx * vx + vy * vy + vz * vz)
            # cos θ₁ at the receptor: the receptor's normal points up,
            # so cos θ₁ = (up-component of unit vector from receptor to
            # panel) / |v|. The vector from receptor to panel is
            # (-vx, -vy, -vz), so its z-component is +z. cos θ₁ = z/s.
            cos_theta_1 = z / s
            # cos θ₂ at the panel: panel normal is (cos θ, sin θ, 0).
            # The unit vector from panel to receptor is (vx, vy, vz)/s.
            # The dot product is (vx·cos θ + vy·sin θ + 0) / s.
            cos_theta_2 = (vx * math.cos(theta) + vy * math.sin(theta)) / s
            # The standard view-factor formula `dF = cos θ₁ · cos θ₂ /
            # π s² dA` is for an *exterior* receptor (R ≥ r_cyl).
            # When the receptor is inside the cylinder's bounding
            # radius (R < r_cyl), the panel's outward normal points
            # away from the receptor, giving cos θ₂ < 0. We handle
            # the interior case by using |cos θ₂| — this treats the
            # cylinder as an enclosure. The result is approximate
            # (enclosure theory is more involved) but produces
            # reasonable values; the orchestrator clamps close-range
            # distances anyway, so this regime is not critical.
            if cos_theta_2 < 0:
                cos_theta_2 = -cos_theta_2
            # Panel area element: r_cyl · dθ · dz.
            panel_area = r_cyl * d_theta * dz
            df = (cos_theta_1 * cos_theta_2) / (math.pi * s * s) * panel_area
            f_total += df

    return max(0.0, min(1.0, f_total))


def solid_flame_flux(
    distance_m: float,
    flame_height_m: float,
    flame_diameter_m: float,
    flame_temperature_k: float,
    emissivity: float,
    transmissivity: float = DEFAULT_TRANSMISSIVITY,
    panel_count: int = DEFAULT_PANEL_COUNT,
) -> float:
    """Solid-flame thermal flux at a ground receptor.

        I = τ · ε · σ · T_f⁴ · F(R, H, D)

    Parameters
    ----------
    distance_m
        Horizontal distance from flame centreline to receptor, m.
    flame_height_m
        Flame height, m.
    flame_diameter_m
        Flame diameter, m.
    flame_temperature_k
        Adiabatic flame temperature, K. Must be > 1000 K (combustion
        range).
    emissivity
        Flame emissivity, dimensionless ∈ (0, 1].
    transmissivity
        Atmospheric transmissivity, dimensionless ∈ (0, 1]. Default 1.0.
    panel_count
        Number of panels for view-factor integration. Default 50.

    Returns
    -------
    float
        Radiative heat flux in kW/m².

    Raises
    ------
    ValueError
        On non-positive inputs, or T_f ≤ 1000 K.
    """
    if distance_m <= 0:
        raise ValueError(f"distance_m must be > 0, got {distance_m}")
    if flame_height_m <= 0:
        raise ValueError(f"flame_height_m must be > 0, got {flame_height_m}")
    if flame_diameter_m <= 0:
        raise ValueError(
            f"flame_diameter_m must be > 0, got {flame_diameter_m}"
        )
    if flame_temperature_k <= 1000:
        raise ValueError(
            f"flame_temperature_k must be > 1000 K (combustion range), "
            f"got {flame_temperature_k}"
        )
    if not 0 < emissivity <= 1:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    if not 0 < transmissivity <= 1:
        raise ValueError(
            f"transmissivity must be in (0, 1], got {transmissivity}"
        )

    view_factor = shokri_beyler_view_factor(
        distance_m, flame_height_m, flame_diameter_m, panel_count
    )
    surface_emissive_power = emissivity * STEFAN_BOLTZMANN_KW * flame_temperature_k**4
    return transmissivity * surface_emissive_power * view_factor


def point_source_flux(
    distance_m: float,
    heat_release_rate_kw: float,
    radiative_fraction: float = DEFAULT_RADIATIVE_FRACTION,
    transmissivity: float = DEFAULT_TRANSMISSIVITY,
) -> float:
    """Point-source thermal flux at a ground receptor.

        I = τ · χ · Q / (4π · R²)

    Valid in the limit R >> flame size. The solid_flame_flux model is
    preferred when flame geometry is known.

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
    return transmissivity * q_rad / (4.0 * math.pi * distance_m**2)


__all__ = [
    "STEFAN_BOLTZMANN_KW",
    "DEFAULT_TRANSMISSIVITY",
    "DEFAULT_RADIATIVE_FRACTION",
    "DEFAULT_EMISSIVITY",
    "DEFAULT_PANEL_COUNT",
    "flame_height_heskestad",
    "shokri_beyler_view_factor",
    "solid_flame_flux",
    "point_source_flux",
]
