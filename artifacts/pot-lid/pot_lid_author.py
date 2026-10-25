"""Pot lid (pot_lid_std) - lid for a celadon pottery jar, rebuilt from the print.

The original authoring script was lost with the PC it lived on (never
committed). This script rebuilds the lid from two surviving sources:

* the printer's `pot_lid.gcode.3mf` (Bambu H2C, 0.16 mm layers), from which
  every wall loop and top-surface contour was read back as (radius, z) - the
  part is a solid of revolution, so that is the whole geometry;
* the "Pot Lid Relief Options" artifact (2026-09-13), which records the
  design intent: O73.5 collar narrowing with an R2.5 rounded edge, relief on
  the top face, built as one profile revolved in Fusion with a Pappus volume
  check.

Geometry, bottom to top: an open annular groove in the underside (the pot's
rim sits in it) between a solid central plug and a tapered outer collar; a
flat outer plateau carrying three hairline beads; a raised central disc with
a large ring bead, a shallow inner dish, a flat boss ring, two small rings
and a spherical dimple at the centre.

Built the way the lost script was: one fixed-art profile (every number is a
named constant in the table below), one revolve, Pappus as the oracle. No
Fusion user parameters are created because nothing would bind to them; edit
the table and re-run instead. `check_profile.py` next to this file overlays
the profile on the printed walls offline.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "liveness": False,     # fixed-art profile: no user parameters to step
    "max_bodies": 2,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
EXPECT_DEAD = []

# ---- parameter table (mm) ----------------------------------------------
# Underside fit. Measured from the printed walls (outer-wall centreline
# + 0.21 mm half line width), so these are the as-printed fit surfaces.
PLUG_R = 27.30          # central plug radius, goes inside the pot rim (O54.6)
GROOVE_R0 = 32.36       # groove outer radius at the base (O64.7)
GROOVE_DEPTH = 7.00     # groove ceiling height above the base
DRAFT_DEG = 13.4        # collar faces lean inward by this angle
COLLAR_R0 = 36.77       # collar outer radius at the base (O73.5)
LID_H = 10.84           # height of the outer plateau
EDGE_R = 2.5            # round on the top outer edge (artifact: R2.5)

# Top relief, outer plateau.
BEAD_R = 0.6                      # hairline bead radius (semicircular)
BEAD_CENTRES = (27.0, 29.5, 30.75)  # bead centre radii on the plateau

# Raised central disc.
DISC_R = 23.70          # disc radius at the plateau
DISC_TOP_R = 22.60      # disc radius at its top (the side is a cone)
DISC_TOP_Z = 12.92      # disc shelf height
RING_R = 20.0           # big ring bead centre radius
RING_BEAD_R = 1.6       # big ring bead radius
RING_PEAK_Z = 14.04     # crest of the ring bead = overall lid height
SHELF_IN_R = 17.0       # inner end of the shelf the ring bead sits on
DISH_R = 10.0           # outer end of the shallow inner dish
DISH_Z = 12.44          # dish height at DISH_R (slopes down from the shelf)
BOSS_TOP_R = 9.7        # flat boss ring, outer radius at its top
BOSS_Z = 13.24          # flat boss ring height
BOSS_IN_R = 6.9         # flat boss ring, inner radius
MICRO_RINGS = ((6.5, 12.92), (5.85, 13.40), (5.2, 12.92))  # two small rings
DIMPLE_RIM_R = 4.5      # spherical centre dimple, rim radius
DIMPLE_FLOOR_Z = 11.64  # dimple floor on the axis
DIMPLE_SPHERE_R = 6.2   # dimple sphere radius

VOLUME_TOL = 0.005      # Pappus vs Fusion body volume, relative


def profile_segments():
    """Closed revolve profile in the (r, z) half-plane, mm, starting at the
    axis foot (0, 0) and running outward along the underside, up the collar,
    inward across the top relief, down the axis. Each segment is
    ("L", end) or ("A", mid, end); the final axis line is implied."""
    segs = []

    def line(p):
        segs.append(("L", p))

    def arc(mid, end):
        segs.append(("A", mid, end))

    k = math.tan(math.radians(DRAFT_DEG))

    # Underside: plug, groove, collar foot.
    line((PLUG_R, 0.0))
    line((PLUG_R, GROOVE_DEPTH))
    line((GROOVE_R0 - k * GROOVE_DEPTH, GROOVE_DEPTH))
    line((GROOVE_R0, 0.0))
    line((COLLAR_R0, 0.0))

    # Collar outer face up to the rounded top edge. The round is tangent to
    # the leaning side and the flat plateau.
    corner_r = COLLAR_R0 - k * LID_H
    half = math.radians((90.0 + DRAFT_DEG) / 2.0)
    t = EDGE_R / math.tan(half)
    s, c = math.sin(math.radians(DRAFT_DEG)), math.cos(math.radians(DRAFT_DEG))
    side_tan = (corner_r + t * s, LID_H - t * c)
    top_tan = (corner_r - t, LID_H)
    centre = (top_tan[0], LID_H - EDGE_R)
    vx, vz = corner_r - centre[0], LID_H - centre[1]
    vn = math.hypot(vx, vz)
    mid = (centre[0] + EDGE_R * vx / vn, centre[1] + EDGE_R * vz / vn)
    line(side_tan)
    arc(mid, top_tan)

    # Plateau with its hairline beads, outermost first.
    for rb in sorted(BEAD_CENTRES, reverse=True):
        line((rb + BEAD_R, LID_H))
        arc((rb, LID_H + BEAD_R), (rb - BEAD_R, LID_H))
    line((DISC_R, LID_H))

    # Raised disc: cone side, shelf, ring bead, shelf.
    line((DISC_TOP_R, DISC_TOP_Z))
    ring_cz = RING_PEAK_Z - RING_BEAD_R
    half_chord = math.sqrt(RING_BEAD_R ** 2 - (DISC_TOP_Z - ring_cz) ** 2)
    line((RING_R + half_chord, DISC_TOP_Z))
    arc((RING_R, RING_PEAK_Z), (RING_R - half_chord, DISC_TOP_Z))
    line((SHELF_IN_R, DISC_TOP_Z))

    # Shallow dish, boss ring, two small rings.
    line((DISH_R, DISH_Z))
    line((BOSS_TOP_R, BOSS_Z))
    line((BOSS_IN_R, BOSS_Z))
    for p in MICRO_RINGS:
        line(p)

    # Spherical dimple down to the axis.
    zc = DIMPLE_FLOOR_Z + DIMPLE_SPHERE_R
    rim_z = zc - math.sqrt(DIMPLE_SPHERE_R ** 2 - DIMPLE_RIM_R ** 2)
    mid_r = DIMPLE_RIM_R / 2.0
    mid_z = zc - math.sqrt(DIMPLE_SPHERE_R ** 2 - mid_r ** 2)
    line((DIMPLE_RIM_R, rim_z))
    arc((mid_r, mid_z), (0.0, DIMPLE_FLOOR_Z))
    return segs


def profile_polygon(arc_steps=48):
    """The profile as a dense closed polygon of (r, z) mm points."""
    pts = [(0.0, 0.0)]
    for seg in profile_segments():
        if seg[0] == "L":
            pts.append(seg[1])
            continue
        _, m, e = seg
        s = pts[-1]
        cx, cz, rad = _circle3(s, m, e)
        a0 = math.atan2(s[1] - cz, s[0] - cx)
        a1 = math.atan2(e[1] - cz, e[0] - cx)
        am = math.atan2(m[1] - cz, m[0] - cx)
        # Sweep from a0 to a1 passing through am.
        d1 = (a1 - a0) % (2 * math.pi)
        dm = (am - a0) % (2 * math.pi)
        if dm > d1:
            d1 -= 2 * math.pi
        for i in range(1, arc_steps + 1):
            a = a0 + d1 * i / arc_steps
            pts.append((cx + rad * math.cos(a), cz + rad * math.sin(a)))
    return pts


def _circle3(p, q, s):
    (x1, y1), (x2, y2), (x3, y3) = p, q, s
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1)
          + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3)
          + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
    return ux, uy, math.hypot(x1 - ux, y1 - uy)


def pappus_volume_cm3():
    """Volume of the revolved profile by Pappus: V = 2*pi*r_centroid*A."""
    pts = profile_polygon()
    n = len(pts)
    a2 = 0.0
    cr6 = 0.0
    for i in range(n):
        r0, z0 = pts[i]
        r1, z1 = pts[(i + 1) % n]
        cross = r0 * z1 - r1 * z0
        a2 += cross
        cr6 += (r0 + r1) * cross
    area = a2 / 2.0
    r_bar = cr6 / (6.0 * area)
    return 2.0 * math.pi * abs(r_bar) * abs(area) / 1000.0


def _fix_sketch(sk):
    for cv in sk.sketchCurves:
        adsk.doEvents()
        if not cv.isFixed:
            cv.isFixed = True
    for sp in sk.sketchPoints:
        adsk.doEvents()
        if sp.isFullyConstrained or sp.isFixed:
            continue
        sp.isFixed = True


def _nearest(sk, candidates, target_mm):
    """Pick the sketch point whose model position is the intended end."""
    best, best_d = None, 1e9
    for spt in candidates:
        w = sk.sketchToModelSpace(spt.geometry)
        d = math.hypot(w.x - target_mm[0] / 10.0, w.z - target_mm[1] / 10.0)
        if d < best_d:
            best, best_d = spt, d
    return best


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    pt = ctx.pt
    cbs = ctx.cbs
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    expected = pappus_volume_cm3()
    print("FH pot lid: Pappus volume %.4f cm3, height %.2f mm, base O%.2f mm"
          % (expected, RING_PEAK_Z, 2 * COLLAR_R0))

    sk = root.sketches.add(root.xZConstructionPlane)
    sk.name = "pot_lid_profile"
    lines = sk.sketchCurves.sketchLines
    arcs = sk.sketchCurves.sketchArcs

    def sp(p_mm):
        return sk.modelToSketchSpace(pt(p_mm[0] / 10.0, 0.0, p_mm[1] / 10.0))

    segs = profile_segments()
    first = lines.addByTwoPoints(sp((0.0, 0.0)), sp(segs[0][1]))
    cur = first.endSketchPoint
    for i, seg in enumerate(segs[1:], start=1):
        if i % 8 == 0:
            adsk.doEvents()
        if seg[0] == "L":
            ln = lines.addByTwoPoints(cur, sp(seg[1]))
            cur = ln.endSketchPoint
        else:
            _, m, e = seg
            ac = arcs.addByThreePoints(cur, sp(m), sp(e))
            cur = _nearest(sk, (ac.startSketchPoint, ac.endSketchPoint), e)
    lines.addByTwoPoints(cur, first.startSketchPoint)   # axis line closes it
    _fix_sketch(sk)
    if sk.profiles.count != 1:
        raise RuntimeError("pot_lid_profile profiles %d, expected 1"
                           % sk.profiles.count)

    rev = root.features.revolveFeatures
    rinp = rev.createInput(sk.profiles.item(0), root.zConstructionAxis,
                           ctx.ops.NewBodyFeatureOperation)
    rinp.setAngleExtent(False, cbs("360 deg"))
    rf = rev.add(rinp)
    rf.name = "pot_lid_revolve"
    if rf.healthState not in healthy:
        raise RuntimeError("pot_lid_revolve unhealthy state %s" % rf.healthState)
    body = rf.bodies.item(0)
    body.name = "pot_lid"

    got = body.volume
    err = abs(got - expected) / expected
    print("FH pot lid: body volume %.4f cm3 (Pappus %.4f, err %.3f%%)"
          % (got, expected, 100 * err))
    if err > VOLUME_TOL:
        raise RuntimeError("volume mismatch: Fusion %.4f vs Pappus %.4f cm3"
                           % (got, expected))

    bb = body.boundingBox
    print("FH pot lid: bbox x %.2f..%.2f z %.2f..%.2f mm"
          % (10 * bb.minPoint.x, 10 * bb.maxPoint.x,
             10 * bb.minPoint.z, 10 * bb.maxPoint.z))
    if abs(10 * bb.maxPoint.z - RING_PEAK_Z) > 0.05:
        raise RuntimeError("height %.3f mm, expected %.3f"
                           % (10 * bb.maxPoint.z, RING_PEAK_Z))
    if abs(10 * bb.maxPoint.x - COLLAR_R0) > 0.05:
        raise RuntimeError("base radius %.3f mm, expected %.3f"
                           % (10 * bb.maxPoint.x, COLLAR_R0))
    print("FH pot lid: done")
