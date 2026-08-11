"""ORRERY mk3 rev 4 - planets on BOTH faces of the ring.

Five coaxial gear stages, every one standing on the build plate:

    housing (75T internal, the part you hold)
      -> 5 outer planets (10T)
        -> ring: 55T external / 40T internal  <- the flywheel
          -> 5 inner planets (10T)
            -> sun (20T, a FREE idler)

Letting the sun float is what makes this printable. A fixed sun would
have to be joined to the housing, and any such bridge has to cross the
rotating ring - impossible below the ring, and a 27 mm span above it.
Free, the sun is still captive: it is trapped by the inner planets,
which are trapped by the ring, which is trapped by the outer planets.
Nothing needs a post, a carrier or an axle.

Retention (rev 6) is a MID-HEIGHT SQUARE-SHOULDERED GROOVE: rev 5's
V-way, which held perfectly in the hand, with the flanks flattened.

END retention was tried twice and failed twice in the hand. Rev 3 used
45 deg ramps, which cam: a 45 deg face converts axial load one-for-one
into radial load, so the flange was driven out of its own capture.
Rev 4 replaced them with square shoulders, camming ratio zero - and the
assembly still came apart, because a square shoulder at the END of a
part only has to lose contact ONCE, and nothing stops the planet
drifting radially far enough to clear it. Both failures share a root
cause: an end feature restrains the planet on one side only.

The V-way removes that. Each planet carries one full-circle V-groove
around its tip at mid-height; each mating gear carries a matching
V-ridge that fills its own tooth spaces out into that groove. So each
planet is gripped from BOTH sides at once - sun and ring for the inner
stage, ring and housing for the outer. The flanks are 45 deg and they
do cam, but now the camming has nowhere to go: to ride out of the sun's
ridge the planet must move radially outward, which drives it harder
onto the ring's ridge. The sun, ring and housing are each held by five
planets in a full circular pattern, so their radial forces cancel by
symmetry. Nothing in the train can escape without every other part
moving with it.

This is the same reason the Supernova journal works: the column is
trapped in its bore, so its 45 deg diamond ridge cannot cam out.

  - planet groove: a 3.0 mm tall channel, 1.5 mm deep into the tip,
    centred on z 7.25, with HORIZONTAL top and bottom faces;
  - gear ridge: 2.5 mm tall, apex 0.25 mm radially clear of the groove
    floor, base sunk 0.15 mm past that gear's own ROOT so the revolve
    joins solid and the ridge fills the tooth spaces;
  - axial float 0.25 mm each way; radial running clearance 0.25 mm.

Rev 5 shipped 45 deg flanks and DID hold - held horizontally it no
longer came apart. But it would not spin in that orientation, and the
reason was the flank angle. Held flat, the whole 36.6 g of ring +
planets + sun hangs on these faces, and a 45 deg face converts that
weight into a radial wedge: 0.51 N of contact load to carry 0.36 N of
weight, squeezing each planet into both of its meshes at once. Measured
coast-down was 0.09 s flat against 3.2 s vertical. Flattening the
flanks makes the contact normal vertical, so the wedge disappears and
the contact load is just the weight.

Worth being honest about the ceiling: this buys roughly 5x, not 30x.
The load still rides on sliding plastic at 27-37 mm radius, where a
normal spinner uses a ball race at ~4 mm. Flat spin lands near half a
second; the design remains, by its geometry, an edge-on spinner.

Deleting the end features pays a second dividend: every body is now a
plain full-height gear with teeth from z0 to z14.5, so the mesh face
width goes from 4.5 mm to about 12.7 mm, and the only overhangs left
in the whole model are the 45 deg V flanks themselves.

Mesh (rev 2): 25 deg pressure angle, backlash 0.20 mm, tips shortened
(sun 10.95, ring-int 19.25, ring-ext 28.40, housing 36.70). At 20 deg
the 10T planets put their roots 0.95 mm below the base circle and every
mating tip swept through that zone - a measured, systematic 8.2 mm3 of
tip interference per planet that mid-band retention was wrongly blamed
for. At 25 deg with these tips every mesh clears its interference limit
by 0.10-0.19 mm on the line of action, contact ratios 1.31-1.43, and
the 10T tip land stays ~0.16 mm (25 deg + backlash sharpens low-count
tips; 0.35 mm backlash would make them pointed).

Every stage is a cylinder at its tip radius with ONE tooth space cut and
patterned - about ten API calls per gear instead of several hundred.
Flanks use 5 samples: 3 left the spaces measurably narrow.

Raised top decor (rev 3): procedural engraved scrollwork, styled on
hand-engraved wheel rims (log-spiral curls with flowing tapered tails,
nested counter-curls and teardrop leaves). Sun carries a 5-scroll
rosette, ring and housing carry S-flowing scroll bands (8 and 10
repeats), every planet flange a 3-scroll triskelion. All fields are
full n-fold circular patterns so balance is free. 0.8 mm tall,
extruded straight up from z14.5; every polygon validated offline as
simple (non-self-intersecting) and numerically confined to its own
part's top face, so there are no new overhangs and no swept-annulus
overlap between neighbouring rotating parts.

All 13 bodies are then packaged into one component (orrery_mk3_90) for
easy export selection.

Idempotent: each stage skips when its output already exists, so a re-run
after a timed-out MCP request is a clean no-op.
"""
import math
import time

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {"liveness": False}
INTERFERENCE_ALLOWED = []

