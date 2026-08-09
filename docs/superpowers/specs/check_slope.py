"""Verify A(z) samples and the COMBINED overhang worst case (profile + relief + twist)."""
from itertools import pairwise

import numpy as np


def A(z):
    z = np.asarray(z, float)
    out = np.zeros_like(z)
    rise = (z >= 40) & (z <= 130)
    fall = (z > 130) & (z <= 240)
    out[rise] = 7.0 * (1 - np.cos(np.pi * (z[rise] - 40) / 90)) / 2
    out[fall] = 7.0 * (1 + np.cos(np.pi * (z[fall] - 130) / 110)) / 2
    return out

print("=== A(z) samples ===")
for z in (40, 110, 130, 150, 185, 225, 240):
    print(f"  A({z:3d}) = {A(np.array([z]))[0]:.4f} mm")

zz = np.linspace(40, 240, 20001)
dA = np.gradient(A(zz), zz)
print(f"  max |dA/dz| = {np.abs(dA).max():.4f} mm/mm")

# profile radius breakpoints (z, diameter)
BP = [(0, 70), (40, 80), (150, 112), (185, 116), (225, 96),
      (240, 78), (262, 58), (300, 68)]
print("\n=== profile segment slopes dr/dz ===")
worst_r = 0.0
for (z0, d0), (z1, d1) in pairwise(BP):
    s = (d1 / 2 - d0 / 2) / (z1 - z0)
    worst_r = max(worst_r, abs(s))
    print(f"  z {z0:3d}->{z1:3d}  d {d0:3d}->{d1:3d}  dr/dz = {s:+.4f}  "
          f"({np.degrees(np.arctan(abs(s))):5.2f} deg from vertical)")

TWIST = 0.4169  # tangential drift mm per mm Z at r=58 (from design_constants.py)
print("\n=== combined worst case ===")
comb = abs(worst_r) + np.abs(dA).max()          # meridional: profile + relief, same direction
total = np.hypot(comb, TWIST)                    # orthogonal tangential twist component
ang = np.degrees(np.arctan(total))
print(f"  worst meridional |dr/dz|      = {worst_r:.4f}")
print(f"  + max relief slope            = {np.abs(dA).max():.4f}")
print(f"  = meridional total            = {comb:.4f}")
print(f"  tangential (twist) at r=58    = {TWIST:.4f}")
print(f"  combined |grad r|             = {total:.4f}")
print(f"  angle from vertical           = {ang:.2f} deg   limit 45 -> "
      f"{'PASS' if ang < 45 else 'FAIL'}   margin {45-ang:.2f} deg")
