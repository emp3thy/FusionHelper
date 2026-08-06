"""ORRERY mk3 - planets on BOTH faces of the ring.

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

Retention (rev 2) lives at the ENDS, never mid-band - the scheme
measured off the working commercial reference (Gear+fidget+spinner.3mf):

  - planets carry full-circle end flanges at tip + 0.6 mm, z 0-1.2 and
    z 13.3-14.5; the top flange underside is chamfered 45 deg so it
    prints on its own cone;
  - sun / ring / housing are recessed at both ends to ROOT -/+ 0.55 mm.
    Root-referenced: tip-referenced sizing is what produced 2.8 mm-deep
    grooves and the 5.4 mm mid-band recess that cut across the tooth
    band on rev 1;
  - a 45 deg tooth-entry chamfer joins each recess to its tip band, so
    no tooth tip overhangs a recess. Tip band z 4.55-9.95.

Every body is full height, z0 to z14.5. There are no caps. Flange sits
0.2 mm radially clear of every recess; axial float ~0.75 mm per stage.

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

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {"liveness": False}
INTERFERENCE_ALLOWED = []

PANG = math.radians(25)
BACKLASH = 0.020
H = 1.45                       # full stack; every body spans z0..H
FL_H, FL_R = 0.12, 0.06        # planet end flange: height, radial protrusion
RC_CLR = 0.055                 # recess clears the gear's own ROOT by this
CH = 0.28                      # entry-chamfer z span; radial spans 0.255-0.275
#                                so every chamfer is 45.6-47.7 deg, printable
RZ0 = 0.175                    # bottom recess ceiling; top floor at H - RZ0
RZ1 = H - RZ0
ZB0, ZB1 = RZ0 + CH, RZ1 - CH  # full-profile tip band, z 4.55..9.95 mm

SUN = dict(N=20, rp=1.00, tip=1.095, root=0.875, internal=False)
PLI = dict(N=10, rp=0.50, tip=0.60, root=0.375, internal=False)
RGI = dict(N=40, rp=2.00, tip=1.925, root=2.125, internal=True)
RGE = dict(N=55, rp=2.75, tip=2.840, root=2.625, internal=False)
PLO = dict(N=10, rp=0.50, tip=0.60, root=0.375, internal=False)
HSG = dict(N=75, rp=3.75, tip=3.670, root=3.875, internal=True)
ST_IN, ST_OUT = 1.50, 3.25
HOUSE_OUT = 4.50
N_PL = 5


def _rc(g):
    """End-recess radius: 0.55 mm beyond the gear's own tooth root."""
    return g["root"] + RC_CLR if g["internal"] else g["root"] - RC_CLR


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

    # ---- sun: free idler ---------------------------------------------
    rcs = _rc(SUN)
    sun = gear("o3_sun", [
        (0.0, 0.0), (rcs, 0.0), (rcs, RZ0), (SUN["tip"], ZB0),
        (SUN["tip"], ZB1), (rcs, RZ1), (rcs, H), (0.0, H)],
        [(SUN, "sun_tooth", 0.0)])
    print("FH sun %.3f cm3" % sun.volume)

    # ---- ring: teeth on both faces -----------------------------------
    rci, rce = _rc(RGI), _rc(RGE)
    ring = gear("o3_ring", [
        (rci, 0.0), (rce, 0.0), (rce, RZ0), (RGE["tip"], ZB0),
        (RGE["tip"], ZB1), (rce, RZ1), (rce, H), (rci, H),
        (rci, RZ1), (RGI["tip"], ZB1), (RGI["tip"], ZB0), (rci, RZ0)],
        [(RGI, "ring_int", 0.0), (RGE, "ring_ext", 0.0)])
    print("FH ring %.3f cm3" % ring.volume)

    # ---- housing: the part you hold ----------------------------------
    rch = _rc(HSG)
    house = gear("o3_housing", [
        (rch, 0.0), (HOUSE_OUT, 0.0), (HOUSE_OUT, H), (rch, H),
        (rch, RZ1), (HSG["tip"], ZB1), (HSG["tip"], ZB0), (rch, RZ0)],
        [(HSG, "house_tooth", 0.0)])
    print("FH housing %.3f cm3" % house.volume)

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

        fr = g["tip"] + FL_R
        zc = H - FL_H - FL_R           # top flange under-chamfer start
        for fname, prof in (
                (name + "_flange_lo", [(0.30, 0.0), (fr, 0.0),
                                       (fr, FL_H), (0.30, FL_H)]),
                (name + "_flange_hi", [(0.30, zc), (g["tip"], zc),
                                       (fr, zc + FL_R), (fr, H),
                                       (0.30, H)])):
            adsk.doEvents()
            skb = root.sketches.add(root.xZConstructionPlane)
            skb.name = fname
            _poly_rz(skb, pt, prof)
            _fix(skb)
            if skb.profiles.count != 1:
                raise RuntimeError("%s profiles %d"
                                   % (fname, skb.profiles.count))
            vb = body.volume
            bin_ = rev.createInput(skb.profiles.item(0),
                                   root.zConstructionAxis,
                                   ctx.ops.JoinFeatureOperation)
            bin_.setAngleExtent(False, cbs("360 deg"))
            bin_.participantBodies = [body]
            rev.add(bin_).name = fname + "_revolve"
            if body.volume - vb < 0.002:
                raise RuntimeError("%s added %.4f" % (fname,
                                                      body.volume - vb))

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

    def find_extrude(name):
        # a join whose participants live inside a component lands in
        # THAT component's feature collection, not root's - a root-only
        # itemByName then misses it and the stage re-joins zero volume
        f = root.features.extrudeFeatures.itemByName(name)
        if f is not None:
            return f
        occs = root.allOccurrences
        for i in range(occs.count):
            f = occs.item(i).component.features.extrudeFeatures \
                .itemByName(name)
            if f is not None:
                return f
        return None

    def decor(sk_name, polys, participants, min_vol):
        # guard on the JOIN, not the sketch: a dead client can commit
        # the sketch and die before the join, and a sketch-based guard
        # would then silently skip the decor forever. The join gets a
        # "_join" suffix - sketches and features share one name
        # namespace, and an extrude named like its sketch is silently
        # auto-suffixed to "name (1)", which a guard then misses.
        if find_extrude(sk_name + "_join") is not None:
            print("FH skip %s (exists)" % sk_name)
            return
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
        print("FH %s: %d stroke profiles joined, %d enclosed dropped"
              % (sk_name, profs.count, dropped))

    decor("o3_dec_sun", dec_sun_polys(), [sun], 0.02)

    # one sketch per band unit: Fusion's sketch solve is superlinear and
    # a 2680-line one-sketch band measured 70+ minutes; ~180-line unit
    # sketches solve in seconds
    for k in range(8):
        adsk.doEvents()
        decor("o3_dec_ring_%d" % k,
              dec_band(dec_ring_unit(), 2.375, 2 * math.pi * k / 8, 0.80),
              [ring], 0.003)

    for k in range(10):
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
    for sname, stv in (("in", ST_IN), ("out", ST_OUT)):
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

    group_component("orrery_mk3_90")

    n_total = root.bRepBodies.count
    occs = root.allOccurrences
    for i in range(occs.count):
        n_total += occs.item(i).bRepBodies.count
    print("FH BUILD OK: %d bodies" % n_total)
