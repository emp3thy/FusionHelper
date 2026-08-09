"""How much does the missing low-pass / gradient clamp actually matter?

Builds the real outer radius r(theta,z) = r0(z) + A(z)*tanh(1.6*f) and measures
the TRUE overhang: |dr/dz| at fixed theta, which is what the nozzle experiences.
"""
import numpy as np
from scipy import ndimage

from fractalvase.config import DOUADY_HELIX as C
from fractalvase.julia import normalised_field

# profile.py is Task 3, not built yet -- inline from the plan
BP = [(0, 70), (40, 80), (150, 112), (185, 116), (225, 96), (240, 78), (262, 58), (300, 68)]
_ZS = np.array([b[0] for b in BP], float)
_RS = np.array([b[1] / 2 for b in BP], float)


def radius_at(z):
    return np.interp(np.asarray(z, float), _ZS, _RS)


def relief_amplitude(z, cfg):
    z = np.asarray(z, float)
    out = np.zeros_like(z)
    lo, pk, hi = cfg.band_lo, cfg.relief_peak_z, cfg.band_hi
    rise = (z >= lo) & (z <= pk)
    fall = (z > pk) & (z <= hi)
    out[rise] = cfg.relief_peak * (1 - np.cos(np.pi * (z[rise] - lo) / (pk - lo))) / 2
    out[fall] = cfg.relief_peak * (1 + np.cos(np.pi * (z[fall] - pk) / (hi - pk))) / 2
    return out

NT, NZ = C.n_theta, C.n_z


def outer_radius(field):
    z = np.linspace(C.band_lo, C.band_hi, field.shape[1])
    r0 = radius_at(z)[None, :]
    amp = relief_amplitude(z, C)[None, :]
    return r0 + amp * np.tanh(1.6 * field), z


def report(name, field):
    r, z = outer_radius(field)
    dz = z[1] - z[0]
    drdz = np.gradient(r, dz, axis=1)          # at fixed theta: what printing sees
    ang = np.degrees(np.arctan(np.abs(drdz)))
    frac_over = (ang > 45).mean()
    print(f"{name:28s} max |dr/dz| {np.abs(drdz).max():7.3f}  "
          f"max angle {ang.max():6.2f}deg  "
          f"over45 {100*frac_over:6.3f}%  "
          f"p99.9 {np.percentile(ang, 99.9):6.2f}deg")
    return ang


print(f"grid {NT} x {NZ}, dz = {(C.band_hi-C.band_lo)/(NZ-1):.3f} mm, "
      f"arc at r=58: {2*np.pi*58/NT:.3f} mm")
print()

f1 = normalised_field(C, NT, NZ, supersample=1)
f2 = normalised_field(C, NT, NZ, supersample=2)

report("supersample=1 (raw)", f1)
report("supersample=2 (as shipped)", f2)

# what the spec asked for but the plan dropped: Gaussian low-pass sigma=0.5mm
dz_mm = (C.band_hi - C.band_lo) / (NZ - 1)
dtheta_mm = 2 * np.pi * 58.0 / NT
sigma_cells = (0.5 / dtheta_mm, 0.5 / dz_mm)
print(f"\nGaussian sigma 0.5mm = {sigma_cells[0]:.2f} cells theta, "
      f"{sigma_cells[1]:.2f} cells z")
f_lp = ndimage.gaussian_filter(f2, sigma=sigma_cells, mode=("wrap", "nearest"))
report("+ gaussian lowpass 0.5mm", f_lp)

for s in (0.75, 1.0, 1.5):
    sc = (s / dtheta_mm, s / dz_mm)
    report(f"+ gaussian lowpass {s}mm",
           ndimage.gaussian_filter(f2, sigma=sc, mode=("wrap", "nearest")))

# how much relief survives the filter? band-limiting that flattens the art is no good
for nm, f in (("shipped", f2), ("lp 0.5mm", f_lp)):
    r, _ = outer_radius(f)
    r0 = radius_at(np.linspace(C.band_lo, C.band_hi, NZ))[None, :]
    print(f"{nm:10s} relief peak-to-peak {np.ptp(r - r0):.3f} mm, "
          f"std {(r - r0).std():.3f} mm")
