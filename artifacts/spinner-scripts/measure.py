import sys, os, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings('ignore')
import numpy as np
from rasterlib import *

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spinners')


def region_report(slicer, cxy, z, pitch=0.03, topn=10, pairs=True, teeth=True, savepng=None):
    g, o, p = slicer.raster(z, pitch)
    if g is None:
        print(f" z={z:.2f}: empty")
        return
    lab, keep = regions(g, 0.5, p)
    print(f" z={z:.2f}: total area {g.sum()*p*p:.0f} mm2, {len(keep)} regions >0.5mm2")
    for k, (li, ar) in enumerate(keep[:topn]):
        ys, xs = np.nonzero(lab == li)
        x = o[0] + xs * p - cxy[0]
        y = o[1] + ys * p - cxy[1]
        r = np.hypot(x, y)
        cx, cy = x.mean(), y.mean()
        rc = np.hypot(cx, cy)
        rl = np.hypot(x - cx, y - cy)
        line = (f"  R{k}: area {ar:7.1f}  r {r.min():6.2f}..{r.max():6.2f}  "
                f"centroid@r={rc:5.2f}  localDia {2*rl.max():6.2f}/eq {2*np.sqrt(ar/np.pi):5.2f}")
        if teeth and ar > 20:
            r_out, r_in = r_theta_of_region(lab, li, o, p, cxy)
            n_o, lo_o, hi_o = count_teeth(r_out)
            n_i, lo_i, hi_i = count_teeth(-r_in)
            if not np.isnan(lo_o):
                line += f"  teethOut~{n_o}({lo_o:.2f}-{hi_o:.2f})  teethIn~{n_i}(r{-hi_i:.2f}-{-lo_i:.2f})"
        print(line)
    if pairs and len(keep) >= 2:
        n = min(len(keep), 6)
        for i in range(n):
            for j in range(i + 1, n):
                c = region_clearance(lab, keep[i][0], keep[j][0], p)
                if c < 2.5:
                    print(f"   gap R{i}-R{j}: {c:.3f} mm")
    if savepng:
        import matplotlib; matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.figure(figsize=(9, 9))
        show = np.zeros_like(lab, dtype=float)
        for k, (li, ar) in enumerate(keep[:topn]):
            show[lab == li] = (k % 19) + 1
        plt.imshow(show, origin='lower', cmap='tab20', interpolation='nearest')
        plt.title(f"z={z}")
        plt.savefig(savepng, dpi=55, bbox_inches='tight')
        plt.close()
    return g, o, p


def rim_fraction_slicer(slicer, cxy, frac=0.8, n=11, pitch=0.1):
    lo, hi = slicer.mesh.bounds
    zs = np.linspace(lo[2] + 0.12, hi[2] - 0.12, n)
    packs = []
    rmax_all = 0.0
    for z in zs:
        g, o, p = slicer.raster(z, pitch)
        if g is None:
            continue
        xs, ys = grid_coords(g, o, p)
        gx, gy = np.meshgrid(xs - cxy[0], ys - cxy[1])
        rr = np.hypot(gx, gy)[g]
        if len(rr):
            rmax_all = max(rmax_all, rr.max())
            packs.append(rr)
    tot = sum(len(rr) for rr in packs)
    rim = sum((rr > frac * rmax_all).sum() for rr in packs)
    return (rim / tot if tot else 0), rmax_all


def zprofile(slicer, n=16, pitch=0.12):
    lo, hi = slicer.mesh.bounds
    zs = np.linspace(lo[2] + 0.1, hi[2] - 0.1, n)
    out = []
    for z in zs:
        g, o, p = slicer.raster(z, pitch)
        out.append((z, 0 if g is None else g.sum() * p * p))
    return out


def full(name, rel, zlist, pitch=0.03, png_z=None, vol_min=5.0, do_rim=True, do_prof=True):
    path = os.path.join(BASE, rel)
    m = load(path)
    cxy = center_xy(m)
    lo, hi = m.bounds
    print(f"\n#### {name}: bbox {hi[0]-lo[0]:.1f}x{hi[1]-lo[1]:.1f}x{hi[2]-lo[2]:.1f}, vol {abs(m.volume):.0f} mm3 ({abs(m.volume)*DENS:.1f} g)")
    sl = BodySlicer(m, vol_min)
    print(f"3D bodies >{vol_min}mm3: {len(sl.bodies)}")
    if do_rim:
        rf, rmax = rim_fraction_slicer(sl, cxy)
        print(f"Rmax {rmax:.2f} | vol beyond 0.8R: {rf*100:.1f}%")
    for z in zlist:
        zz = lo[2] + z if z >= 0 else hi[2] + z
        png = f"{name}_z{z}.png".replace(' ', '_') if (png_z is not None and abs(z - png_z) < 1e-6) else None
        region_report(sl, cxy, zz, pitch, savepng=png)
    if do_prof:
        prof = zprofile(sl)
        print("   z:area " + " ".join(f"{z:.1f}:{a:.0f}" for z, a in prof))
    return m, cxy, sl
