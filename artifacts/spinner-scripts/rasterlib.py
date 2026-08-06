"""Raster-based slice forensics: robust to dirty multi-shell STLs."""
import numpy as np
import trimesh
from matplotlib.path import Path as MplPath
from scipy import ndimage

DENS = 1.24e-3  # g/mm3 PLA


def load(path):
    return trimesh.load(path, force='mesh')


def center_xy(mesh):
    lo, hi = mesh.bounds
    return (lo[:2] + hi[:2]) / 2.0


def slice_rings(mesh, z):
    """Closed 2D rings (world xy) of the section at z."""
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return []
    return [d[:, :2] for d in sec.discrete]


def rasterize(rings, pitch=0.025, pad=0.5, bounds=None, dedup=False):
    """Even-odd scanline rasterization of all rings combined.

    dedup=True: multiple crossings landing in the same raster cell count once
    (kills exactly-coincident duplicated shell boundaries).
    Returns bool grid (ny,nx), (x0,y0) of pixel [0,0] center, pitch."""
    rings = [r for r in rings if len(r) >= 3]
    if not rings:
        return None, None, pitch
    if bounds is None:
        allpts = np.vstack(rings)
        x0, y0 = allpts.min(axis=0) - pad
        x1, y1 = allpts.max(axis=0) + pad
    else:
        (x0, y0), (x1, y1) = bounds
    nx = int(np.ceil((x1 - x0) / pitch)) + 1
    ny = int(np.ceil((y1 - y0) / pitch)) + 1
    # gather all segments (each ring closed: last==first assumed; close anyway)
    seg_a = []
    seg_b = []
    for ring in rings:
        a = ring
        b = np.roll(ring, -1, axis=0)
        seg_a.append(a)
        seg_b.append(b)
    A = np.vstack(seg_a)
    B = np.vstack(seg_b)
    X0, Y0 = A[:, 0], A[:, 1]
    X1, Y1 = B[:, 0], B[:, 1]
    ylo = np.minimum(Y0, Y1)
    yhi = np.maximum(Y0, Y1)
    j0 = np.ceil((ylo - y0) / pitch).astype(np.int64)
    j1 = (np.ceil((yhi - y0) / pitch) - 1).astype(np.int64)
    j0 = np.clip(j0, 0, ny - 1)
    cnt = np.maximum(0, j1 - j0 + 1)
    total = int(cnt.sum())
    if total == 0:
        return np.zeros((ny, nx), dtype=bool), (x0, y0), pitch
    idx = np.repeat(np.arange(len(cnt)), cnt)
    starts = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    offs = np.arange(total) - np.repeat(starts, cnt)
    rows = j0[idx] + offs
    y = y0 + rows * pitch
    dy = Y1[idx] - Y0[idx]
    t = (y - Y0[idx]) / dy
    x = X0[idx] + t * (X1[idx] - X0[idx])
    cols = np.ceil((x - x0) / pitch).astype(np.int64)
    cols = np.clip(cols, 0, nx)  # nx = off-grid sentinel col in diff array
    diff = np.zeros((ny, nx + 1), dtype=np.int32)
    np.add.at(diff, (rows, cols), 1)
    if dedup:
        diff = (diff > 0).astype(np.int32)
    parity = np.cumsum(diff[:, :nx], axis=1) % 2
    return parity.astype(bool), (x0, y0), pitch


def _pt_tri_dist(P, T):
    """Exact distance from points P (n,3) to triangles T (n,3,3), paired."""
    from trimesh.triangles import closest_point
    C = closest_point(T, P)
    return np.linalg.norm(P - C, axis=1)


