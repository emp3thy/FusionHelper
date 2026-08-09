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

    Samples that fall outside [0, 300] are taken by slope-preserving (odd)
    reflection about the nearest edge -- ``2*radius_at(edge) -
    radius_at(mirror)`` -- not by clamping to the edge value. At the exact
    edges (z=0, z=300) this reproduces radius_at(edge) EXACTLY for any
    window: the reflected term and the direct term it's paired with are
    the same sampled values reindexed, so they cancel algebraically
    regardless of window size or the boundary segment's shape (verified up
    to window=250 mm). What the guard below actually protects is the
    general near-edge case -- any z strictly inside the domain, not the
    two exact edges -- where the reflected samples must stay within the
    single boundary segment physically attached to that edge; past that,
    reflection pulls in mirrored geometry from an unrelated interior
    segment, a distortion distinct from the corner-rounding this function
    already performs intentionally at interior breakpoints.

    Raises ValueError if the window reaches past either boundary segment's
    own span (read from BREAKPOINTS, not hardcoded). Clamping the old way
    biased the average toward the interior slope (+0.30 mm at z=0, -0.32 mm
    at z=300 for the default window+samples). Naive even/mirror reflection
    of the sample coordinate (radius_at(|z|) / radius_at(600-z)) is worse,
    not better (+0.61 mm / -0.64 mm): a monotonic boundary segment is not
    symmetric about its own edge, so that doubles the slope's contribution
    instead of cancelling it.

    The inner wall is built from this, never from the relief-bearing outer
    surface: an inward offset of a detailed surface self-intersects wherever
    the wall thickness exceeds the local radius of curvature.
    """
    offsets = np.linspace(-window, window, samples)
    reach = float(np.abs(offsets).max()) if offsets.size else 0.0
    lo_span = float(_ZS[1] - _ZS[0])
    hi_span = float(_ZS[-1] - _ZS[-2])
    if reach > lo_span or reach > hi_span:
        raise ValueError(
            f"window={window} reaches {reach:g} mm from each sample point, exceeding "
            f"the first ({lo_span:g} mm) or last ({hi_span:g} mm) BREAKPOINTS segment "
            "span -- the boundary reflection is only meaningful within a single linear "
            "segment"
        )

    z = np.asarray(z, dtype=float)

    def sample(zz: np.ndarray) -> np.ndarray:
        below = zz < 0.0
        above = zz > 300.0
        out = radius_at(np.clip(zz, 0.0, 300.0))
        out[below] = 2 * _RS[0] - radius_at(-zz[below])
        out[above] = 2 * _RS[-1] - radius_at(600.0 - zz[above])
        return out

    stack = np.stack([sample(z + d) for d in offsets])
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


def max_envelope_slope(cfg: VaseConfig) -> float:
    """Worst-case |grad r| of the SMOOTH ENVELOPE -- profile + relief + twist.

    This bounds ``radius_at`` and ``relief_amplitude`` only. It has no
    access to the Julia field and must not gain one: the field's own
    z-gradient is what actually drives the steepest local slopes on the
    textured surface, and this function never sees it. The real
    printability gate is a separate check against the actual radius field
    (Task 4) -- do not treat this as that guarantee. Measured: the printed
    vase's textured surface reaches ~43.71 degrees against the 45-degree
    limit (margin 1.29 degrees), while this envelope bound -- corrected for
    the true profile+relief combined maximum radius (62.446 mm at z=151.3,
    not the profile-only 58 mm) -- comes out to ~0.8503 (40.38 degrees),
    understating the real surface by 3.33 degrees.

    Within its own scope it is still deliberately pessimistic: it stacks
    the steepest profile taper against the peak relief gradient and the
    twist drift at maximum combined radius, three things that do not
    co-occur on the real surface either.
    """
    z = np.linspace(0.0, 300.0, 30001)

    seg = np.abs(np.diff(_RS) / np.diff(_ZS)).max()
    relief_grad = np.abs(np.gradient(relief_amplitude(z, cfg), z)).max()
    meridional = seg + relief_grad

    r_max = (radius_at(z) + relief_amplitude(z, cfg)).max()
    tangential = r_max * abs(cfg.twist_rate_rad_per_mm)

    return float(np.hypot(meridional, tangential))
