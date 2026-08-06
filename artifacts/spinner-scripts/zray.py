"""Vertical ray-casting occupancy: robust to non-watertight meshes.

For a given (x,y) column, casts a ray up through the mesh and returns the
sorted list of z-crossings, which pair up into solid intervals.
"""
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import trimesh


def load_clean(path):
    m = trimesh.load(path, force='mesh')
    m.merge_vertices()
    try:
        m.update_faces(m.nondegenerate_faces())
    except Exception:
        pass
    m.remove_unreferenced_vertices()
    return m


def z_crossings(mesh, pts_xy, z_lo=None, z_hi=None, tol=1e-4):
    """Returns list (per xy point) of sorted unique z hit values."""
    lo, hi = mesh.bounds
    z0 = (lo[2] - 10.0) if z_lo is None else z_lo
    pts_xy = np.asarray(pts_xy, dtype=float).reshape(-1, 2)
    origins = np.c_[pts_xy, np.full(len(pts_xy), z0)]
    dirs = np.tile([0.0, 0.0, 1.0], (len(origins), 1))
    locs, idx_ray, idx_tri = mesh.ray.intersects_location(
        origins, dirs, multiple_hits=True)
    out = [[] for _ in range(len(origins))]
    for L, ir in zip(locs, idx_ray):
        out[ir].append(L[2])
    res = []
    for zs in out:
        zs = np.sort(np.array(zs))
        if len(zs):
            keep = [zs[0]]
            for z in zs[1:]:
                if z - keep[-1] > tol:
                    keep.append(z)
            zs = np.array(keep)
        res.append(zs)
    return res


def intervals(zs):
    """Pair crossings into (enter, exit) solid intervals."""
    if len(zs) % 2 != 0:
        # odd -> drop nothing, just pair greedily
        pass
    return [(zs[i], zs[i + 1]) for i in range(0, len(zs) - 1, 2)]


def fmt_intervals(iv):
    return "  ".join("[%.3f,%.3f]" % (a, b) for a, b in iv)


def ring_pts(cx, cy, r, n=72):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.c_[cx + r * np.cos(t), cy + r * np.sin(t)]


def scan_line(cx, cy, ang_deg, r0, r1, n=60):
    a = np.radians(ang_deg)
    r = np.linspace(r0, r1, n)
    return np.c_[cx + r * np.cos(a), cy + r * np.sin(a)], r
