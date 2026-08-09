"""Predict Task 4's shell geometry independently, so the dispatch can pin real
numbers instead of letting the implementer's own output define correctness.

Also answers the question the plan's new test asks: does the REAL surface
(profile + relief + twist, low-passed) stay inside the 45 degree limit?
"""
import numpy as np

from fractalvase.config import DOUADY_HELIX, VaseConfig
from fractalvase.julia import normalised_field
from fractalvase.profile import radius_at, relief_amplitude, smooth_radius


def outer_radius(cfg):
    """Exactly what Task 4's _outer_radius must produce."""
    z = np.linspace(0.0, cfg.height, cfg.n_z)
    base = radius_at(z)[None, :]
    amp = relief_amplitude(z, cfg)[None, :]
    field = np.zeros((cfg.n_theta, cfg.n_z))
    in_band = (z >= cfg.band_lo) & (z <= cfg.band_hi)
    field[:, in_band] = normalised_field(cfg, cfg.n_theta, int(in_band.sum()))
    return base + amp * np.tanh(1.6 * field), z


for name, cfg in (("SMALL (test cfg)", VaseConfig(n_theta=96, n_z=80)),
                  ("PRODUCTION", DOUADY_HELIX)):
    r, z = outer_radius(cfg)
    nt, nz = cfg.n_theta, cfg.n_z

    # triangle budget
    outer_tris = 2 * nt * (nz - 1)
    in_t, in_z = max(nt // 3, 48), max(nz // 3, 24)
    inner_tris = 2 * in_t * (in_z - 1)
    rim_tris = 2 * nt
    base_tris = 2 * nt + nt          # annulus + fan
    total = outer_tris + inner_tris + rim_tris + base_tris

    # envelope
    dia = 2 * r.max()

    # overhang on the REAL surface
    drdz = np.gradient(r, z[1] - z[0], axis=1)
    ang = np.degrees(np.arctan(np.abs(drdz)))

    # wall sanity: does the inner surface stay inside the outer everywhere?
    r_in = np.clip(smooth_radius(z) - cfg.wall, 0.5, None)
    clearance = r.min(axis=0) - r_in

    print(f"--- {name}: n_theta={nt}, n_z={nz} ---")
    print(f"  triangles: outer {outer_tris:,} + inner {inner_tris:,} "
          f"+ rim {rim_tris:,} + base {base_tris:,} = {total:,}")
    print(f"  binary STL would be {84 + 50*total:,} bytes")
    print(f"  max diameter {dia:.3f} mm   (plate 135, limit 135)")
    print(f"  height {z.max():.1f} mm")
    print(f"  max overhang {ang.max():.2f} deg   over45 {100*(ang>45).mean():.4f}%")
    print(f"  min wall clearance (outer_min - inner) {clearance.min():+.3f} mm")
    if clearance.min() <= 0:
        bad = z[clearance <= 0]
        print(f"    !! inner surface meets/exceeds outer at z in "
              f"[{bad.min():.1f}, {bad.max():.1f}] mm")
    print()
