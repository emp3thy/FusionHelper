"""Recover the (r, z) cross-section of a rotationally symmetric print from a
Bambu `.gcode.3mf`.

The sliced archive carries no mesh, only toolpaths, but for a solid of
revolution every extrusion move's distance from the part centre is a point on
the profile. This reads `Metadata/plate_1.gcode`, takes the part centre from
`Metadata/plate_1.json`, and writes:

* `<out>.csv`  - one row per sampled extrusion point: feature, r_mm, z_mm
* `<out>.png`  - the section, coloured by slicer feature

Outer-wall centrelines sit half a line width (0.21 mm at 0.42 mm) inside the
true surface; `check_profile.py` applies that offset when comparing.

Usage: python gcode_section.py pot_lid.gcode.3mf printed_section
"""
import collections
import json
import math
import re
import sys
import zipfile

KEEP = ("Outer wall", "Inner wall", "Top surface", "Bottom surface", "Bridge")


def read_points(path, min_run=12):
    with zipfile.ZipFile(path) as zf:
        plate = json.loads(zf.read("Metadata/plate_1.json"))
        gcode = zf.read("Metadata/plate_1.gcode").decode("utf-8", "ignore")
    bb = plate["bbox_all"]
    cx, cy = (bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0
    pts = collections.defaultdict(set)
    z = None
    feat = None
    x = y = None
    run = []          # samples of the current contiguous extrusion run
    run_feat = None

    def flush():
        # Seam hops and wipe stubs are labelled as walls but are only a
        # couple of samples long; they are not geometry. Keep real runs.
        if run_feat in KEEP and len(run) >= min_run:
            pts[run_feat].update(run)
        run.clear()

    for line in gcode.splitlines():
        if line.startswith("; FEATURE:"):
            flush()
            feat = line[10:].strip()
            run_feat = feat
            continue
        if not line or line[0] == ";":
            continue
        if line[:2] in ("G1", "G0", "G2", "G3"):
            m = dict(re.findall(r"([XYZE])(-?[\d.]+)", line))
            if "Z" in m:
                flush()
                z = float(m["Z"])
            nx = float(m["X"]) if "X" in m else x
            ny = float(m["Y"]) if "Y" in m else y
            extruding = "E" in m and float(m["E"]) > 0
            if (extruding and x is not None and nx is not None and z is not None
                    and feat in KEEP):
                length = math.hypot(nx - x, ny - y)
                n = max(1, int(length / 0.3))
                for i in range(n + 1):
                    t = i / n
                    r = math.hypot(x + (nx - x) * t - cx, y + (ny - y) * t - cy)
                    run.append((round(r, 2), round(z, 2)))
            elif not extruding:
                flush()
            x, y = nx, ny
    flush()
    return (cx, cy), pts


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, out = argv[1], argv[2]
    centre, pts = read_points(src)
    with open(out + ".csv", "w", encoding="utf-8") as f:
        f.write("feature,r_mm,z_mm\n")
        for feat in KEEP:
            for r, z in sorted(pts.get(feat, ())):
                f.write("%s,%.2f,%.2f\n" % (feat, r, z))
    print("centre (%.3f, %.3f); points: %s" % (
        centre[0], centre[1],
        ", ".join("%s=%d" % (k, len(v)) for k, v in sorted(pts.items()))))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; CSV written, PNG skipped")
        return 0
    fig, ax = plt.subplots(figsize=(14, 6))
    colours = {"Outer wall": "k", "Inner wall": "tab:blue", "Top surface": "tab:red",
               "Bottom surface": "tab:orange", "Bridge": "tab:purple"}
    for feat in KEEP:
        if feat not in pts:
            continue
        rs, zs = zip(*sorted(pts[feat]))
        ax.scatter(rs, zs, s=2, c=colours[feat], label=feat, rasterized=True)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3)
    ax.set_xlabel("radius (mm)")
    ax.set_ylabel("z (mm)")
    ax.legend(markerscale=6, fontsize=8)
    ax.set_title("%s: section from gcode" % src)
    fig.savefig(out + ".png", dpi=150, bbox_inches="tight")
    print("wrote %s.csv and %s.png" % (out, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
