"""Vase silhouette and relief envelope.

The profile is a piecewise-linear set of breakpoints, smoothed so it reads
as a vase rather than a chart. Relief A(z) is a raised cosine on both sides
of its peak: zero-valued AND zero-slope at both band ends, so ornament
emerges from the quiet zones without a visible start line.
"""

from __future__ import annotations

import numpy as np

from fractalvase.config import VaseConfig

# (z mm, diameter mm) -- spec section 3.1
BREAKPOINTS: tuple[tuple[float, float], ...] = (
    (0.0, 70.0),
    (40.0, 80.0),
    (150.0, 112.0),
    (185.0, 116.0),
    (225.0, 96.0),
    (240.0, 78.0),
    (262.0, 58.0),
    (300.0, 68.0),
)

_ZS = np.array([b[0] for b in BREAKPOINTS])
_RS = np.array([b[1] / 2.0 for b in BREAKPOINTS])


def radius_at(z: np.ndarray) -> np.ndarray:
    """Piecewise-linear radius, in mm."""
    return np.interp(np.asarray(z, dtype=float), _ZS, _RS)


def smooth_radius(z: np.ndarray, window: float = 9.0, samples: int = 13) -> np.ndarray:
    """Box-average the piecewise profile so breakpoints read as curves.

    The inner wall is built from this, never from the relief-bearing outer
    surface: an inward offset of a detailed surface self-intersects wherever
    the wall thickness exceeds the local radius of curvature.
    """
    z = np.asarray(z, dtype=float)
    offsets = np.linspace(-window, window, samples)
    stack = np.stack([radius_at(np.clip(z + d, 0.0, 300.0)) for d in offsets])
    return stack.mean(axis=0)


def relief_amplitude(z: np.ndarray, cfg: VaseConfig) -> np.ndarray:
    """A(z): raised cosine rising to relief_peak, then falling to zero."""
    z = np.asarray(z, dtype=float)
    out = np.zeros_like(z)

    lo, pk, hi = cfg.band_lo, cfg.relief_peak_z, cfg.band_hi
    rise = (z >= lo) & (z <= pk)
    fall = (z > pk) & (z <= hi)

    out[rise] = cfg.relief_peak * (1 - np.cos(np.pi * (z[rise] - lo) / (pk - lo))) / 2
    out[fall] = cfg.relief_peak * (1 + np.cos(np.pi * (z[fall] - pk) / (hi - pk))) / 2
    return out


def max_slope(cfg: VaseConfig) -> float:
    """Worst-case |grad r|, composing profile taper, relief and helical lean.

    Deliberately pessimistic: it stacks the steepest taper against the peak
    relief gradient and the twist drift at maximum radius, which do not
    co-occur. Spec section 3.4 records 0.8339 -> 39.82 degrees.
    """
    z = np.linspace(0.0, 300.0, 30001)

    seg = np.abs(np.diff(_RS) / np.diff(_ZS)).max()
    relief_grad = np.abs(np.gradient(relief_amplitude(z, cfg), z)).max()
    meridional = seg + relief_grad

    r_max = _RS.max()
    tangential = r_max * abs(cfg.twist_rate_rad_per_mm)

    return float(np.hypot(meridional, tangential))