def gap3d(a, b, k=30, expand=0.4):
    """Fast near-exact min surface gap between two meshes."""
    from scipy.spatial import cKDTree
    va, vb = a.vertices, b.vertices
    ta = cKDTree(va)
    dvv, _ = ta.query(vb, k=1)
    dmin = dvv.min()
    best = dmin
    for src, dst in ((a, b), (b, a)):
        # dst vertices near src surface
        tsrc = cKDTree(src.vertices)
        d, _ = tsrc.query(dst.vertices, k=1)
        sel = d < dmin + expand
        pts = dst.vertices[sel]
        if len(pts) == 0:
            continue
        cent = src.triangles_center
        tc = cKDTree(cent)
        kk = min(k, len(cent))
        _, fidx = tc.query(pts, k=kk)
        if kk == 1:
            fidx = fidx[:, None]
        P = np.repeat(pts, kk, axis=0)
        T = src.triangles[fidx.ravel()]
        dd = _pt_tri_dist(P, T)
        best = min(best, dd.min())
    return float(best)


class BodySlicer:
    """Slice a dirty multi-shell mesh: per-3D-body even-odd raster, OR-combined.

    Robust against duplicated/coincident shells across bodies."""

    def __init__(self, mesh, vol_min=5.0):
        parts = mesh.split(only_watertight=False)
        self.bodies = [p for p in parts if abs(p.volume) > vol_min]
        self.bodies.sort(key=lambda p: -abs(p.volume))
        self.mesh = mesh

    def raster(self, z, pitch=0.03, pad=0.5):
        lo, hi = self.mesh.bounds
        bounds = ((lo[0] - pad, lo[1] - pad), (hi[0] + pad, hi[1] + pad))
        acc = None
        for b in self.bodies:
            blo, bhi = b.bounds
            if not (blo[2] < z < bhi[2]):
                continue
            rings = slice_rings(b, z)
            g, o, p = rasterize(rings, pitch, bounds=bounds)
            if g is None:
                continue
            acc = g if acc is None else (acc | g)
        if acc is None:
            return None, None, pitch
        return acc, bounds[0], pitch


def grid_coords(grid, origin, pitch):
    ny, nx = grid.shape
    xs = origin[0] + np.arange(nx) * pitch
    ys = origin[1] + np.arange(ny) * pitch
    return xs, ys


def regions(grid, min_area_mm2=1.0, pitch=0.025):
    """Label connected material regions; return label array + sizes (mm2), sorted desc."""
    lab, n = ndimage.label(grid, structure=np.ones((3, 3)))
    sizes = ndimage.sum(grid, lab, index=np.arange(1, n + 1)) * pitch * pitch
    order = np.argsort(-sizes)
    keep = [(int(order[k]) + 1, float(sizes[order[k]])) for k in range(n)
            if sizes[order[k]] >= min_area_mm2]
    return lab, keep


def region_clearance(lab, a, b, pitch):
    """Min gap (mm, edge-to-edge approx) between labeled regions a and b."""
    A = lab == a
    B = lab == b
    # EDT of ~A gives distance from each pixel to nearest A pixel (center-to-center)
    d = ndimage.distance_transform_edt(~A) * pitch
    val = d[B].min()
    # convert center-to-center to edge gap: subtract ~1 pixel
    return max(0.0, float(val - pitch))


def radial_occupancy_grid(grid, origin, pitch, cxy, n_r=800):
    xs, ys = grid_coords(grid, origin, pitch)
    gx, gy = np.meshgrid(xs - cxy[0], ys - cxy[1])
    rr = np.hypot(gx, gy)
    rmax = rr[grid].max() if grid.any() else 0
    edges = np.linspace(0, rmax + pitch, n_r + 1)
    which = np.digitize(rr.ravel(), edges) - 1
    which = np.clip(which, 0, n_r - 1)
    tot = np.bincount(which, minlength=n_r).astype(float)
    occ_cnt = np.bincount(which[grid.ravel()], minlength=n_r).astype(float)
    occ = np.where(tot > 0, occ_cnt / np.maximum(tot, 1), 0)
    r_mid = 0.5 * (edges[:-1] + edges[1:])
    return r_mid, occ


