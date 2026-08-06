"""Vertical-clearance forensics for print-in-place loose bodies."""
import sys, os, math
import numpy as np
import trimesh

np.set_printoptions(suppress=True, precision=3)


def load(path):
    m = trimesh.load(path, force='mesh')
    return m


def split(m, min_vol=1.0):
    parts = m.split(only_watertight=False)
    if len(parts) == 0:
        parts = [m]
    parts = [p for p in parts if abs(p.volume) > min_vol or len(p.faces) > 50]
    parts = sorted(parts, key=lambda p: -abs(p.volume))
    return parts


def summarize(parts, label=""):
    print(f"--- bodies ({label}) n={len(parts)} ---")
    print(" i    vol_mm3   z0     z1     cx      cy      r_c    xy_extent   faces  wt")
    rows = []
    for i, p in enumerate(parts):
        lo, hi = p.bounds
        c = (lo + hi) / 2
        r_c = math.hypot(c[0], c[1])
        rows.append((i, abs(p.volume), lo[2], hi[2], c[0], c[1], r_c,
                     hi[0] - lo[0], hi[1] - lo[1], len(p.faces), p.is_watertight))
        print(f"{i:3d} {abs(p.volume):9.1f} {lo[2]:6.2f} {hi[2]:6.2f} "
              f"{c[0]:7.2f} {c[1]:7.2f} {r_c:6.2f}  {hi[0]-lo[0]:5.2f}x{hi[1]-lo[1]:5.2f} "
              f"{len(p.faces):7d}  {str(p.is_watertight)[0]}")
    return rows


def z_hist(part, dz=0.05):
    """Histogram of vertex z counts - reveals flat faces."""
    z = part.vertices[:, 2]
    lo, hi = z.min(), z.max()
    bins = np.arange(lo, hi + dz, dz)
    h, e = np.histogram(z, bins=bins)
    return h, e


def underside_profile(part, nz=40, zspan=3.0):
    """Cross-section area of a body vs height in the bottom zspan mm.
    Reveals flat (constant area) vs chamfered/domed (area growing) undersides."""
    lo, hi = part.bounds
    z0 = lo[2]
    out = []
    zs = z0 + np.linspace(0.001, min(zspan, (hi[2] - z0) * 0.98), nz)
    for z in zs:
        sec = part.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if sec is None:
            out.append((z - z0, 0.0, 0.0))
            continue
        try:
            planar, T = sec.to_2D()
            a = sum(pp.area for pp in planar.polygons_full)
            # equivalent radius
            r = math.sqrt(a / math.pi) if a > 0 else 0.0
            out.append((z - z0, a, r))
        except Exception:
            out.append((z - z0, float('nan'), float('nan')))
    return out


def xy_footprint_overlap(a, b):
    """Do bodies a,b overlap in XY (bounding-box test) and by how much."""
    la, ha = a.bounds
    lb, hb = b.bounds
    ox = min(ha[0], hb[0]) - max(la[0], lb[0])
    oy = min(ha[1], hb[1]) - max(la[1], lb[1])
    return ox, oy


def vertical_gap(upper, lower, nsamp=200000):
    """For points on upper's lower surface, find highest lower-body surface directly beneath.
    Uses ray casting straight down from sampled points on the upper body's bottom region."""
    lo, hi = upper.bounds
    # sample points on the bottom 0.3mm of the upper body
    v = upper.vertices
    sel = v[:, 2] < lo[2] + 0.25
    pts = v[sel]
    if len(pts) == 0:
        return None
    origins = pts.copy()
    origins[:, 2] = lo[2] - 0.001
    dirs = np.tile([0, 0, -1.0], (len(origins), 1))
    try:
        locs, idx_ray, _ = lower.ray.intersects_location(origins, dirs, multiple_hits=False)
    except Exception:
        return None
    if len(locs) == 0:
        return None
    gaps = origins[idx_ray][:, 2] - locs[:, 2]
    return dict(n=len(gaps), gmin=float(gaps.min()), gmed=float(np.median(gaps)),
                gmax=float(gaps.max()), gmean=float(gaps.mean()))


def gap_to_all_below(upper, others, tag=""):
    lo, hi = upper.bounds
    res = []
    for j, o in enumerate(others):
        ol, oh = o.bounds
        if oh[2] < lo[2] + 0.5:  # candidate lies below
            ox, oy = xy_footprint_overlap(upper, o)
            if ox > 0 and oy > 0:
                res.append((j, oh[2], lo[2] - oh[2], ox, oy))
    return res
