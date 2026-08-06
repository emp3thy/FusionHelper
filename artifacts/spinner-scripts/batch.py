import sys, os, warnings, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings('ignore')
import numpy as np
from rasterlib import *
from measure import BASE, region_report  # noqa
from scipy.spatial import cKDTree
from trimesh.triangles import closest_point


def teeth_own(lab, li, o, p, cent_abs, n_t=720):
    """Teeth count of region about its own centroid."""
    ys, xs = np.nonzero(lab == li)
    x = o[0] + xs * p - cent_abs[0]
    y = o[1] + ys * p - cent_abs[1]
    r = np.hypot(x, y)
    t = (np.arctan2(y, x) % (2 * np.pi) / (2 * np.pi) * n_t).astype(int) % n_t
    r_out = np.full(n_t, -np.inf)
    np.maximum.at(r_out, t, r)
    r_out[np.isinf(r_out)] = np.nan
    return count_teeth(r_out)


def slice_report(m, cxy, z, pitch=0.03, topn=8, own_teeth_regions=(), png=None, gap_pairs=True):
    rings = slice_rings(m, z)
    g, o, p = rasterize(rings, pitch)
    if g is None:
        print(f"  z={z:.2f}: empty"); return
    lab, keep = regions(g, 0.5, p)
    r_all, occ = radial_occupancy_grid(g, o, p, cxy)
    bds = bands(r_all, occ)
    gps = gaps(bds)
    print(f"  z={z:.2f}: area {g.sum()*p*p:.0f} mm2, {len(keep)} regions")
    print("   bands: " + fmt_bands(bds, gps))
    cents = {}
    for k, (li, ar) in enumerate(keep[:topn]):
        ys, xs = np.nonzero(lab == li)
        x = o[0] + xs * p - cxy[0]; y = o[1] + ys * p - cxy[1]
        r = np.hypot(x, y)
        cx, cy = x.mean(), y.mean()
        cents[k] = (cx + cxy[0], cy + cxy[1])
        rl = np.hypot(x - cx, y - cy)
        line = (f"   R{k}: area {ar:7.1f} r {r.min():6.2f}..{r.max():6.2f} c@r={np.hypot(cx,cy):5.2f} "
                f"locDia {2*rl.max():5.2f}")
        if ar > 15:
            r_out, r_in = r_theta_of_region(lab, li, o, p, cxy)
            n_o, lo_o, hi_o = count_teeth(r_out)
            n_i, lo_i, hi_i = count_teeth(-r_in)
            line += f" | axis teethOut~{n_o}({lo_o:.2f}-{hi_o:.2f}) teethIn~{n_i}({-hi_i:.2f}-{-lo_i:.2f})"
        if k in own_teeth_regions:
            n, rlo, rhi = teeth_own(lab, li, o, p, cents[k])
            line += f" | ownTeeth~{n}(r{rlo:.2f}-{rhi:.2f})"
        print(line)
    if gap_pairs and len(keep) >= 2:
        for i in range(min(len(keep), 5)):
            for j in range(i + 1, min(len(keep), 5)):
                c = region_clearance(lab, keep[i][0], keep[j][0], p)
                if c < 2.0:
                    print(f"   2Dgap R{i}-R{j}: {c:.3f}")
    if png:
        import matplotlib; matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.figure(figsize=(8, 8))
        show = np.zeros_like(lab, dtype=float)
        for k, (li, ar) in enumerate(keep[:19]):
            show[lab == li] = (k % 19) + 1
        plt.imshow(show, origin='lower', cmap='tab20', interpolation='nearest')
        plt.title(f"z={z:.2f}"); plt.savefig(png, dpi=50, bbox_inches='tight'); plt.close()