# The decor is cosmetic but costs ~90% of the build (24 sketches joined
# onto bodies whose tooth spaces the V-ridges have already subdivided).
# Set False to validate the MECHANISM in seconds: same gears, same
# V-way, no scrollwork. Always rebuild with it True before exporting.
BUILD_DECOR = True

PANG = math.radians(25)
BACKLASH = 0.020
H = 1.45                       # full stack; every body spans z0..H
ZM = H / 2.0                   # V-way mid-height, z 7.25 mm
GRV_H = 0.15                   # groove half-height: a 3.0 mm tall channel
AX_F = 0.025                   # axial float each way (0.25 mm)
GRV_D = 0.15                   # groove depth into the planet tip (1.5 mm)
#   Sized by a rotational-phase sweep, not by eye. The groove is ten
#   tooth-tip notches, so engagement breathes as the teeth turn: it is
#   deepest with a tooth facing the gear and shallowest with a space
#   facing it. At 0.9 mm the worst phase left the SUN only 0.205 mm of
#   engagement - less than the planet's own radial slack, so a planet
#   could shrug the sun's ridge off at that phase, and the sun is held
#   by nothing else. 1.5 mm puts the worst phase at 0.805 mm. Floor
#   lands at planet r 4.5 mm, still 0.75 mm clear of the 3.75 root.
GRV_OC = 0.03                  # overcut past the tip so the cut is clean
VCLR = 0.025                   # radial clearance -> 0.177 mm normal at 45 deg
#                                PRINT-PROVEN (Supernova 72 rev B journal)
RIDGE_FOOT = 0.015             # ridge base sunk past the gear's own root

SUN = dict(N=20, rp=1.00, tip=1.095, root=0.875, internal=False)
PLI = dict(N=10, rp=0.50, tip=0.60, root=0.375, internal=False)
RGI = dict(N=40, rp=2.00, tip=1.925, root=2.125, internal=True)
RGE = dict(N=55, rp=2.75, tip=2.840, root=2.625, internal=False)
PLO = dict(N=10, rp=0.50, tip=0.60, root=0.375, internal=False)
HSG = dict(N=75, rp=3.75, tip=3.670, root=3.875, internal=True)
ST_IN, ST_OUT = 1.50, 3.25
HOUSE_OUT = 4.50
N_PL = 5


def groove_rz():
    """The planet's mid-height groove, as a revolve-CUT profile (r, z).

    RECTANGULAR, not a V. The 45 deg V retained perfectly but would not
    let the toy spin held flat: with the axis vertical the whole 36.6 g
    of ring + planets + sun hangs on these flanks, and a 45 deg flank
    turns that weight into a radial wedge - 0.51 N of contact load to
    carry 0.36 N of weight, squeezing the planet into both of its meshes
    at the same time. Measured coast-down was 0.09 s flat against 3.2 s
    vertical. Horizontal faces make the contact normal vertical, so the
    wedge disappears and the load is just the weight."""
    rb = PLI["tip"] - GRV_D
    ro = PLI["tip"] + GRV_OC
    return [(ro, ZM - GRV_H), (rb, ZM - GRV_H),
            (rb, ZM + GRV_H), (ro, ZM + GRV_H)]


def ridge_rz(g, station, inboard):
    """The mating gear's ridge, as a revolve-JOIN profile in (r, z).

    Also rectangular, so both bearing faces are horizontal. Its apex
    sits VCLR radially clear of the groove floor; the base is sunk
    RIDGE_FOOT past the gear's own ROOT, which does two things: the
    revolve lands on solid material, and the ridge fills the gear's
    tooth spaces out to the apex, which is what the planet's grooved
    teeth actually run against.

    The ridge's underside is now a horizontal overhang - but it is only
    unsupported ACROSS a tooth space (~1.7 mm) and is anchored at both
    ends by the teeth it grows from, so it bridges rather than
    cantilevers. Returns (profile, apex_radius)."""
    s = 1.0 if inboard else -1.0
    apex = station - s * (PLI["tip"] - GRV_D + VCLR)
    base = g["root"] - s * RIDGE_FOOT
    hr = GRV_H - AX_F
    return ([(base, ZM - hr), (apex, ZM - hr),
             (apex, ZM + hr), (base, ZM + hr)], apex)


