"""Offline 2D preview of the fixed art (no Fusion needed)."""
import importlib.util
import sys
import types
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

here = Path(__file__).parent
for _n in ("adsk", "adsk.core", "adsk.fusion", "fusionhelper",
           "fusionhelper.buildkit"):
    sys.modules[_n] = types.ModuleType(_n)
setattr(sys.modules["fusionhelper.buildkit"], "BuildCtx", object)


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, here / (name + "_author.py"))
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


fig, axs = plt.subplots(1, 3, figsize=(15, 8))
BIS, PINK, JAM, INK, CHEEK, EMB = ("#dcc088", "#f0b0a4", "#dc5060", "#111",
                                   "#eb8296", "#c09a58")


def poly(ax, pts, c, z=1.0):
    ax.add_patch(Polygon(pts, closed=True, fc=c, ec="k", lw=0.3, zorder=z))


def circ(ax, x, y, r, c, z=3.0):
    ax.add_patch(Circle((x, y), r, fc=c, ec="k", lw=0.3, zorder=z))


j = load("jammie")
ax = axs[0]
poly(ax, j.jm_outline(0), BIS)
circ(ax, 0, 0, j.JM_RING[1], EMB, 1.5)
circ(ax, 0, 0, j.JM_RING[0], BIS, 1.6)
poly(ax, j.jm_heart(*j.JM_HEART), JAM, 2)
arms, dots = j.jm_splat()
for a in arms:
    poly(ax, a, EMB, 2)
for (x, y, r) in dots:
    circ(ax, x, y, r, EMB, 2)
print("jammie arms", len(arms), "dots", len(dots))
poly(ax, j.smile(0, 13.5, 6.0, 1.3), INK, 3)
for sx in (1, -1):
    circ(ax, sx * 7.5, 14.5, 1.2, INK)
    circ(ax, sx * 14.5, 9.0, 2.5, CHEEK)
    circ(ax, sx * 9, -30, 3.25, "w")

w = load("wafer")
ax = axs[1]
poly(ax, [(-17.5, -37.5), (17.5, -37.5), (17.5, 37.5), (-17.5, 37.5)], PINK)
for s in (1, -1):
    for p in w.wf_lattice(s):
        poly(ax, p, "#e89488", 2)
poly(ax, w.smile(0, 4.0, 4.6, 1.2), INK, 3)
for sx in (1, -1):
    circ(ax, sx * 6, 5, 1.1, INK)
    circ(ax, sx * 11.5, 1.5, 2.0, CHEEK)
    circ(ax, sx * 8, -37.5, 3.25, "w")

c = load("custard")
ax = axs[2]
poly(ax, [(-22.5, -30), (22.5, -30), (22.5, 30), (-22.5, 30)], BIS)
poly(ax, [(-21, -28.5), (21, -28.5), (21, 28.5), (-21, 28.5)], "#e2c890", 1.1)
fr = c.cc_frame()
poly(ax, fr[0], EMB, 2)
poly(ax, fr[1], "#e2c890", 2.1)
for nm in ("cc_big_spirals", "cc_top_spirals", "cc_side_spirals",
           "cc_tendrils"):
    ps = getattr(c, nm)()
    print(nm, "lines", sum(len(q) for q in ps))
    for q in ps:
        poly(ax, q, EMB, 2.2)
for (x, y, r) in c.cc_dots():
    circ(ax, x, y, r, EMB, 2.2)
poly(ax, c.smile(0, 2.5, 4.2, 1.2), INK, 3)
for sx in (1, -1):
    circ(ax, sx * 4, 3.5, 1.1, INK)
    circ(ax, sx * 10, -30, 3.25, "w")

for ax in axs:
    ax.set_aspect("equal")
    ax.set_xlim(-34, 34)
    ax.set_ylim(-40, 40)
    ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(here / "art_preview.png", dpi=80)
print("saved")
