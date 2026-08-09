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

    # --- relief envelope A(z) (spec 3.1) ---
    relief_peak: float = 7.0
    relief_peak_z: float = 130.0

    # --- piercing (spec 3.3) ---
    pierce_threshold: float = 0.62
    min_ligament: float = 2.0
    max_hole_span: float = 12.0
    arch_apex_deg: float = 45.0

    # --- sampling (spec 4) ---
    n_theta: int = 640
    n_z: int = 500

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