# ---- engraved-scrollwork generator (pure math, cm) --------------------
# Tuned offline against reference images of hand-engraved wheel rims;
# every polygon is verified simple and extent-checked in scroll_gen.py
# before landing here. Strokes taper to points; widths are clamped to
# the local spiral radius so an inner whorl can never swallow itself.

def _dstrip(pw, pointed=False):
    n = len(pw)
    left, right = [], []
    for i, (x, y, w) in enumerate(pw):
        h = w / 2.0
        if i == 0:
            dx, dy = pw[1][0] - x, pw[1][1] - y
        elif i == n - 1:
            dx, dy = x - pw[-2][0], y - pw[-2][1]
        else:
            dx, dy = pw[i + 1][0] - pw[i - 1][0], \
                pw[i + 1][1] - pw[i - 1][1]
        m = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / m, dx / m
        left.append((x + nx * h, y + ny * h))
        right.append((x - nx * h, y - ny * h))
    if pointed:
        return left[:-1] + [(pw[-1][0], pw[-1][1])] + right[-2::-1]
    return left + right[::-1]


def dec_curl(cx, cy, r0, a0, turns, handed, w0, decay=0.20, n=16):
    pw = []
    for i in range(n + 1):
        t = i / float(n)
        rho = r0 * (decay ** t)
        a = a0 + handed * 2 * math.pi * turns * t
        w = min(w0 * (1.0 - 0.92 * t), 1.5 * rho)
        pw.append((cx + rho * math.cos(a), cy + rho * math.sin(a),
                   max(0.012, w)))
    return _dstrip(pw, pointed=True)


def dec_scroll(tail0, lead, cx, cy, r0, a0, turns, handed, w_tail, w0,
               decay=0.22, n_tail=6, n_sp=14):
    def sp(t):
        rho = r0 * (decay ** t)
        a = a0 + handed * 2 * math.pi * turns * t
        return (cx + rho * math.cos(a), cy + rho * math.sin(a))

    sx, sy = sp(0.0)
    ex, ey = sp(0.01)
    m = math.hypot(ex - sx, ey - sy) or 1.0
    tcx = sx - lead * (ex - sx) / m
    tcy = sy - lead * (ey - sy) / m
    pw = []
    for i in range(n_tail):
        t = i / float(n_tail)
        x = (1 - t) ** 2 * tail0[0] + 2 * (1 - t) * t * tcx + t * t * sx
        y = (1 - t) ** 2 * tail0[1] + 2 * (1 - t) * t * tcy + t * t * sy
        pw.append((x, y, w_tail + (w0 - w_tail) * t))
    for i in range(n_sp + 1):
        t = i / float(n_sp)
        rho = r0 * (decay ** t)
        x, y = sp(t)
        w = min(w0 * (1.0 - 0.92 * t), 1.5 * rho)
        pw.append((x, y, max(0.012, w)))
    return _dstrip(pw, pointed=True)


def dec_leaf(cx, cy, ln, ang, w):
    top, bot = [], []
    for i in range(1, 8):
        t = i / 8.0
        a = math.pi * t
        px = ln * (1 - math.cos(a)) / 2.0
        py = w * math.sin(a) * (1 - 0.55 * t)
        top.append((px, py))
        bot.append((px, -py))
    pts = [(0.0, 0.0)] + top + [(ln, 0.0)] + bot[::-1]
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def _shoelace(poly):
    """Polygon area, for the stroke-profile filter (see decor())."""
    s = 0.0
    j = len(poly) - 1
    for i in range(len(poly)):
        s += poly[j][0] * poly[i][1] - poly[i][0] * poly[j][1]
        j = i
    return abs(s) / 2.0


def _pip(x, y, poly):
    """Even-odd point-in-polygon, for the stroke-profile filter.

    Why a HYBRID filter: extruding every profile of a decor sketch fills
    the curl EYES solid (each enclosed void is its own Fusion profile -
    user-observed blobs). Discriminating stroke from eye needs both
    tests: an unbroken C-shaped strip matches its polygon's shoelace
    AREA but its centroid lies in its own eye; a fragment produced by
    OVERLAPPING strokes (sun tails piercing the centre boss) matches no
    polygon's area but its centroid is covered by a stroke polygon. An
    eye fails both."""
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            if x < xi + (y - yi) / (yj - yi) * (xj - xi):
                inside = not inside
        j = i
    return inside


def dec_band(polys_uv, r_mid, th0, vscale):
    out = []
    for p in polys_uv:
        q = []
        for u, v in p:
            th = th0 + u / r_mid
            q.append(((r_mid + v * vscale) * math.cos(th),
                      (r_mid + v * vscale) * math.sin(th)))
        out.append(q)
    return out


