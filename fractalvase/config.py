"""Every constant the Douady Helix vase is built from.

Derived quantities are properties, not stored fields, so a change to ``c``
propagates rather than leaving stale Koenigs data behind. See
docs/superpowers/specs/2026-08-09-fractal-julia-vase-design.md.
"""

from __future__ import annotations

import cmath
from dataclasses import dataclass


@dataclass(frozen=True)
class VaseConfig:
    """Geometry and field parameters. All lengths in millimetres."""

    # --- the set ---
    c: complex = -0.123 + 0.745j
    max_iter: int = 100
    escape_r: float = 128.0

    # --- log-polar mapping (spec 2.3) ---
    zeta_min: float = 0.02
    nu_ref: float = 12.0
    periods: int = 4
    invert_scale: bool = False

    # --- envelope and bands ---
    height: float = 300.0
    band_lo: float = 40.0
    band_hi: float = 240.0
    wall: float = 2.0
    # Solid floor separating the outer base from the (otherwise open, z=0)
    # cavity floor. Without it the inner surface runs to z=0 too and the
    # base is a zero-thickness membrane -- a real defect found by building
    # the shell (Task 4), not a slicer nicety. 3.0 mm for a 300 mm vase:
    # stiff and reliable over a brim without wasting material.
    base_thickness: float = 3.0

    # --- relief envelope A(z) (spec 3.1) ---
    relief_peak: float = 7.0
    relief_peak_z: float = 130.0

    # --- piercing: seeded lattice, not a threshold (spec 3.3 rewritten --
    # thresholding nu_hat gives one connected blob, see fractalvase/holes.py) ---
    pierce_lo: float = 150.0
    pierce_hi: float = 225.0
    hole_row_pitch: float = 12.0
    hole_col_pitch: float = 14.0
    hole_open_cut: float = 0.35
    hole_size_min: float = 3.0
    hole_size_max: float = 8.0
    min_ligament: float = 2.0
    max_hole_span: float = 12.0
    arch_apex_deg: float = 45.0

    # --- sampling (spec 4) ---
    n_theta: int = 640
    n_z: int = 500

    # --- band-limiting (spec 4 step 2) ---
    lowpass_sigma_mm: float = 0.5
    lowpass_ref_radius_mm: float = 58.0

    def __post_init__(self) -> None:
        """Validate the invariants the field/geometry code actually depends on.

        escape_r > 1 specifically: smooth_escape's renormalisation divides by
        log(mag), which needs log(mag) > 0, i.e. mag > 1. At escape_r == 1
        that is log(1) == 0 -- division by zero, -inf. Below 1 it is negative
        -- log of a negative number, nan. escape_r == e (2.718...) is fine;
        log(log(e)) == log(1) == 0, a perfectly finite renormalised count.
        """
        if self.escape_r <= 1.0:
            raise ValueError(f"escape_r must be > 1.0 (got {self.escape_r})")
        if not self.band_lo < self.band_hi:
            raise ValueError(f"band_lo must be < band_hi (got {self.band_lo}, {self.band_hi})")
        if self.periods < 1:
            raise ValueError(f"periods must be >= 1 (got {self.periods})")
        if self.zeta_min <= 0.0:
            raise ValueError(f"zeta_min must be > 0 (got {self.zeta_min})")
        if self.wall <= 0.0:
            raise ValueError(f"wall must be > 0 (got {self.wall})")
        if not 0.0 < self.base_thickness < self.height:
            raise ValueError(
                f"base_thickness must be > 0 and < height (got {self.base_thickness}, "
                f"height {self.height})"
            )

    @property
    def alpha(self) -> complex:
        """Repelling fixed point of z^2 + c."""
        return (1 + cmath.sqrt(1 - 4 * self.c)) / 2

    @property
    def mu(self) -> complex:
        """Koenigs multiplier. |mu| is the ornament scale ratio."""
        return 2 * self.alpha

    @property
    def ln_mu(self) -> float:
        return float(cmath.log(abs(self.mu)).real)

    @property
    def arg_mu(self) -> float:
        return float(cmath.phase(self.mu))

    @property
    def band(self) -> float:
        return self.band_hi - self.band_lo

    @property
    def period(self) -> float:
        """Vertical distance over which the pattern reproduces itself."""
        return self.band / self.periods

    @property
    def k(self) -> float:
        """Log-polar rate. One period advances u by exactly ln|mu|."""
        rate = self.ln_mu / self.period
        return -rate if self.invert_scale else rate

    @property
    def twist_rate_rad_per_mm(self) -> float:
        """Screw component: rising one period rotates by exactly arg mu."""
        return self.arg_mu / self.period


DOUADY_HELIX = VaseConfig()
