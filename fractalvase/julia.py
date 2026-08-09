"""Julia escape-time field on a Koenigs-centred log-polar grid.

The mapping must be centred on the repelling fixed point alpha. An
origin-centred map (z = exp(k*h + i*theta)) puts every sample far outside
K_c, the field goes flat, and the vase comes out a smooth cone. See spec
section 2.3 and docs/superpowers/specs/proto_field.py.

The field is band-limited by two independent mechanisms (spec 4 step 2):
an s x s rotated-grid supersample and a Gaussian low-pass. A fractal has
unbounded detail; neither mechanism alone is enough to keep the sampled
field's gradient printable, but together they keep the surface's overhang
within reach of an unsupported nozzle.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter1d

from fractalvase.config import VaseConfig

_LOG2 = np.log(2.0)
_RGSS_ANGLE = np.arctan(0.5)  # classic rotated-grid-supersampling angle


def smooth_escape(z0: np.ndarray, cfg: VaseConfig) -> tuple[np.ndarray, np.ndarray]:
    """Renormalised escape time.

    Returns ``(nu, interior)``. ``nu`` is the continuous iteration count
    ``n + 1 - log(log|z_n|)/log 2``; the integer count terraces and would
    beat against layer lines. ``interior`` marks points that never escaped.
    """
    z = np.asarray(z0, dtype=np.complex128).copy()
    nu = np.full(z.shape, float(cfg.max_iter), dtype=np.float64)
    alive = np.ones(z.shape, dtype=bool)

    for n in range(cfg.max_iter):
        z[alive] = z[alive] ** 2 + cfg.c
        mag = np.abs(z)
        escaped = alive & (mag > cfg.escape_r)
        if escaped.any():
            nu[escaped] = n + 1 - np.log(np.log(mag[escaped])) / _LOG2
            alive &= ~escaped
        if not alive.any():
            break

    return nu, alive


def _base_grid(cfg: VaseConfig, n_theta: int, n_z: int) -> tuple[np.ndarray, np.ndarray]:
    """The (theta, h) sample grid before any supersample offset is applied.

    theta excludes its own upper bound: the axis is periodic (2*pi is the
    same angle as 0), so including both bounds would sample that angle
    twice, doubling the seam column. This is the ONLY place that builds the
    base theta axis -- koenigs_grid and _supersampled_field both go through
    it, so flipping that one flag cannot hide behind an unguarded second
    copy the way it could before this was extracted.
    """
    theta = np.linspace(0.0, 2 * np.pi, n_theta, endpoint=False)
    h = np.linspace(cfg.band_lo, cfg.band_hi, n_z)
    return np.meshgrid(theta, h, indexing="ij")


def _map_to_plane(cfg: VaseConfig, theta: np.ndarray, h: np.ndarray) -> np.ndarray:
    """(theta, h) -> the complex plane, Koenigs-centred on alpha.

    Rising one period advances u by exactly ln|mu| and v by exactly arg mu,
    which is the Koenigs map itself -- so the pattern reproduces, rotated.
    This is the ONLY place ``alpha + exp(...)`` may appear in this module;
    an origin-centred variant here (spec 2.3) puts every sample far outside
    K_c and the field goes flat.
    """
    dh = h - cfg.band_lo
    u = np.log(cfg.zeta_min) + cfg.k * dh
    v = theta + cfg.twist_rate_rad_per_mm * dh
    return cfg.alpha + np.exp(u + 1j * v)


def koenigs_grid(cfg: VaseConfig, n_theta: int, n_z: int) -> np.ndarray:
    """Map the vase's (theta, h) onto the complex plane around alpha.

    The offset-zero case of the sampling ``_supersampled_field`` performs:
    both go through ``_base_grid`` and ``_map_to_plane``.
    """
    t_grid, h_grid = _base_grid(cfg, n_theta, n_z)
    return _map_to_plane(cfg, t_grid, h_grid)


def _raw_field(cfg: VaseConfig, zc: np.ndarray) -> np.ndarray:
    """nu normalised by nu_ref and clamped to [0, 1]; interior is 1.0.

    The clip is two-sided: nu legitimately goes negative for deep-exterior
    points (points that escape on iteration 1 can have nu as low as
    ``1 - log(log(escape_r))/log(2)``, e.g. -2.788 at z=1000+0j against this
    config), and the lower clip saturates those to 0 -- the correct
    geometric outcome, not an edge case to special-case around.
    """
    nu, interior = smooth_escape(zc, cfg)
    field = np.clip(nu / cfg.nu_ref, 0.0, 1.0)
    field[interior] = 1.0
    return field


def _supersample_offsets(s: int) -> list[tuple[float, float]]:
    """s x s rotated-grid offsets, fractions of one cell in (theta, h).

    A regular s x s stratified grid is rotated by ``_RGSS_ANGLE`` so no two
    samples share a theta or a h coordinate -- unlike slicing a fixed-size
    list, this makes every ``s`` produce genuinely ``s**2`` distinct sample
    points instead of silently reusing the same handful for every s >= 2.
    """
    cos_a, sin_a = np.cos(_RGSS_ANGLE), np.sin(_RGSS_ANGLE)
    offsets = []
    for i in range(s):
        for j in range(s):
            gt = (i + 0.5) / s - 0.5
            gh = (j + 0.5) / s - 0.5
            offsets.append((float(gt * cos_a - gh * sin_a), float(gt * sin_a + gh * cos_a)))
    return offsets


def _supersampled_field(cfg: VaseConfig, n_theta: int, n_z: int, supersample: int) -> np.ndarray:
    """Field averaged over an s x s rotated-grid supersample, before the low-pass.

    A fractal has unbounded detail, so no sample rate is sufficient -- the
    field must be filtered, not merely sampled finely. Supersampling on a
    rotated offset grid averages the sub-sample detail away rather than
    aliasing it into the geometry.
    """
    if supersample <= 1:
        return _raw_field(cfg, koenigs_grid(cfg, n_theta, n_z))

    offsets = _supersample_offsets(supersample)
    dtheta = (2 * np.pi) / n_theta
    dh = (cfg.band_hi - cfg.band_lo) / max(n_z - 1, 1)
    t_grid, h_grid = _base_grid(cfg, n_theta, n_z)

    acc = np.zeros((n_theta, n_z), dtype=np.float64)
    for ot, oh in offsets:
        tt = t_grid + ot * dtheta
        hh = np.clip(h_grid + oh * dh, cfg.band_lo, cfg.band_hi)
        acc += _raw_field(cfg, _map_to_plane(cfg, tt, hh))

    return acc / len(offsets)


def _lowpass_sigma_cells(cfg: VaseConfig, n_theta: int, n_z: int) -> tuple[float, float]:
    """Gaussian low-pass sigma (spec 4 step 2), converted from mm to grid cells.

    theta cell width is fixed once, from circumference at the maximum
    radius (``lowpass_ref_radius_mm``); that one cell count is then applied
    uniformly at every radius the theta axis samples. The physical width
    actually achieved therefore scales with radius: exact
    (``lowpass_sigma_mm``) at the reference radius, and proportionally
    *smaller* everywhere else on the surface -- this is under-applied
    almost everywhere, not "never under-applied". Using the minimum radius
    instead would make that guarantee true but over-smooth by up to ~1.45x
    at the belly, where the design's main relief actually lives; using the
    maximum radius is the better trade because the shortfall is largest
    exactly where relief is zero (the foot and neck quiet zones) and
    smallest where relief peaks (~8.5% at ``relief_peak_z``, measured
    against spec 3.1's profile table -- see
    ``test_physical_lowpass_sigma_at_relief_peak_is_close_to_nominal``).
    """
    dtheta_mm = (2 * np.pi * cfg.lowpass_ref_radius_mm) / n_theta
    dh_mm = (cfg.band_hi - cfg.band_lo) / max(n_z - 1, 1)
    return cfg.lowpass_sigma_mm / dtheta_mm, cfg.lowpass_sigma_mm / dh_mm


def _lowpass_sigma_mm_at_radius(cfg: VaseConfig, r_mm: float) -> float:
    """Physical low-pass width (mm) actually achieved at a given radius.

    ``_lowpass_sigma_cells`` fixes a cell count from ``lowpass_sigma_mm``
    evaluated at ``lowpass_ref_radius_mm``; independent of grid resolution
    (the cell count and the arc length per cell both scale with n_theta and
    cancel), the achieved physical width at radius ``r_mm`` is
    ``lowpass_sigma_mm * r_mm / lowpass_ref_radius_mm``.
    """
    return cfg.lowpass_sigma_mm * r_mm / cfg.lowpass_ref_radius_mm


def normalised_field(
    cfg: VaseConfig, n_theta: int, n_z: int, supersample: int = 2
) -> np.ndarray:
    """Band-limited field in [0, 1].

    Two independent band-limiting mechanisms, per spec 4 step 2: an s x s
    rotated-grid supersample (``_supersampled_field``) followed by a
    Gaussian low-pass of ``cfg.lowpass_sigma_mm`` millimetres. The low-pass
    runs after the supersample so it smooths what supersampling could not
    -- detail finer than the sample grid itself. Wrapping in theta (the
    axis is periodic) and clamping in h (the band has real edges) keeps the
    filter from either seaming or bleeding past the vase's ends. Applied as
    two 1-D passes rather than a single call with a per-axis mode tuple,
    which keeps each call's ``mode`` a plain string.
    """
    field = _supersampled_field(cfg, n_theta, n_z, supersample)
    if cfg.lowpass_sigma_mm <= 0:
        return field

    sigma_theta, sigma_h = _lowpass_sigma_cells(cfg, n_theta, n_z)
    field = gaussian_filter1d(field, sigma=sigma_theta, axis=0, mode="wrap")
    field = gaussian_filter1d(field, sigma=sigma_h, axis=1, mode="nearest")
    return field
