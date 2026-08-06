"""Mesh forensics helpers for fidget spinner corpus."""
import numpy as np
import trimesh
import shapely
from shapely.geometry import Point
from shapely.ops import unary_union

DENS = 1.24e-3  # g/mm3 PLA


def load(path):
    m = trimesh.load(path, force='mesh')
    return m


def bodies_of(mesh):
    """Split into connected components, sorted by volume desc."""
    parts = mesh.split(only_watertight=False)
    parts = sorted(parts, key=lambda p: -abs(p.volume))
    return parts


def center_xy(mesh):
    lo, hi = mesh.bounds
    return (lo[:2] + hi[:2]) / 2.0


def slice_polys(mesh, z, cxy):
    """Return shapely MultiPolygon of the cross-section at height z, centered on cxy."""
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return None
    planar, T = sec.to_2D()
    polys = planar.polygons_full
    if len(polys) == 0:
        return None
    # T maps 2D homogeneous -> 3D. Find the 2D image of (cxy, z) and shift it to origin.
    Tinv = np.linalg.inv(T)
    p2 = (Tinv @ np.array([cxy[0], cxy[1], z, 1.0]))[:2]
    u = unary_union(list(polys))
    u = shapely.affinity.translate(u, xoff=-p2[0], yoff=-p2[1])
    return u


import shapely.affinity


def radial_occupancy(poly, r_max, n_r=600, n_t=720):
    """occupancy fraction of circumference vs radius. Returns r_grid, occ."""
    r = np.linspace(1e-3, r_max, n_r)
    t = np.linspace(0, 2 * np.pi, n_t, endpoint=False)
    R, T = np.meshgrid(r, t)
    X = (R * np.cos(T)).ravel()
    Y = (R * np.sin(T)).ravel()
    inside = shapely.contains_xy(poly, X, Y).reshape(n_t, n_r)
    occ = inside.mean(axis=0)
    return r, occ


def bands_from_occ(r, occ, thresh=0.0):
    """Contiguous radial bands where occ>thresh; returns list of dicts."""
    on = occ > thresh
    out = []
    i = 0
    n = len(r)
    while i < n:
        if on[i]:
            j = i
            while j + 1 < n and on[j + 1]:
                j += 1
            out.append(dict(r0=r[i], r1=r[j], w=r[j] - r[i],
                            occ_mean=float(occ[i:j + 1].mean()),
                            occ_max=float(occ[i:j + 1].max())))
            i = j + 1
        else:
            i += 1
    return out


def gaps_from_bands(bands):
    gaps = []
    for a, b in zip(bands[:-1], bands[1:]):
        gaps.append(dict(g0=a['r1'], g1=b['r0'], w=b['r0'] - a['r1']))
    return gaps


def body_radial_range(body, cxy, z=None):
    """min/max radius of body vertices about cxy (optionally near height z +-0.5)."""
    v = body.vertices
    if z is not None:
        sel = np.abs(v[:, 2] - z) < 0.6
        if sel.sum() > 10:
            v = v[sel]
    rr = np.hypot(v[:, 0] - cxy[0], v[:, 1] - cxy[1])
    return rr.min(), rr.max()


def min_gap(a, b, n=4000):
    """Minimum surface-to-surface distance between two bodies."""
    from trimesh.proximity import ProximityQuery
    pa = a.sample(n)
    pb = b.sample(n)
    d1 = ProximityQuery(b).signed_distance(pa)
    d2 = ProximityQuery(a).signed_distance(pb)
    # distances are positive outside? signed_distance: positive INSIDE. take abs of min magnitude outside
    d = np.concatenate([-d1, -d2])  # positive = outside
    return float(d.min())


def min_gap_fast(a, b, n=6000):
    """Min distance using nearest-surface query (unsigned)."""
    from trimesh.proximity import ProximityQuery
    pa = a.sample(n)
    _, d1, _ = ProximityQuery(b).on_surface(pa)
    pb = b.sample(n)
    _, d2, _ = ProximityQuery(a).on_surface(pb)
    return float(min(d1.min(), d2.min()))


