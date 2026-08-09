"""Locate the thin-wall spot and test the candidate fix."""
import numpy as np

from fractalvase.config import DOUADY_HELIX as C
from fractalvase.profile import radius_at, smooth_radius

z = np.linspace(0.0, C.height, 3001)
r_out_min = radius_at(z)          # outer at its thinnest over theta (field = 0)
r_sm = smooth_radius(z)

print("smooth_radius - radius_at, where positive it EATS the wall:")
delta = r_sm - r_out_min
worst = int(np.argmax(delta))
print(f"  max bulge {delta.max():.4f} mm at z = {z[worst]:.1f} mm")
print(f"  wall {C.wall} mm -> actual {C.wall - delta.max():.4f} mm there")
print()
print("  z      radius_at  smooth   bulge   wall_actual")
for zz in (0, 40, 150, 185, 225, 240, 255, 262, 270, 300):
    i = int(np.argmin(np.abs(z - zz)))
    print(f"  {zz:4.0f}   {r_out_min[i]:7.3f}  {r_sm[i]:7.3f}  "
          f"{delta[i]:+6.3f}  {C.wall - delta[i]:8.4f}")

print("\n--- candidate fix: inner = min(smooth_radius, radius_at) - wall ---")
r_in_fixed = np.minimum(r_sm, r_out_min) - C.wall
clearance = r_out_min - r_in_fixed
print(f"  min clearance now {clearance.min():.4f} mm (was {(r_out_min-(r_sm-C.wall)).min():.4f})")
print(f"  inner radius range {r_in_fixed.min():.3f} .. {r_in_fixed.max():.3f} mm")
print(f"  inner stays positive: {bool((r_in_fixed > 0.5).all())}")

# curvature check: does min() introduce a kink sharp enough to matter?
d1 = np.gradient(r_in_fixed, z[1] - z[0])
print(f"  inner |dr/dz| max {np.abs(d1).max():.4f} "
      f"({np.degrees(np.arctan(np.abs(d1).max())):.2f} deg) -- inner face, "
      f"not printed as an overhang but should stay sane")

# does the fix change the usable interior volume much?
vol_old = np.trapezoid(np.pi * np.clip(r_sm - C.wall, 0.5, None) ** 2, z) / 1000
vol_new = np.trapezoid(np.pi * np.clip(r_in_fixed, 0.5, None) ** 2, z) / 1000
print(f"  interior volume {vol_old:.1f} -> {vol_new:.1f} cm^3 "
      f"({100*(vol_new/vol_old-1):+.2f}%)")