def dec_housing_unit():
    polys = [dec_scroll((0.02, -0.16), 0.55, 0.72, 0.04, 0.21,
                        math.radians(-100), 1.5, 1, 0.05, 0.13),
             dec_scroll((1.06, 0.17), 0.52, 1.98, -0.04, 0.195,
                        math.radians(82), 1.5, -1, 0.05, 0.125),
             dec_curl(1.06, -0.115, 0.095, math.radians(115), 1.15, -1,
                      0.058),
             dec_curl(2.32, 0.105, 0.082, math.radians(-65), 1.10, 1,
                      0.050),
             dec_leaf(1.20, -0.135, 0.52, math.radians(-6), 0.085),
             dec_leaf(2.46, 0.115, 0.42, math.radians(174), 0.075)]
    return polys


def dec_ring_unit():
    polys = [dec_scroll((0.02, -0.085), 0.34, 0.50, 0.015, 0.115,
                        math.radians(-100), 1.4, 1, 0.04, 0.082),
             dec_scroll((0.70, 0.095), 0.32, 1.38, -0.02, 0.105,
                        math.radians(80), 1.4, -1, 0.04, 0.078),
             dec_curl(0.72, -0.072, 0.052, math.radians(105), 1.0, -1,
                      0.042),
             dec_leaf(0.90, -0.088, 0.36, math.radians(-4), 0.058)]
    return polys


def dec_sun_polys():
    # 5 DISJOINT scrolls + boss, no leaves: overlapping strokes here
    # formed a closed ring whose enclosed centre read as one filled
    # plateau (user-observed). Disjointness is validated offline in
    # scroll_gen.py (pairwise segment intersection); with every stroke
    # disjoint and every curl open, the sketch has exactly one profile
    # per polygon and nothing to mis-classify.
    polys = []
    for k in range(5):
        a = 2 * math.pi * k / 5
        ca, sa = math.cos(a), math.sin(a)
        p = dec_scroll((0.135, -0.045), 0.24, 0.50, 0.07, 0.225,
                       math.radians(-70), 1.1, 1, 0.05, 0.10,
                       decay=0.26)
        polys.append([(x * ca - y * sa, x * sa + y * ca)
                      for x, y in p])
    polys.append([(0.10 * math.cos(2 * math.pi * i / 12),
                   0.10 * math.sin(2 * math.pi * i / 12))
                  for i in range(12)])
    return polys


def dec_planet_polys(st, ang):
    cx, cy = st * math.cos(ang), st * math.sin(ang)
    polys = []
    for k in range(3):
        a = 2 * math.pi * k / 3
        ca, sa = math.cos(a), math.sin(a)
        # 0.95 turns and open decay: at curl diameter 3 mm a stroke can
        # never face its own next whorl below one full turn — 1.35 turns
        # with 0.75 mm strokes merged into blobs (user-observed)
        base = dec_scroll((0.015, -0.02), 0.10, 0.145, 0.03, 0.15,
                          math.radians(-95), 0.95, 1, 0.028, 0.062,
                          decay=0.30)
        polys.append([(cx + x * ca - y * sa, cy + x * sa + y * ca)
                      for x, y in base])
    return polys


def _inv(a):
    return math.tan(a) - a


def _psi(g, r):
    rb = g["rp"] * math.cos(PANG)
    ap = math.acos(min(1.0, rb / g["rp"]))
    ar = math.acos(min(1.0, rb / max(r, rb)))
    p = math.pi / (2 * g["N"]) - BACKLASH / (2 * g["rp"])
    return p - _inv(ap) + _inv(ar) if g["internal"] else \
        p + _inv(ap) - _inv(ar)


def space(g, phase=0.0):
    half = math.pi / g["N"]
    lo, hi = (g["tip"], g["root"]) if g["internal"] else (g["root"], g["tip"])
    rs = [lo + (hi - lo) * i / 4.0 for i in range(5)]
    pts = []
    for r in rs:
        a = phase + half - _psi(g, r)
        pts.append((r * math.cos(a), r * math.sin(a)))
    if not g["internal"]:
        # Close the space mouth OUTSIDE the tip circle. A straight chord
        # between the two tip points leaves an uncut crescent inside the
        # tip arc (sagitta 0.29 mm on the 10T planets) that the mating
        # tooth sweeps through - measured 1.22 mm2 per mesh, the actual
        # source of the ~8-9 mm3 "involute" interference. Internal gears
        # need nothing: their mouth chord dips into air and their root
        # chord sagitta is < 2 um at N=40/75.
        ov = g["tip"] + 0.08
        a1 = phase + half - _psi(g, g["tip"])
        a2 = phase - (half - _psi(g, g["tip"]))
        pts.append((ov * math.cos(a1), ov * math.sin(a1)))
        pts.append((ov * math.cos(a2), ov * math.sin(a2)))
    for r in reversed(rs):
        a = phase - (half - _psi(g, r))
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def _fix(sk):
    for c in sk.sketchCurves:
        if not c.isFixed:
            c.isFixed = True
    for sp in sk.sketchPoints:
        if not (sp.isFullyConstrained or sp.isFixed):
            sp.isFixed = True
    adsk.doEvents()


