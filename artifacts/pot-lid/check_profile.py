"""Offline check of `pot_lid_author.py`: Pappus volume, key dimensions, and a
comparison of the revolve profile against the printed part's walls recovered
from gcode (`printed_section.csv`, made by `gcode_section.py`).

Loads the author module with a stand-in `adsk` so its pure-Python profile
functions can run outside Fusion. Prints the deviation of every printed
outer-wall and top-surface point from the profile outline (walls are offset
by half a line width to the true surface) and writes
`profile_vs_printed.png`.

Usage: python check_profile.py            (run from this directory)
"""
import csv
import importlib.util
import math
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
HALF_LINE = 0.21   # half of the 0.42 mm outer-wall line width


def load_author():
    fake = types.ModuleType("adsk")
    fake.core = types.ModuleType("adsk.core")
    fake.fusion = types.ModuleType("adsk.fusion")
    fake.doEvents = lambda: None
    sys.modules.setdefault("adsk", fake)
    sys.modules.setdefault("adsk.core", fake.core)
    sys.modules.setdefault("adsk.fusion", fake.fusion)
    bk = types.ModuleType("fusionhelper.buildkit")
    bk.BuildCtx = object
    sys.modules.setdefault("fusionhelper", types.ModuleType("fusionhelper"))
    sys.modules.setdefault("fusionhelper.buildkit", bk)
    spec = importlib.util.spec_from_file_location(
        "pot_lid_author", os.path.join(HERE, "pot_lid_author.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def seg_distance(p, a, b):
    """Distance from point p to segment a-b."""
    ax, az = a
    bx, bz = b
    px, pz = p
    dx, dz = bx - ax, bz - az
    L2 = dx * dx + dz * dz
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L2))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz))


def outline_distance(p, poly):
    return min(seg_distance(p, poly[i], poly[(i + 1) % len(poly)])
               for i in range(len(poly)))


def main():
    mod = load_author()
    poly = mod.profile_polygon()
    vol = mod.pappus_volume_cm3()
    k = math.tan(math.radians(mod.DRAFT_DEG))
    print("segments: %d, polygon points: %d" % (len(mod.profile_segments()), len(poly)))
    print("Pappus volume: %.4f cm3" % vol)
    print("height: %.2f mm   base dia: %.2f mm   plateau dia: %.2f mm"
          % (mod.RING_PEAK_Z, 2 * mod.COLLAR_R0, 2 * (mod.COLLAR_R0 - k * mod.LID_H)))
    print("groove: inner dia %.2f, outer dia %.2f at base -> %.2f at ceiling, depth %.2f"
          % (2 * mod.PLUG_R, 2 * mod.GROOVE_R0,
             2 * (mod.GROOVE_R0 - k * mod.GROOVE_DEPTH), mod.GROOVE_DEPTH))
    rmax = max(r for r, _ in poly)
    zmax = max(z for _, z in poly)
    zmin = min(z for _, z in poly)
    assert abs(rmax - mod.COLLAR_R0) < 1e-6, rmax
    assert abs(zmax - mod.RING_PEAK_Z) < 1e-6, zmax
    assert abs(zmin) < 1e-9, zmin

    # Simple polygon check: no two non-adjacent edges may cross.
    n = len(poly)

    def crosses(a, b, c, d):
        def orient(p, q, r):
            return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return (orient(a, b, c) * orient(a, b, d) < 0
                and orient(c, d, a) * orient(c, d, b) < 0)

    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if crosses(poly[i], poly[(i + 1) % n], poly[j], poly[(j + 1) % n]):
                raise SystemExit("profile self-intersects at edges %d and %d" % (i, j))
    print("profile is a simple closed polygon")

    csv_path = os.path.join(HERE, "printed_section.csv")
    if not os.path.exists(csv_path):
        print("no printed_section.csv; skipping comparison")
        return 0
    printed = {"Outer wall": [], "Top surface": []}
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["feature"] in printed:
                printed[row["feature"]].append((float(row["r_mm"]), float(row["z_mm"])))

    # Outer-wall centrelines sit HALF_LINE inside the surface. Push each
    # point outward along the local normal, approximated radially for the
    # side walls and vertically for the top skin.
    def surface_points():
        out = []
        for r, z in printed["Outer wall"]:
            out.append(("wall", r + HALF_LINE if r > 1.0 else r, z))
        for r, z in printed["Top surface"]:
            out.append(("top", r, z + 0.08))
        return out

    devs = []
    for kind, r, z in surface_points():
        devs.append((outline_distance((r, z), poly), kind, r, z))
    devs.sort(reverse=True)
    walls = [d for d in devs if d[1] == "wall"]
    tops = [d for d in devs if d[1] == "top"]
    for name, ds in (("outer walls", walls), ("top surface", tops)):
        if not ds:
            continue
        vals = [d[0] for d in ds]
        vals_sorted = sorted(vals)
        p95 = vals_sorted[int(0.95 * (len(vals_sorted) - 1))]
        print("%s: n=%d mean=%.3f p95=%.3f max=%.3f mm" % (
            name, len(vals), sum(vals) / len(vals), p95, vals_sorted[-1]))
    print("worst 8 printed points vs profile:")
    for d, kind, r, z in devs[:8]:
        print("   %.2f mm  %-4s r=%.2f z=%.2f" % (d, kind, r, z))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; PNG skipped")
        return 0
    fig, ax = plt.subplots(figsize=(14, 6))
    for feat, colour in (("Outer wall", "0.6"), ("Top surface", "tab:red")):
        if printed[feat]:
            rs, zs = zip(*printed[feat])
            ax.scatter(rs, zs, s=2, c=colour, label="printed: " + feat.lower(), rasterized=True)
    rs = [p[0] for p in poly] + [poly[0][0]]
    zs = [p[1] for p in poly] + [poly[0][1]]
    ax.plot(rs, zs, "b-", lw=1.2, label="pot_lid_author profile")
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3)
    ax.set_xlabel("radius (mm)")
    ax.set_ylabel("z (mm)")
    ax.legend(markerscale=6, fontsize=8)
    ax.set_title("pot lid: rebuilt revolve profile over the printed section")
    out = os.path.join(HERE, "profile_vs_printed.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