def bands(r, occ, thresh=0.004):
    on = occ > thresh
    out, i, n = [], 0, len(r)
    while i < n:
        if on[i]:
            j = i
            while j + 1 < n and on[j + 1]:
                j += 1
            out.append(dict(r0=r[i], r1=r[j], w=r[j] - r[i],
                            occ_mean=float(occ[i:j + 1].mean())))
            i = j + 1
        else:
            i += 1
    return out


def gaps(bds):
    return [dict(g0=a['r1'], w=b['r0'] - a['r1']) for a, b in zip(bds[:-1], bds[1:])]


def fmt_bands(bds, gps):
    s = " | ".join(f"{b['r0']:.2f}-{b['r1']:.2f} (w{b['w']:.2f}, occ{b['occ_mean']:.2f})" for b in bds)
    if gps:
        s += "\n      gaps: " + " | ".join(f"@r{g['g0']:.2f} w={g['w']:.2f}" for g in gps)
    return s


def r_theta_of_region(lab, idx, origin, pitch, cxy, n_t=1440):
    """Outer and inner radius vs angle for one labeled region (from pixels)."""
    ys_idx, xs_idx = np.nonzero(lab == idx)
    x = origin[0] + xs_idx * pitch - cxy[0]
    y = origin[1] + ys_idx * pitch - cxy[1]
    r = np.hypot(x, y)
    t = np.arctan2(y, x) % (2 * np.pi)
    bin_ = (t / (2 * np.pi) * n_t).astype(int) % n_t
    r_out = np.full(n_t, np.nan)
    r_in = np.full(n_t, np.nan)
    np.maximum.at(r_out, bin_, np.where(np.isnan(r_out[bin_]), r, r))
    # numpy maximum.at with nan doesn't work; do manually
    r_out = np.full(n_t, -np.inf)
    r_in = np.full(n_t, np.inf)
    np.maximum.at(r_out, bin_, r)
    np.minimum.at(r_in, bin_, r)
    r_out[np.isinf(r_out)] = np.nan
    r_in[np.isinf(r_in)] = np.nan
    return r_out, r_in


def count_teeth(rt):
    good = ~np.isnan(rt)
    if good.sum() < 10:
        return 0, np.nan, np.nan
    r = np.where(good, rt, np.nanmedian(rt))
    lo, hi = np.nanmin(rt), np.nanmax(rt)
    mid = (lo + hi) / 2
    on = r > mid
    edges = int(np.sum((~on[:-1]) & on[1:]) + ((not on[-1]) and on[0]))
    return edges, float(lo), float(hi)


def z_slices(mesh, n=9, margin=0.15):
    lo, hi = mesh.bounds
    return np.linspace(lo[2] + margin, hi[2] - margin, n)


def rim_fraction_raster(mesh, cxy, frac=0.8, n=15, pitch=0.06):
    zs = z_slices(mesh, n)
    tot = rim = 0.0
    rmax_all = 0.0
    slabs = []
    for z in zs:
        rings = slice_rings(mesh, z)
        g, o, p = rasterize(rings, pitch)
        if g is None:
            slabs.append((z, None))
            continue
        slabs.append((z, (g, o, p)))
        xs, ys = grid_coords(g, o, p)
        gx, gy = np.meshgrid(xs - cxy[0], ys - cxy[1])
        rr = np.hypot(gx, gy)[g]
        if len(rr):
            rmax_all = max(rmax_all, rr.max())
    for z, pack in slabs:
        if pack is None:
            continue
        g, o, p = pack
        xs, ys = grid_coords(g, o, p)
        gx, gy = np.meshgrid(xs - cxy[0], ys - cxy[1])
        rr = np.hypot(gx, gy)[g]
        tot += len(rr)
        rim += (rr > frac * rmax_all).sum()
    return (rim / tot if tot else 0.0), rmax_all