def _poly(sk, pt, pts, z):
    sp = [sk.modelToSketchSpace(pt(x, y, z)) for x, y in pts]
    ln = sk.sketchCurves.sketchLines
    first = ln.addByTwoPoints(sp[0], sp[1])
    prev = first
    for i in range(2, len(sp)):
        prev = ln.addByTwoPoints(prev.endSketchPoint, sp[i])
    ln.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _poly_rz(sk, pt, rz):
    sp = [sk.modelToSketchSpace(pt(r, 0, z)) for r, z in rz]
    ln = sk.sketchCurves.sketchLines
    first = ln.addByTwoPoints(sp[0], sp[1])
    prev = first
    for i in range(2, len(sp)):
        prev = ln.addByTwoPoints(prev.endSketchPoint, sp[i])
    ln.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    adsk.doEvents()


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs
    rev = root.features.revolveFeatures
    cpats = root.features.circularPatternFeatures
    popts = adsk.fusion.PatternComputeOptions
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    for nm, val, d in (("o3_h", "14.5 mm", "full stack height"),
                       ("o3_dec_h", "0.8 mm", "raised top decor height")):
        adsk.doEvents()
        if up.itemByName(nm) is None:
            up.add(nm, cbs(val), "mm", d)

    def find_body(name):
        b = root.bRepBodies.itemByName(name)
        if b is not None:
            return b
        occs = root.allOccurrences
        for i in range(occs.count):
            b = occs.item(i).bRepBodies.itemByName(name)
            if b is not None:
                return b
        return None

    def bodies_by_prefix(pref):
        out = []
        for b in root.bRepBodies:
            if b.name.startswith(pref):
                out.append(b)
        occs = root.allOccurrences
        for i in range(occs.count):
            for b in occs.item(i).bRepBodies:
                if b.name.startswith(pref):
                    out.append(b)
        return out

    def revolve_body(name, rz):
        sk = root.sketches.add(root.xZConstructionPlane)
        sk.name = name + "_profile"
        _poly_rz(sk, pt, rz)
        _fix(sk)
        if sk.profiles.count != 1:
            raise RuntimeError("%s profiles %d" % (name, sk.profiles.count))
        rin = rev.createInput(sk.profiles.item(0), root.zConstructionAxis,
                              ctx.ops.NewBodyFeatureOperation)
        rin.setAngleExtent(False, cbs("360 deg"))
        f = rev.add(rin)
        f.name = name + "_revolve"
        b = f.bodies.item(0)
        b.name = name
        return b

    def cut_teeth(body, g, name, phase=0.0):
        sk = root.sketches.add(root.xYConstructionPlane)
        sk.name = name + "_space"
        _poly(sk, pt, space(g, phase), 0.0)
        _fix(sk)
        fc = ctx.blind_cut(ctx.all_profiles(sk), "o3_h", [body],
                           name, min_vol_cm3=0.0004)
        fc.name = name + "_cut"
        v0 = body.volume
        coll = adsk.core.ObjectCollection.create()
        coll.add(fc)
        pin = cpats.createInput(coll, root.zConstructionAxis)
        pin.quantity = cbs(str(g["N"]))
        pin.totalAngle = cbs("360 deg")
        pin.isSymmetric = False
        pin.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
        pf = cpats.add(pin)
        if pf.healthState not in healthy or v0 - body.volume < 0.02:
            raise RuntimeError("%s pattern dv=%.4f" % (name,
                                                       v0 - body.volume))
        pf.name = name + "_pattern"

    def find_feature(name):
        # Two traps, both measured: a feature whose participants live
        # inside a component lands in THAT component's collection, not
        # root's; and revolves and extrudes are separate collections, so
        # a guard that only searches one silently re-runs its stage.
        for holder in [root] + [root.allOccurrences.item(i).component
                                for i in range(root.allOccurrences.count)]:
            for coll in (holder.features.extrudeFeatures,
                         holder.features.revolveFeatures):
                f = coll.itemByName(name)
                if f is not None:
                    return f
        return None

    def gear(name, rz, cuts):
        b = find_body(name)
        if b is not None:
            print("FH skip %s (exists)" % name)
            return b
        b = revolve_body(name, rz)
        for g, cname, ph in cuts:
            adsk.doEvents()
            cut_teeth(b, g, cname, ph)
        return b

    def add_ridge(body, g, station, inboard, name):
        """Revolve-join the V-ridge. Must run AFTER the teeth are cut:
        the ridge's job is to fill the tooth spaces at mid-height, out
        to where the planet's grooved teeth run."""
        if find_feature(name + "_revolve") is not None:
            print("FH skip %s (exists)" % name)
            return
        stale = root.sketches.itemByName(name)
        if stale is not None:      # sketch committed, revolve did not
            stale.deleteMe()
        prof, apex = ridge_rz(g, station, inboard)
        lo, hi = sorted((g["tip"], g["root"]))
        if not lo < apex < hi:
            raise RuntimeError("%s apex %.3f outside tip/root %.3f..%.3f"
                               % (name, apex, lo, hi))
        sk = root.sketches.add(root.xZConstructionPlane)
        sk.name = name
        _poly_rz(sk, pt, prof)
        _fix(sk)
        if sk.profiles.count != 1:
            raise RuntimeError("%s profiles %d" % (name, sk.profiles.count))
        v0 = body.volume
        rin = rev.createInput(sk.profiles.item(0), root.zConstructionAxis,
                              ctx.ops.JoinFeatureOperation)
        rin.setAngleExtent(False, cbs("360 deg"))
        rin.participantBodies = [body]
        rev.add(rin).name = name + "_revolve"
        dv = body.volume - v0
        if dv < 0.004:
            raise RuntimeError("%s added %.4f cm3" % (name, dv))
        print("FH %s ridge apex %.2f mm (root %.2f, tip %.2f) +%.3f cm3"
              % (name, apex * 10, g["root"] * 10, g["tip"] * 10, dv))

    # Bodies are plain full-height gears now - the V-way carries all the
    # retention, so there are no end recesses and the teeth run z0..H.
    # ---- sun: free idler ---------------------------------------------
    sun = gear("o3_sun", [
        (0.0, 0.0), (SUN["tip"], 0.0), (SUN["tip"], H), (0.0, H)],
        [(SUN, "sun_tooth", 0.0)])
    print("FH sun %.3f cm3" % sun.volume)

    # ---- ring: teeth on both faces -----------------------------------
    ring = gear("o3_ring", [
        (RGI["tip"], 0.0), (RGE["tip"], 0.0),
        (RGE["tip"], H), (RGI["tip"], H)],
        [(RGI, "ring_int", 0.0), (RGE, "ring_ext", 0.0)])
    print("FH ring %.3f cm3" % ring.volume)

    # ---- housing: the part you hold ----------------------------------
    house = gear("o3_housing", [
        (HSG["tip"], 0.0), (HOUSE_OUT, 0.0),
        (HOUSE_OUT, H), (HSG["tip"], H)],
        [(HSG, "house_tooth", 0.0)])
    print("FH housing %.3f cm3" % house.volume)

    # NOTE: the four add_ridge() calls deliberately run LAST, after all
    # the decor - see the call site below group_component's definition.

    # ---- planets: built at origin, then translated out ---------------
    def planet(g, station, name):
        # the circular pattern renames the seed too, so bodies end up
        # name_2..name_6 â€” guard on the survivor count, not on name_1
        if len(bodies_by_prefix(name)) >= N_PL:
            print("FH skip %s (exists)" % name)
            return
        sk = root.sketches.add(root.xYConstructionPlane)
        sk.name = name + "_disc"
        ctx.bound_circle(sk, (0, 0, 0), g["tip"], "12 mm",
                         x_pos="0 mm", v_pos="0 mm")

        def ok(b):
            return 1.3 < b.volume < 2.0

        f, body = ctx.checked_newbody(ctx.all_profiles(sk), "o3_h",
                                      ok, name)
        f.name = name + "_extrude"
        body.name = name + "_1"
        cut_teeth(body, g, name + "_tooth", phase=math.pi / g["N"])

        # One V-groove serves both mates: the inboard gear's ridge and
        # the outboard gear's ridge enter the same groove from opposite
        # sides, which is exactly what makes the planet inescapable.
        # Cut AFTER the teeth so it notches the tooth tips.
        adsk.doEvents()
        gname = name + "_vway"
        skb = root.sketches.add(root.xZConstructionPlane)
        skb.name = gname
        _poly_rz(skb, pt, groove_rz())
        _fix(skb)
        if skb.profiles.count != 1:
            raise RuntimeError("%s profiles %d" % (gname,
                                                   skb.profiles.count))
        vb = body.volume
        cin = rev.createInput(skb.profiles.item(0),
                              root.zConstructionAxis,
                              ctx.ops.CutFeatureOperation)
        cin.setAngleExtent(False, cbs("360 deg"))
        cin.participantBodies = [body]
        rev.add(cin).name = gname + "_revolve"
        # ~4.7 mm3 measured: at 25 deg PA a 10T tooth is nearly pointed
        # at the tip, so the groove is ten tip notches, not a channel.
        # That is fine - the notches bear on the mating gear's ridge,
        # which IS a continuous annulus, and the load is a 1.5 g planet.
        dv = vb - body.volume
        if dv < 0.003:
            raise RuntimeError("%s removed %.4f cm3" % (gname, dv))
        print("FH %s groove floor %.2f mm -%.3f cm3"
              % (name, (g["tip"] - GRV_D) * 10, dv))

        mv = adsk.core.ObjectCollection.create()
        mv.add(body)
        mi = root.features.moveFeatures.createInput2(mv)
        mi.defineAsTranslateXYZ(cbs("%.4f mm" % (station * 10)),
                                cbs("0 mm"), cbs("0 mm"), True)
        root.features.moveFeatures.add(mi).name = name + "_to_station"

        before = root.bRepBodies.count
        bc = adsk.core.ObjectCollection.create()
        bc.add(body)
        pin = cpats.createInput(bc, root.zConstructionAxis)
        pin.quantity = cbs(str(N_PL))
        pin.totalAngle = cbs("360 deg")
        pin.isSymmetric = False
        pf = cpats.add(pin)
        if (pf.healthState not in healthy
                or root.bRepBodies.count - before != N_PL - 1):
            raise RuntimeError("%s pattern added %d"
                               % (name, root.bRepBodies.count - before))
        pf.name = name + "_pattern"
        for i in range(pf.bodies.count):
            pf.bodies.item(i).name = "%s_%d" % (name, i + 2)
        print("FH %s %.3f cm3 at r%.1f" % (name, body.volume, station * 10))

    planet(PLI, ST_IN, "o3_pl_in")
    planet(PLO, ST_OUT, "o3_pl_out")

    # ---- raised top decor: engraved scrollwork, 0.8 mm up ------------
    dec_state = {"plane": None}

    def dec_plane():
        if dec_state["plane"] is None:
            pl = root.constructionPlanes.itemByName("o3_dec_plane")
            if pl is None:
                pl = ctx.plane_at_z("o3_h", "o3_dec_plane")
            dec_state["plane"] = pl
        return dec_state["plane"]

    def join_up(profs, participants, kind, min_vol):
        v0 = sum(b.volume for b in participants)
        for d in (ctx.dirs.PositiveExtentDirection,
                  ctx.dirs.NegativeExtentDirection):
            adsk.doEvents()
            inp = ctx.extrudes.createInput(profs,
                                           ctx.ops.JoinFeatureOperation)
            ext = adsk.fusion.DistanceExtentDefinition.create(
                cbs("o3_dec_h"))
            inp.setOneSideExtent(ext, d)
            inp.participantBodies = participants
            f = ctx.extrudes.add(inp)
            if sum(b.volume for b in participants) - v0 > min_vol:
                f.name = kind + "_join"
                return f
            f.deleteMe()
        raise RuntimeError("%s joined nothing" % kind)

    def decor(sk_name, polys, participants, min_vol):
        # guard on the JOIN, not the sketch: a dead client can commit
        # the sketch and die before the join, and a sketch-based guard
        # would then silently skip the decor forever. The join gets a
        # "_join" suffix - sketches and features share one name
        # namespace, and an extrude named like its sketch is silently
        # auto-suffixed to "name (1)", which a guard then misses.
        if find_feature(sk_name + "_join") is not None:
            print("FH skip %s (exists)" % sk_name)
            return
        t_start = time.time()
        counts = [len(p) for p in polys]
        total = sum(counts)
        sk = root.sketches.itemByName(sk_name)
        if sk is None:
            sk = root.sketches.add(dec_plane())
            sk.name = sk_name
        have = sk.sketchCurves.count
        if have != total:
            # resume a dead client's partial sketch at the first undrawn
            # polygon. NEVER delete a big sketch to start over: deleting
            # ~1200 fixed curves measured ~20 minutes of frozen UI â€”
            # deletion, not creation, is the pathological operation.
            start = None
            acc = 0
            for idx, c in enumerate(counts):
                if acc == have:
                    start = idx
                    break
                acc += c
            if start is None:
                raise RuntimeError(
                    "%s unresumable: %d lines is not a polygon-boundary "
                    "prefix of %d" % (sk_name, have, total))
            # deferred compute: per-line solves on a several-thousand-
            # entity sketch are O(n^2) and blew a 2-minute client timeout
            sk.isComputeDeferred = True
            for p in polys[start:]:
                adsk.doEvents()
                _poly(sk, pt, p, H)
        sk.isComputeDeferred = True
        _fix(sk)
        sk.isComputeDeferred = False
        adsk.doEvents()
        areas = [_shoelace(p) for p in polys]
        profs = adsk.core.ObjectCollection.create()
        dropped = 0
        for prof in sk.profiles:  # fusionhelper: allow R11 — profile filter, not a document mutation
            ap = prof.areaProperties()
            keep = any(abs(ap.area - ea) <= 0.03 * ea + 1e-5
                       for ea in areas)
            if not keep:
                c = sk.sketchToModelSpace(ap.centroid)
                keep = any(_pip(c.x, c.y, p) for p in polys)
            if keep:
                profs.add(prof)
            else:
                dropped += 1
        if profs.count == 0:
            raise RuntimeError("%s: no stroke profiles found" % sk_name)
        join_up(profs, participants, sk_name, min_vol)
        print("FH %s: %d strokes, %d dropped, %.1f s"
              % (sk_name, profs.count, dropped, time.time() - t_start))

    if not BUILD_DECOR:
        print("FH decor SKIPPED (BUILD_DECOR False) - mechanism only")

    if BUILD_DECOR:
        decor("o3_dec_sun", dec_sun_polys(), [sun], 0.02)

    # one sketch per band unit: Fusion's sketch solve is superlinear and
    # a 2680-line one-sketch band measured 70+ minutes; ~180-line unit
    # sketches solve in seconds
    for k in range(8 if BUILD_DECOR else 0):
        adsk.doEvents()
        # vscale 0.60 keeps the band 0.5 mm clear of the ring's top
        # face, which in rev 5 is the solid web between the two ROOT
        # circles (22.2..25.3 mm) - the teeth now run full height
        decor("o3_dec_ring_%d" % k,
              dec_band(dec_ring_unit(), 2.375, 2 * math.pi * k / 8, 0.60),
              [ring], 0.003)

    for k in range(10 if BUILD_DECOR else 0):
        adsk.doEvents()
        decor("o3_dec_house_%d" % k,
              dec_band(dec_housing_unit(), 4.215,
                       2 * math.pi * k / 10, 0.80),
              [house], 0.006)

    pls = bodies_by_prefix("o3_pl_in") + bodies_by_prefix("o3_pl_out")
    if len(pls) != 2 * N_PL:
        raise RuntimeError("planet scan found %d bodies" % len(pls))
    # one small sketch per planet so every 2-minute client window
    # completes whole stages; participants stay the full planet set
    # because pattern body names do not map predictably to angles
    for sname, stv in ((("in", ST_IN), ("out", ST_OUT))
                       if BUILD_DECOR else ()):
        for k in range(N_PL):
            adsk.doEvents()
            decor("o3_dec_pl_%s_%d" % (sname, k),
                  dec_planet_polys(stv, 2 * math.pi * k / N_PL),
                  pls, 0.003)

    # ---- package everything into one component for easy export -------
    def group_component(cname):
        occs = root.occurrences
        for i in range(occs.count):
            if occs.item(i).component.name == cname:
                print("FH skip group (exists)")
                return
        # snapshot first: moveToComponent mutates the live root list
        snap = [b for b in root.bRepBodies]
        names = sorted(b.name for b in snap)
        vtot = sum(b.volume for b in snap)
        occ = occs.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = cname
        for b in snap:
            adsk.doEvents()
            b.moveToComponent(occ)
        comp = occ.component
        after = sorted(b.name for b in comp.bRepBodies)
        v2 = sum(b.volume for b in comp.bRepBodies)
        if (after != names or abs(v2 - vtot) > 0.001
                or root.bRepBodies.count != 0):
            raise RuntimeError("group verify: %d->%d bodies dv=%.4f"
                               % (len(names), len(after), v2 - vtot))
        if not occ.isLightBulbOn:
            occ.isLightBulbOn = True
        print("FH grouped %d bodies into %s vol=%.3f cm3"
              % (len(after), cname, v2))

    # Ridges LAST. Each one fills its gear's tooth spaces at mid-height,
    # which multiplies that body's face count (75 pockets on the housing
    # alone). Joining 24 decor sketches onto bodies in that state is what
    # made rev 5 grind for 45 min at 17 GB. The ridge is a plain revolve
    # and does not care how decorated the body already is, so doing it
    # after the decor costs nothing and keeps every decor boolean cheap.
    # Order is otherwise irrelevant: the ridge sits at mid-height, the
    # decor at z14.5, and neither touches the other.
    add_ridge(sun, SUN, ST_IN, True, "o3_ridge_sun")
    add_ridge(ring, RGI, ST_IN, False, "o3_ridge_ring_int")
    add_ridge(ring, RGE, ST_OUT, True, "o3_ridge_ring_ext")
    add_ridge(house, HSG, ST_OUT, False, "o3_ridge_house")

    group_component("orrery_mk3_90")

    n_total = root.bRepBodies.count
    occs = root.allOccurrences
    for i in range(occs.count):
        n_total += occs.item(i).bRepBodies.count
    print("FH BUILD OK: %d bodies" % n_total)
