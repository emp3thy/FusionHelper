"""Seeded pierced lattice: the field chooses size, a lattice fixes topology.

Rows are spaced in z; each row is offset half a step in theta from its
neighbour (hexagonal packing, the densest arrangement for a given minimum
separation). Every site samples the field; sites below a cut stay closed,
the rest open to an arch whose size scales with the field.

Everything here is measured in millimetres ON THE SURFACE, so arc spacing
is computed from the local radius rather than a fixed angular step.
"""
import numpy as np

from fractalvase.config import DOUADY_HELIX as C
from fractalvase.julia import normalised_field
from fractalvase.profile import radius_at, relief_amplitude

BAND_LO, BAND_HI = 150.0, 225.0

_FULL = normalised_field(C, C.n_theta, C.n_z)
_ZF = np.linspace(C.band_lo, C.band_hi, C.n_z)


def field_at(theta, z):
    """Sample the normalised field at arbitrary (theta, z), nearest-neighbour."""
    ti = np.round(theta / (2 * np.pi) * C.n_theta).astype(int) % C.n_theta
    zi = np.clip(np.searchsorted(_ZF, z), 0, C.n_z - 1)
    return _FULL[ti, zi]


def lattice(row_pitch, col_pitch, open_cut, size_lo, size_hi):
    """Return (theta, z, size_mm) for every OPEN site."""
    rows = np.arange(BAND_LO + row_pitch / 2, BAND_HI, row_pitch)
    th, zz, sz = [], [], []
    for i, z in enumerate(rows):
        r = float(radius_at(np.array([z]))[0]) + float(
            relief_amplitude(np.array([z]), C)[0])
        n = max(int(round(2 * np.pi * r / col_pitch)), 3)
        offset = (i % 2) * (np.pi / n)          # hex stagger
        t = np.linspace(0, 2 * np.pi, n, endpoint=False) + offset
        f = field_at(t, np.full(n, z))
        keep = f >= open_cut
        if not keep.any():
            continue
        # size scales with how far above the cut the field sits
        frac = (f[keep] - open_cut) / max(1e-9, 1.0 - open_cut)
        th.append(t[keep])
        zz.append(np.full(keep.sum(), z))
        sz.append(size_lo + frac * (size_hi - size_lo))
    if not th:
        return np.array([]), np.array([]), np.array([])
    return np.concatenate(th), np.concatenate(zz), np.concatenate(sz)


print(f"band z {BAND_LO}..{BAND_HI} mm ({BAND_HI - BAND_LO:.0f} mm tall)")
print(f"min_ligament {C.min_ligament} mm, max_hole_span {C.max_hole_span} mm\n")
print(f"{'row':>5} {'col':>5} {'cut':>5} {'holes':>7} {'rows':>5} "
      f"{'size min/max':>14} {'min gap':>9}")

for row_pitch, col_pitch in ((10.0, 12.0), (12.0, 14.0), (14.0, 16.0)):
    for cut in (0.35, 0.50, 0.62):
        t, z, s = lattice(row_pitch, col_pitch, cut, 3.0, 8.0)
        if len(t) == 0:
            print(f"{row_pitch:5.1f} {col_pitch:5.1f} {cut:5.2f} {0:7d}  none open")
            continue
        # worst-case ligament: closest pair of open sites minus their half-sizes
        r = radius_at(z) + relief_amplitude(z, C)
        x, y = r * np.cos(t), r * np.sin(t)
        pts = np.stack([x, y, z], axis=1)
        d = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
        np.fill_diagonal(d, np.inf)
        half = s / 2
        gap = (d - half[:, None] - half[None, :]).min()
        print(f"{row_pitch:5.1f} {col_pitch:5.1f} {cut:5.2f} {len(t):7d} "
              f"{len(np.unique(z)):5d} {s.min():6.2f}/{s.max():6.2f} {gap:8.2f}mm")

print("\nmin gap must stay >= min_ligament (2.0 mm) or the lattice snaps.")
