import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from rasterlib import *

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spinners')


def analyze(name, rel, zfracs=(0.25, 0.5, 0.75), pitch=0.03, teeth_region_count=0,
            clearance_pairs=3, do_rim=True):
    path = os.path.join(BASE, rel)
    m = load(path)
    cxy = center_xy(m)
    lo, hi = m.bounds
    H = hi[2] - lo[2]
    print(f"\n#### {name}")
    print(f"bbox {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {H:.1f} mm, mesh volume {abs(m.volume):.0f} mm3 (~{abs(m.volume)*DENS:.1f} g PLA)")
    if do_rim:
        rf, rmax = rim_fraction_raster(m, cxy, 0.8, 13, 0.08)
        print(f"Rmax {rmax:.2f} mm | volume beyond 0.8*Rmax: {rf*100:.1f}%")
    for zf in zfracs:
        z = lo[2] + zf * H
        rings = slice_rings(m, z)
        g, o, p = rasterize(rings, pitch)
        if g is None:
            print(f" z={z:.2f}: no section")
            continue
        r, occ = radial_occupancy_grid(g, o, p, cxy)
        bds = bands(r, occ)
        gps = gaps(bds)
        area = g.sum() * p * p
        lab, keep = regions(g, 1.0, p)
        print(f" z={z:.2f} (frac {zf}): area {area:.0f} mm2, {len(keep)} regions>1mm2")
        print("   radial bands: " + fmt_bands(bds, gps))
        # clearances between largest regions
        if len(keep) >= 2 and clearance_pairs:
            npair = 0
            for i in range(min(len(keep), 4)):
                for j in range(i + 1, min(len(keep), 4)):
                    if npair >= clearance_pairs: break
                    c = region_clearance(lab, keep[i][0], keep[j][0], p)
                    if c < 3.0:
                        print(f"   2D clearance region{i}({keep[i][1]:.0f}mm2) vs region{j}({keep[j][1]:.0f}mm2): {c:.3f} mm")
                        npair += 1
        # teeth on largest regions if requested
        for k in range(teeth_region_count):
            if k >= len(keep): break
            r_out, r_in = r_theta_of_region(lab, keep[k][0], o, p, cxy)
            n_out, lo_o, hi_o = count_teeth(r_out)
            n_in, lo_i, hi_i = count_teeth(-r_in)  # teeth pointing inward
            print(f"   region{k}: outer r {np.nanmin(r_out):.2f}..{np.nanmax(r_out):.2f} teeth~{n_out}; "
                  f"inner r {np.nanmin(r_in):.2f}..{np.nanmax(r_in):.2f} teeth~{n_in}")
    # z thickness profile: area at many z
    zs = z_slices(m, 15)
    prof = []
    for z in zs:
        rings = slice_rings(m, z)
        g2, o2, p2 = rasterize(rings, 0.1)
        prof.append((z, 0 if g2 is None else g2.sum() * p2 * p2))
    print("   z-area profile: " + " ".join(f"{z:.1f}:{a:.0f}" for z, a in prof))
    return m, cxy


if __name__ == '__main__':
    import json
    which = sys.argv[1] if len(sys.argv) > 1 else 'gman'
    if which == 'gman':
        analyze('GMan-Geometric-Core',
                r"G-Man+Projects+-+Geometric+Spinner+-+Core+-+Monocolour_stls\obj_1_non circular circle 2.5 0.15 0.16 tighter.STEP.stl")
        analyze('GMan-Geometric-Razor',
                r"G-Man+Projects+-+Geometric+Spinner+-+Razor+-+Multicolour+2_stls\obj_1_non circular 6 2.5 0.15 0.16 0.02 0.10.STEP.stl")
    elif which == 'gman2':
        analyze('GMan-Square-Fragment',
                r"G-Man+Projects+-+Square+Spinner+-+Fragment+-+Multicolour+1_stls\obj_1_mainframe 0.12 2.6 0.13.STEP.stl")
        analyze('GMan-HeavyDuty-Blade',
                r"G-Man+Projects+Heavy+Duty+Planetary+Gears+-+Blade_stls\obj_1_test-split-ams-fat-boy.STEP.stl",
                teeth_region_count=2)
    elif which == 'planetary':
        analyze('GMan-PlanetaryGears-cog10',
                r"G-Man+Projects+Planetary+Gears+Fidget+Spinner_stls\obj_6_planetary-gears-cog-10-large.STEP.stl",
                teeth_region_count=3)
        analyze('PiP-Planetary-Gear-Spinner',
                r"Print+in+Place+Planetary+Gear+Spinner\Planetary Gear Spinner.stl",
                teeth_region_count=3)
    elif which == 'gyro':
        analyze('Gyro-7rings', r"Gyro+Fidget+Rings\STL Files\gyro_spinner_7_rings.stl", pitch=0.025)
        analyze('WaveGyro', r"_Wave_+Gyro+Fidget+Spinner+Heavy+Duty\Wave Gyro Fidget Spinner.stl", pitch=0.025)
    elif which == 'arcspin':
        analyze('Arcspin', r"FloW_Arcspin_plain_M_Silk_20262101_stls\obj_1_Zusammenbau.stl", pitch=0.025,
                zfracs=(0.15, 0.3, 0.5, 0.7, 0.85))
