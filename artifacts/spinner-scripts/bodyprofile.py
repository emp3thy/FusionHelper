"""Underside / clearance profiling for print-in-place assemblies."""
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import trimesh
import math


def clean(path):
    m = trimesh.load(path, force='mesh')
    m.merge_vertices()
    try:
        m.update_faces(m.unique_faces())
    except Exception:
        pass
    m.remove_unreferenced_vertices()
    return m


def comps(m, minf=30):
    return sorted([c for c in m.split(only_watertight=False) if len(c.faces) > minf],
                  key=lambda p: -abs(p.volume))


def sec_area(body, z):
    s = body.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return 0.0, 0.0
    try:
        pl, T = s.to_2D()
        a = sum(p.area for p in pl.polygons_full)
        per = sum(p.length for p in pl.polygons_full)
        return a, per
    except Exception:
        return float('nan'), float('nan')


def underside(body, name, zs=None, span=2.0, n=21):
    lo, hi = body.bounds
    if zs is None:
        zs = lo[2] + np.concatenate([[0.001, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4,
                                      0.5, 0.6, 0.8, 1.0, 1.5, 2.0]])
    print('  %s  z0=%.4f z1=%.4f' % (name, lo[2], hi[2]))
    print('     dz_above_bottom   area_mm2   equiv_r    d_area')
    prev = None
    for z in zs:
        a, p = sec_area(body, z)
        d = '' if prev is None else '%+.3f' % (a - prev)
        r = math.sqrt(a / math.pi) if a > 0 else 0
        print('        %7.3f      %9.3f   %7.4f   %s' % (z - lo[2], a, r, d))
        prev = a


def zlevels(body, tol=1e-4):
    z = body.vertices[:, 2]
    u = np.unique(np.round(z, 4))
    return u


def flatface_area(body, zt, tol=1e-5):
    """Total area of triangles lying in plane z=zt."""
    v = body.vertices
    f = body.faces
    zz = v[f][:, :, 2]
    sel = np.all(np.abs(zz - zt) < tol, axis=1)
    if sel.sum() == 0:
        return 0.0, 0
    tris = v[f[sel]]
    a = trimesh.triangles.area(tris).sum()
    return a, int(sel.sum())


def min_clearance(a, b, n=40000):
    """Minimum surface-surface distance between two bodies."""
    from trimesh.proximity import ProximityQuery
    pa = a.sample(n)
    _, d1, _ = ProximityQuery(b).on_surface(pa)
    pb = b.sample(n)
    _, d2, _ = ProximityQuery(a).on_surface(pb)
    return float(min(d1.min(), d2.min())), float(np.percentile(d1, 1)), float(np.percentile(d2, 1))