def rim_fraction(mesh, cxy, frac=0.8, n_slices=25):
    """Volume fraction beyond frac*Rmax, via slice-area integration."""
    lo, hi = mesh.bounds
    rmax = max_radius(mesh, cxy)
    zs = np.linspace(lo[2] + 0.05, hi[2] - 0.05, n_slices)
    circ = Point(0, 0).buffer(frac * rmax, resolution=128)
    tot = 0.0
    rim = 0.0
    for z in zs:
        u = slice_polys(mesh, z, cxy)
        if u is None:
            continue
        tot += u.area
        rim += u.difference(circ).area
    return rim / tot if tot > 0 else 0.0, rmax


def max_radius(mesh, cxy):
    v = mesh.vertices
    return float(np.hypot(v[:, 0] - cxy[0], v[:, 1] - cxy[1]).max())


def z_area_profile(mesh, cxy, n=40):
    lo, hi = mesh.bounds
    zs = np.linspace(lo[2] + 0.05, hi[2] - 0.05, n)
    out = []
    for z in zs:
        u = slice_polys(mesh, z, cxy)
        out.append((z, 0.0 if u is None else u.area))
    return out


def tooth_profile(poly_or_body_slice, cxy_already_centered=True, n_t=2880):
    """r(theta) outer profile of a centered shapely polygon; returns theta, r arrays."""
    poly = poly_or_body_slice
    t = np.linspace(0, 2 * np.pi, n_t, endpoint=False)
    # ray cast: max radius along each direction using boundary intersection
    from shapely.geometry import LineString
    rmax_glob = poly.bounds
    R = max(abs(rmax_glob[0]), abs(rmax_glob[1]), abs(rmax_glob[2]), abs(rmax_glob[3])) * 1.1
    r_out = np.zeros(n_t)
    r_in = np.zeros(n_t)
    b = poly.boundary
    for i, th in enumerate(t):
        ray = LineString([(0, 0), (R * np.cos(th), R * np.sin(th))])
        x = ray.intersection(b)
        if x.is_empty:
            r_out[i] = np.nan
            r_in[i] = np.nan
            continue
        pts = []
        if x.geom_type == 'Point':
            pts = [x]
        elif hasattr(x, 'geoms'):
            for g in x.geoms:
                if g.geom_type == 'Point':
                    pts.append(g)
                elif g.geom_type == 'LineString':
                    pts.extend([Point(c) for c in g.coords])
        rs = [np.hypot(p.x, p.y) for p in pts]
        r_out[i] = max(rs)
        r_in[i] = min(rs)
    return t, r_out, r_in


def count_teeth(r_theta):
    """Count teeth by counting crossings above midline."""
    r = r_theta[~np.isnan(r_theta)]
    mid = (np.nanmax(r) + np.nanmin(r)) / 2
    on = r > mid
    # count rising edges (circular)
    edges = np.sum((~on[:-1]) & on[1:]) + (1 if (not on[-1]) and on[0] else 0)
    return int(edges), float(np.nanmin(r)), float(np.nanmax(r))


def summarize_bodies(parts, cxy):
    rows = []
    for i, p in enumerate(parts):
        lo, hi = p.bounds
        rmin, rmax = body_radial_range(p, cxy)
        rows.append(dict(i=i, vol=abs(p.volume), mass=abs(p.volume) * DENS,
                         z0=lo[2], z1=hi[2], rmin=rmin, rmax=rmax,
                         watertight=p.is_watertight, faces=len(p.faces)))
    return rows


def fmt_bodies(rows):
    s = " i    vol_mm3   mass_g     z-range        r_in..r_out   wt\n"
    for r in rows:
        s += (f"{r['i']:2d} {r['vol']:9.0f} {r['mass']:7.2f}  "
              f"{r['z0']:6.2f}..{r['z1']:6.2f}  {r['rmin']:6.2f}..{r['rmax']:6.2f}  {str(r['watertight'])[0]}\n")
    return s
