"""Offline 2D preview of the fixed art (no Fusion needed)."""
import importlib.util
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

here = Path(__file__).parent

import sys
import types
for _n in ("adsk", "adsk.core", "adsk.fusion", "fusionhelper",
           "fusionhelper.buildkit"):
    sys.modules[_n] = types.ModuleType(_n)
sys.modules["fusionhelper.buildkit"].BuildCtx = object


def load(name):
    spec = importlib.util.spec_from_file_location(name, here / (name + "_author.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


fig, axs = plt.subplots(1, 3, figsize=(15, 8))
BIS, PINK, JAM, INK, BROWN, CHEEK = "#dcc088", "#f0b0a4", "#dc5060", "#111", "#5a3220", "#eb8296"


def poly(ax, pts, c, z=1):
    ax.add_patch(Polygon(pts, closed=True, fc=c, ec="k", lw=0.3, zorder=z))


def circ(ax, x, y, r, c, z=3):
    ax.add_patch(Circle((x, y), r, fc=c, ec="k", lw=0.3, zorder=z))


j = load("jammie")
ax = axs[0]
poly(ax, j.jm_outline(0), BIS)
poly(ax, j.jm_heart(0.68, -5.0), JAM, 2)
poly(ax, j.smile(0, 13.5, 6.0, 1.3), INK, 3)
for sx in (1, -1):
    circ(ax, sx * 7.5, 14.5, 1.2, INK)
    circ(ax, sx * 14.5, 9.0, 2.5, CHEEK)
    circ(ax, sx * 9, -30, 3.25, "w")

w = load("wafer")
ax = axs[1]
poly(ax, [(-17.5, -37.5), (17.5, -37.5), (17.5, 37.5), (-17.5, 37.5)], PINK)
n = 0
for s in (1, -1):
    for p in w.wf_lattice(s):
        poly(ax, p, "#e89488", 2)
        n += len(p)
print("wafer lattice lines", n, "polys", len(w.wf_lattice(1)), len(w.wf_lattice(-1)))
poly(ax, w.smile(0, 4.0, 4.6, 1.2), INK, 3)
for sx in (1, -1):
    circ(ax, sx * 6, 5, 1.1, INK)
    circ(ax, sx * 11.5, 1.5, 2.0, CHEEK)
    circ(ax, sx * 8, -37.5, 3.25, "w")

c = load("custard")
ax = axs[2]
poly(ax, [(-22.5, -30), (22.5, -30), (22.5, 30), (-22.5, 30)], BIS)
poly(ax, [(9, 0), (0, 13), (-9, 0), (0, -13)], "#e6cc98", 2)
nb = sum(len(p) for p in c.cc_brackets())
nc = sum(len(p) for p in c.cc_curls())
print("custard lines brackets", nb, "curls", nc)
for p in c.cc_brackets() + c.cc_curls():
    poly(ax, p, BROWN, 2)
poly(ax, c.smile(0, 1.5, 3.2, 1.0), INK, 3)
for sx in (1, -1):
    circ(ax, sx * 3, 2.6, 0.9, INK)
    circ(ax, sx * 10, -30, 3.25, "w")

for ax in axs:
    ax.set_aspect("equal")
    ax.set_xlim(-34, 34)
    ax.set_ylim(-40, 40)
    ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(here / "art_preview.png", dpi=80)
print("saved")
