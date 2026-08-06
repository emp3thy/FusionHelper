import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from meshlib import *

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spinners')

FILES = {
 'GMan-Geometric-Core': r"G-Man+Projects+-+Geometric+Spinner+-+Core+-+Monocolour_stls\obj_1_non circular circle 2.5 0.15 0.16 tighter.STEP.stl",
 'GMan-Geometric-Razor': r"G-Man+Projects+-+Geometric+Spinner+-+Razor+-+Multicolour+2_stls\obj_1_non circular 6 2.5 0.15 0.16 0.02 0.10.STEP.stl",
 'GMan-Square-Fragment': r"G-Man+Projects+-+Square+Spinner+-+Fragment+-+Multicolour+1_stls\obj_1_mainframe 0.12 2.6 0.13.STEP.stl",
 'GMan-HeavyDuty-Blade': r"G-Man+Projects+Heavy+Duty+Planetary+Gears+-+Blade_stls\obj_1_test-split-ams-fat-boy.STEP.stl",
}

for name, rel in FILES.items():
    path = os.path.join(BASE, rel)
    m = load(path)
    cxy = center_xy(m)
    lo, hi = m.bounds
    print(f"\n#### {name}  bounds z {lo[2]:.2f}..{hi[2]:.2f}  overall mass {abs(m.volume)*DENS:.1f} g")
    parts = bodies_of(m)
    print(f"bodies: {len(parts)}")
    rows = summarize_bodies(parts, cxy)
    print(fmt_bodies(rows[:12]))
    # rim fraction
    rf, rmax = rim_fraction(m, cxy, 0.8, 21)
    print(f"Rmax {rmax:.2f} mm; volume fraction beyond 0.8R: {rf:.3f}")
    # occupancy at 3 z levels
    for zf in (0.25, 0.5, 0.75):
        z = lo[2] + zf * (hi[2] - lo[2])
        u = slice_polys(m, z, cxy)
        if u is None: continue
        r, occ = radial_occupancy(u, rmax * 1.02)
        bands = bands_from_occ(r, occ)
        gaps = gaps_from_bands(bands)
        bs = " | ".join(f"{b['r0']:.2f}-{b['r1']:.2f}(occ{b['occ_mean']:.2f})" for b in bands)
        gs = " | ".join(f"{g['g0']:.2f}+{g['w']:.2f}" for g in gaps)
        print(f"z={z:.2f}: bands {bs}")
        if gaps: print(f"        air-gaps(r+w): {gs}")
    # min gaps between the largest bodies
    n = min(len(parts), 6)
    for i in range(n):
        for j in range(i+1, n):
            # only if radially adjacent
            ri = body_radial_range(parts[i], cxy); rj = body_radial_range(parts[j], cxy)
            g = min_gap_fast(parts[i], parts[j], 3000)
            print(f"min gap body{i}(r{ri[0]:.1f}-{ri[1]:.1f}) vs body{j}(r{rj[0]:.1f}-{rj[1]:.1f}): {g:.3f} mm")
