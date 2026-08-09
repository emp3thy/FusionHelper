"""Douady Helix — verified design constants."""
import numpy as np

c = -0.123 + 0.745j
alpha = (1 + np.sqrt(complex(1 - 4 * c))) / 2
mu = 2 * alpha
absmu, argmu = abs(mu), np.angle(mu)
lnmu = np.log(absmu)
e = np.e

print("=== Koenigs data, c = -0.123 + 0.745i (Douady rabbit) ===")
print(f"  alpha      = {alpha.real:.10f} {alpha.imag:+.10f}i")
print(f"  mu = 2a    = {mu.real:.10f} {mu.imag:+.10f}i")
print(f"  |mu|       = {absmu:.10f}")
print(f"  e          = {e:.10f}")
print(f"  |mu|/e     = {absmu/e:.6f}   -> {100*(absmu/e-1):+.3f}% from e")
print(f"  arg mu     = {argmu:.10f} rad = {np.degrees(argmu):.4f} deg")
print(f"  ln|mu|     = {lnmu:.10f}")

BAND_LO, BAND_HI = 40.0, 240.0
BAND = BAND_HI - BAND_LO
print(f"\n=== log-polar mapping, fractal band z = {BAND_LO}..{BAND_HI} mm ({BAND:.0f} mm) ===")
for P in (3, 4, 5):
    dh = BAND / P
    k = lnmu / dh
    print(f"  P={P} periods: dh={dh:7.3f} mm  k={k:.7f} /mm  "
          f"twist/period={np.degrees(argmu):+7.2f} deg  "
          f"total twist={P * np.degrees(argmu):+8.2f} deg")

P = 4
dh = BAND / P
k = lnmu / dh
print(f"\n  CHOSEN P={P}: dh={dh:.4f} mm, k={k:.7f} /mm, "
      f"total twist={P * np.degrees(argmu):+.2f} deg")

print(f"\n=== scale ladder, ratio |mu| = {absmu:.4f} ===")
D_MAX, MIN_RIDGE = 116.0, 1.0
s, lvl = D_MAX, 0
while s >= MIN_RIDGE:
    flag = ""
    if s < 2.2:
        flag = "  <- below 2.2mm target floor"
    if s < MIN_RIDGE * 2:
        flag += "  <- approaching 1.0mm min ridge"
    print(f"  level {lvl}: {s:8.3f} mm{flag}")
    s /= absmu
    lvl += 1
n_levels = int(np.floor(np.log(D_MAX / MIN_RIDGE) / lnmu)) + 1
print(f"  usable levels above {MIN_RIDGE} mm ridge: {n_levels}")

print("\n=== twist gradient / printability ===")
R_MAX = 116.0 / 2
tw_rate = abs(argmu) / dh
print(f"  twist rate            = {np.degrees(tw_rate):.4f} deg/mm")
print(f"  tangential drift at r={R_MAX:.0f}mm = {R_MAX*tw_rate:.4f} mm per mm of Z")
print(f"  lean angle from vertical      = {np.degrees(np.arctan(R_MAX*tw_rate)):.3f} deg"
      f"   (limit 45)  -> {'OK' if np.degrees(np.arctan(R_MAX*tw_rate)) < 45 else 'FAIL'}")

print("\n=== mesh / z-sampling ===")
NZ, NTH = 500, 640
print(f"  Nz={NZ} over 300mm  -> {300/NZ:.4f} mm per step "
      f"({BAND/(300/NZ)/P:.1f} steps per fractal period, need >=50)")
print(f"  Ntheta={NTH}        -> arc {2*np.pi*R_MAX/NTH:.4f} mm at r={R_MAX:.0f}mm")
print(f"  chord sagitta       = {R_MAX*(1-np.cos(np.pi/NTH)):.6f} mm")
print(f"  triangles outer     = {2*NTH*(NZ-1):,}")
