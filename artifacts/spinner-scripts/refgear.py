import trimesh, numpy as np
p = r"C:\Users\gethi\Downloads\Gear+fidget+spinner.3mf"
s = trimesh.load(p)
name = sorted(s.geometry.keys())[0]
m = s.geometry[name]
print("design %r: %d tris" % (name, len(m.faces)))
parts = m.split(only_watertight=False)
print("separate bodies in this spinner: %d" % len(parts))
cx, cy = m.vertices[:, 0].mean(), m.vertices[:, 1].mean()
rows = []
for b in parts:
    v = b.vertices
    r = np.hypot(v[:, 0] - cx, v[:, 1] - cy)
    c = b.centroid
    rows.append((np.hypot(c[0]-cx, c[1]-cy), r.min(), r.max(),
                 v[:, 2].min(), v[:, 2].max(), abs(b.volume), b))
rows.sort()
print("\n%8s %8s %8s %7s %7s %9s" %
      ("r_centre", "r_min", "r_max", "z_lo", "z_hi", "vol_mm3"))
for rc, rmn, rmx, z0, z1, vol, b in rows:
    print("%8.2f %8.2f %8.2f %7.2f %7.2f %9.1f" % (rc, rmn, rmx, z0, z1, vol))

# z-profile of each body: max radius per z slice reveals flanges/lips
print("\nz-profile (max radius from each body's OWN axis, per 1 mm):")
for rc, rmn, rmx, z0, z1, vol, b in rows[:6]:
    v = b.vertices
    ax, ay = b.centroid[0], b.centroid[1]
    rr = np.hypot(v[:, 0] - ax, v[:, 1] - ay)
    line = []
    for zz in np.arange(0.5, 12.0, 1.0):
        sel = np.abs(v[:, 2] - zz) < 0.6
        line.append("%5.1f" % (rr[sel].max() if sel.any() else 0))
    print("  body r_c=%6.2f :%s" % (rc, "".join(line)))