def body_gaps(m, cxy, topk=10, gap_max=1.5, vol_min=20):
    parts = [p for p in m.split(only_watertight=False) if abs(p.volume) > vol_min]
    parts.sort(key=lambda q: -abs(q.volume))
    parts = parts[:topk]
    info = []
    for i, b in enumerate(parts):
        lo, hi = b.bounds
        v = b.vertices
        r = np.hypot(v[:, 0] - cxy[0], v[:, 1] - cxy[1])
        info.append((lo[2], hi[2], r.min(), r.max()))
        print(f"  b{i}: vol {abs(b.volume):8.0f} z {lo[2]:6.2f}..{hi[2]:6.2f} r {r.min():6.2f}..{r.max():6.2f} wt={str(b.is_watertight)[0]}")
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            zi, zj = info[i], info[j]
            if min(zi[1], zj[1]) - max(zi[0], zj[0]) < 0.3: continue
            if min(zi[3], zj[3]) - max(zi[2], zj[2]) < -3.0: continue
            try:
                gg = gap3d(parts[i], parts[j])
            except Exception as e:
                print(f"  gap b{i}-b{j} FAIL {e}"); continue
            if gg < gap_max:
                print(f"  gap3D b{i}-b{j}: {gg:.3f}")
    return parts


def header(name, m):
    lo, hi = m.bounds
    print(f"\n===== {name}: {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, "
          f"{abs(m.volume):.0f} mm3 ({abs(m.volume)*DENS:.1f} g PLA)")
    return lo, hi


def rimfrac(m, cxy, n=11, pitch=0.1):
    lo, hi = m.bounds
    zs = np.linspace(lo[2] + 0.1, hi[2] - 0.1, n)
    packs = []; rmax = 0
    for z in zs:
        rings = slice_rings(m, z)
        g, o, p = rasterize(rings, pitch)
        if g is None: continue
        xs, ys = grid_coords(g, o, p)
        gx, gy = np.meshgrid(xs - cxy[0], ys - cxy[1])
        rr = np.hypot(gx, gy)[g]
        if len(rr): packs.append(rr); rmax = max(rmax, rr.max())
    tot = sum(len(x) for x in packs)
    rim = sum((x > 0.8 * rmax).sum() for x in packs)
    print(f"  Rmax {rmax:.2f}; vol fraction beyond 0.8R: {100*rim/tot:.1f}%")


def zprof(m, cxy, n=16, pitch=0.12):
    lo, hi = m.bounds
    zs = np.linspace(lo[2] + 0.08, hi[2] - 0.08, n)
    out = []
    for z in zs:
        rings = slice_rings(m, z)
        g, o, p = rasterize(rings, pitch)
        out.append((z, 0 if g is None else g.sum() * p * p))
    print("  z:area " + " ".join(f"{z:.1f}:{a:.0f}" for z, a in out))


