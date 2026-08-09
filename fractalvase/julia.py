"""Julia escape-time field on a Koenigs-centred log-polar grid.

The mapping must be centred on the repelling fixed point alpha. An
origin-centred map (z = exp(k*h + i*theta)) puts every sample far outside
K_c, the field goes flat, and the vase comes out a smooth cone. See spec
section 2.3 and docs/superpowers/specs/proto_field.py.
"""

from __future__ import annotations

import numpy as np

from fractalvase.config import VaseConfig

_LOG2 = np.log(2.0)


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


def koenigs_grid(cfg: VaseConfig, n_theta: int, n_z: int) -> np.ndarray:
    """Map the vase's (theta, h) onto the complex plane around alpha.

    Rising one period advances u by exactly ln|mu| and v by exactly arg mu,
    which is the Koenigs map itself -- so the pattern reproduces, rotated.
    """
    theta = np.linspace(0.0, 2 * np.pi, n_theta, endpoint=False)
    h = np.linspace(cfg.band_lo, cfg.band_hi, n_z)
    t_grid, h_grid = np.meshgrid(theta, h, indexing="ij")

    dh = h_grid - cfg.band_lo
    u = np.log(cfg.zeta_min) + cfg.k * dh
    v = t_grid + cfg.twist_rate_rad_per_mm * dh
    return cfg.alpha + np.exp(u + 1j * v)


def _raw_field(cfg: VaseConfig, zc: np.ndarray) -> np.ndarray:
    """nu clamped at nu_ref and normalised to [0, 1]; interior is 1.0."""
    nu, interior = smooth_escape(zc, cfg)
    field = np.clip(nu / cfg.nu_ref, 0.0, 1.0)
    field[interior] = 1.0
    return field


def normalised_field(
    cfg: VaseConfig, n_theta: int, n_z: int, supersample: int = 2
) -> np.ndarray:
    """Band-limited field in [0, 1].

    A fractal has unbounded detail, so no sample rate is sufficient -- the
    field must be filtered, not merely sampled finely. Supersampling on a
    rotated offset grid averages the sub-sample detail away rather than
    aliasing it into the geometry.
    """
    if supersample <= 1:
        return _raw_field(cfg, koenigs_grid(cfg, n_theta, n_z))

    acc = np.zeros((n_theta, n_z), dtype=np.float64)
    # rotated-grid offsets: fractions of one cell in (theta, h)
    offsets = [(0.25, 0.25), (0.75, -0.25), (-0.25, 0.75), (-0.75, -0.75)][: supersample**2]
    dtheta = (2 * np.pi) / n_theta
    dh = (cfg.band_hi - cfg.band_lo) / max(n_z - 1, 1)

    theta = np.linspace(0.0, 2 * np.pi, n_theta, endpoint=False)
    h = np.linspace(cfg.band_lo, cfg.band_hi, n_z)
    t_grid, h_grid = np.meshgrid(theta, h, indexing="ij")

    for ot, oh in offsets:
        tt = t_grid + ot * dtheta
        hh = np.clip(h_grid + oh * dh, cfg.band_lo, cfg.band_hi)
        d = hh - cfg.band_lo
        u = np.log(cfg.zeta_min) + cfg.k * d
        v = tt + cfg.twist_rate_rad_per_mm * d
        acc += _raw_field(cfg, cfg.alpha + np.exp(u + 1j * v))

    return acc / len(offsets)