def run(which):
    t0 = time.time()
    if which == 'razor':
        m = load(os.path.join(BASE, r"G-Man+Projects+-+Geometric+Spinner+-+Razor+-+Multicolour+2_stls\obj_1_non circular 6 2.5 0.15 0.16 0.02 0.10.STEP.stl"))
        cxy = center_xy(m); lo, hi = header('GMan-Razor', m)
        rimfrac(m, cxy); zprof(m, cxy)
        slice_report(m, cxy, lo[2] + 1.0, own_teeth_regions=(3, 4, 5))
        body_gaps(m, cxy, topk=10)
    elif which == 'fragment':
        m = load(os.path.join(BASE, r"G-Man+Projects+-+Square+Spinner+-+Fragment+-+Multicolour+1_stls\obj_1_mainframe 0.12 2.6 0.13.STEP.stl"))
        cxy = center_xy(m); lo, hi = header('GMan-SquareFragment', m)
        rimfrac(m, cxy); zprof(m, cxy)
        slice_report(m, cxy, lo[2] + 1.0, own_teeth_regions=(2, 3, 4), png='fragment_z1.png')
        body_gaps(m, cxy, topk=10)
    elif which == 'blade':
        m = load(os.path.join(BASE, r"G-Man+Projects+Heavy+Duty+Planetary+Gears+-+Blade_stls\obj_1_test-split-ams-fat-boy.STEP.stl"))
        cxy = center_xy(m); lo, hi = header('GMan-HeavyDuty-Blade', m)
        rimfrac(m, cxy); zprof(m, cxy)
        slice_report(m, cxy, lo[2] + 1.0, own_teeth_regions=(2, 3, 4), png='blade_z1.png')
        slice_report(m, cxy, lo[2] + 7.1, png='blade_z7.png')
        body_gaps(m, cxy, topk=10)
    elif which == 'cog10':
        m = load(os.path.join(BASE, r"G-Man+Projects+Planetary+Gears+Fidget+Spinner_stls\obj_6_planetary-gears-cog-10-large.STEP.stl"))
        cxy = center_xy(m); lo, hi = header('GMan-Planetary-cog10-large', m)
        rimfrac(m, cxy); zprof(m, cxy)
        slice_report(m, cxy, lo[2] + 1.0, own_teeth_regions=(1, 2, 3), png='cog10_z1.png')
        slice_report(m, cxy, lo[2] + 6.0, png='cog10_z6.png')
        body_gaps(m, cxy, topk=12)
    elif which == 'pip':
        m = load(os.path.join(BASE, r"Print+in+Place+Planetary+Gear+Spinner\Planetary Gear Spinner.stl"))
        cxy = center_xy(m); lo, hi = header('PiP-Planetary', m)
        rimfrac(m, cxy); zprof(m, cxy)
        H = hi[2] - lo[2]
        slice_report(m, cxy, lo[2] + 0.25 * H, own_teeth_regions=(0, 1, 2, 3), png='pip_z25.png')
        slice_report(m, cxy, lo[2] + 0.5 * H, own_teeth_regions=(0, 1, 2, 3), png='pip_z50.png')
        body_gaps(m, cxy, topk=10)
    elif which == 'gyro':
        m = load(os.path.join(BASE, r"Gyro+Fidget+Rings\STL Files\gyro_spinner_7_rings.stl"))
        cxy = center_xy(m); lo, hi = header('Gyro-7rings', m)
        rimfrac(m, cxy); zprof(m, cxy, n=8)
        H = hi[2] - lo[2]
        slice_report(m, cxy, lo[2] + 0.5 * H, pitch=0.02, png='gyro_mid.png')
        body_gaps(m, cxy, topk=8, vol_min=5)
    elif which == 'wave':
        m = load(os.path.join(BASE, r"_Wave_+Gyro+Fidget+Spinner+Heavy+Duty\Wave Gyro Fidget Spinner.stl"))
        cxy = center_xy(m); lo, hi = header('WaveGyro', m)
        rimfrac(m, cxy); zprof(m, cxy)
        H = hi[2] - lo[2]
        slice_report(m, cxy, lo[2] + 0.5 * H, pitch=0.025, png='wave_mid.png')
        body_gaps(m, cxy, topk=8, vol_min=20)
    elif which == 'arcspin':
        m = load(os.path.join(BASE, r"FloW_Arcspin_plain_M_Silk_20262101_stls\obj_1_Zusammenbau.stl"))
        cxy = center_xy(m); lo, hi = header('Arcspin', m)
        rimfrac(m, cxy); zprof(m, cxy)
        H = hi[2] - lo[2]
        for f, tag in ((0.2, 'z20'), (0.5, 'z50'), (0.8, 'z80')):
            slice_report(m, cxy, lo[2] + f * H, pitch=0.025, png=f'arc_{tag}.png')
        body_gaps(m, cxy, topk=8, vol_min=20)
    elif which == 'vega':
        print("\n===== Vega rings (nested ring set)")
        import glob
        for n in range(5, 16):
            tot_mass = 0; row = []
            for half in (1, 2):
                fp = os.path.join(BASE, f"Vega_stls\\obj_*_Vega-{n}.stl_{half}.stl")
                g = glob.glob(fp)
                if not g: continue
                mm = load(g[0])
                lo, hi = mm.bounds
                c = center_xy(mm)
                v = mm.vertices
                r = np.hypot(v[:, 0] - c[0], v[:, 1] - c[1])
                tot_mass += abs(mm.volume) * DENS
                row.append(f"half{half}: OD {2*r.max():5.2f} ID {2*r.min():5.2f} H {hi[2]-lo[2]:.2f} vol {abs(mm.volume):5.0f}")
            print(f" Vega-{n}: " + " | ".join(row) + f" | pair mass {tot_mass:.2f} g")
    print(f"[{which} done in {time.time()-t0:.0f}s]")


if __name__ == '__main__':
    for w in sys.argv[1:]:
        try:
            run(w)
        except Exception as e:
            import traceback; traceback.print_exc()
