"""ORRERY 90 - part 5: the five rollers.

Cylinders that fly outward 5.5 mm under centrifugal force and lock on
the rim race. Each prints its first layer on the build plate through the
slot throat, and twin 45-degree V-grooves engage the slot-wall ridges so
it tracks instead of rattling. Clearances are the print-proven ones:
0.177 mm normal on the V-way flanks.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 7
FH_OPTS = {
    "only_params": ["or_base_t", "or_fuse_ch",
                    "or_roll_d", "or_stub_d"],
}
INTERFERENCE_ALLOWED = []

# ---- fixed art (cm). Journal is the verified recipe scale. ----
H = 1.4
CAP_R = 1.3
JR = 1.1                      # journal column
RIDGE_R = 1.22
RIDGE_Z = (0.58, 0.70, 0.82)  # 45-deg ridge
CONE_Z0, CONE_Z1 = 0.94, 1.14  # stator cap underside cone (45 deg)
BORE_R = 1.125                # journal bore  (0.25 radial clearance)
GROOVE_R = 1.245
CBORE_R = 1.34                # rotor cap counterbores
CB_LOW_TOP = 0.28             # bottom counterbore top
CB_LOW_CONE = 0.495           # ... cone reaches the bore
CB_UP_CONE = 0.9296           # upper cone leaves the bore
CB_UP_TOP = 1.1446            # ... reaches the counterbore
SLEEVE_R = 1.6
DECK_R0, SCALLOP_A, SCALLOP_N = 3.53, 0.07, 12
SLOT_W = 0.9                  # roller cavity width
THROAT_W = 0.6                # through-slot between the rails
SLOT_RIN, SLOT_ROUT = 1.6, 3.3
WIN_W = 0.58
BAR_IN, BAR_OUT = 2.275, 2.525
SECT_RIN, SECT_ROUT = 1.9, 2.9
SECT_HALF = 8.5               # deg
ROLL_REST = 3.52
# 45-deg V-way: ridge on both slot walls, groove around the roller.
VWAY_ZS = (0.45, 1.10)  # two apex heights, 6.5 mm apart
SLOT_HALF = 0.35       # slot wall
RIDGE_TIP = 0.26       # ridge protrudes 0.9 mm off the wall
ROLL_HALF = 0.30
GROOVE_TIP = 0.235     # groove 0.65 mm deep -> 0.25 mm vertical play
RIDGE_H = SLOT_HALF - RIDGE_TIP        # 0.06
GROOVE_H = ROLL_HALF - GROOVE_TIP      # 0.085
# the groove cut must overshoot the roller surface, so it still crosses
# it if sn_roll_d grows (else a leftover ring fouls the wall ridge)
GROOVE_OUT = 0.40
GROOVE_FLANK = GROOVE_OUT - GROOVE_TIP
DIMPLE_RIM, DIMPLE_DEPTH = 0.9, 0.12


def _fix_sketch(sk):
    i = 0
    for c in sk.sketchCurves:
        i += 1
        if i % 20 == 0:
            adsk.doEvents()
        if not c.isFixed:
            c.isFixed = True
    for sp in sk.sketchPoints:
        i += 1
        if i % 20 == 0:
            adsk.doEvents()
        if sp.isFullyConstrained or sp.isFixed:
            continue
        sp.isFixed = True


def _polyline(sk, pt, rz_pts):
    spts = [sk.modelToSketchSpace(pt(r, 0, z)) for r, z in rz_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _fixed_rect(sk, pt, x0, y0, x1, y1, z):
    p0 = sk.modelToSketchSpace(pt(x0, y0, z))
    p1 = sk.modelToSketchSpace(pt(x1, y1, z))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)


def _circle_edges(bod, lo, hi, z_targets):
    out = adsk.core.ObjectCollection.create()
    for e in bod.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
        g = e.geometry
        r = getattr(g, "radius", None)
        if r is None or not (lo < r < hi):
            continue
        bb = e.boundingBox
        if abs(bb.maxPoint.z - bb.minPoint.z) > 0.02:
            continue
        if any(abs(bb.minPoint.z - zt) < 0.03 for zt in z_targets):
            out.add(e)
    return out




def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    pt = ctx.pt
    cbs = ctx.cbs
    rev = root.features.revolveFeatures
    chf = root.features.chamferFeatures
    cpats = root.features.circularPatternFeatures
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    for nm, val, desc in (("or_roll_d", "6 mm", "roller body dia"),
                          ("or_stub_d", "3.4 mm", "roller pilot stub dia")):
        if ctx.up.itemByName(nm) is None:
            ctx.up.add(nm, cbs(val), "mm", desc)

    rotor = root.bRepBodies.itemByName("or_rotor")
    if rotor is None:
        raise RuntimeError("or_rotor not found")
    n_before_all = root.bRepBodies.count
    print("FH P5 start, %d bodies" % n_before_all)

    plr = ctx.plane_at_z("1.2 mm", "roller_base_plane")
    skro = root.sketches.add(plr)
    skro.name = "roller_body"
    ctx.bound_circle(skro, (0, ROLL_REST, 0.12), 0.30, "or_roll_d",
                     x_pos="0 mm", v_pos="35.2 mm")

    def roller_ok(b):
        bb = b.boundingBox
        return (0.25 < b.volume < 0.50 and
                abs((bb.maxPoint.y + bb.minPoint.y) / 2 - ROLL_REST) < 0.05)

    fro, roller = ctx.checked_newbody(
        ctx.all_profiles(skro), "14.5 mm - 1.2 mm", roller_ok, "roller")
    fro.name = "roller_body_extrude"
    roller.name = "or_roller_1"

    skst = root.sketches.add(root.xYConstructionPlane)
    skst.name = "roller_stub"
    ctx.bound_circle(skst, (0, ROLL_REST, 0), 0.17, "or_stub_d",
                     x_pos="0 mm", v_pos="35.2 mm")
    vs0 = roller.volume
    sinp = ctx.extrudes.createInput(ctx.all_profiles(skst),
                                    ctx.ops.JoinFeatureOperation)
    exs = adsk.fusion.DistanceExtentDefinition.create(cbs("1.2 mm"))
    sinp.setOneSideExtent(exs, ctx.dirs.PositiveExtentDirection)
    sinp.participantBodies = [roller]
    fst = ctx.extrudes.add(sinp)
    fst.name = "roller_stub_extrude"
    if roller.volume - vs0 < 0.005:
        raise RuntimeError("stub added %.4f" % (roller.volume - vs0))

    seat = _circle_edges(roller, 0.25, 0.35, (0.12,))
    if seat.count != 1:
        raise RuntimeError("roller seat edge %d != 1" % seat.count)
    ci0 = chf.createInput2()
    ci0.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        seat, cbs("( or_roll_d - or_stub_d ) / 2"), True)
    cf0 = chf.add(ci0)
    cf0.name = "roller_seat_cone"

    skgv = root.sketches.add(root.yZConstructionPlane)
    skgv.name = "roller_vgroove"
    gl = skgv.sketchCurves.sketchLines
    for zc in VWAY_ZS:
        gtri = [(GROOVE_OUT, zc - GROOVE_FLANK),
                (GROOVE_TIP, zc),
                (GROOVE_OUT, zc + GROOVE_FLANK)]
        gpts = [skgv.modelToSketchSpace(pt(0, ROLL_REST + r, z))
                for r, z in gtri]
        ga = gl.addByTwoPoints(gpts[0], gpts[1])
        gb = gl.addByTwoPoints(ga.endSketchPoint, gpts[2])
        gl.addByTwoPoints(gb.endSketchPoint, ga.startSketchPoint)
    ax = gl.addByTwoPoints(
        skgv.modelToSketchSpace(pt(0, ROLL_REST, 0.0)),
        skgv.modelToSketchSpace(pt(0, ROLL_REST, 1.45)))
    ax.isConstruction = True
    _fix_sketch(skgv)
    gprof = adsk.core.ObjectCollection.create()
    for p in skgv.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
        if p.areaProperties().area < 0.05:
            gprof.add(p)
    if gprof.count != 2:
        raise RuntimeError("roller V-groove profiles %d != 2" % gprof.count)
    gv0 = roller.volume
    grinp = rev.createInput(gprof, ax, ctx.ops.CutFeatureOperation)
    grinp.setAngleExtent(False, cbs("360 deg"))
    grinp.participantBodies = [roller]
    fgv = rev.add(grinp)
    fgv.name = "roller_vgroove_cut"
    if gv0 - roller.volume < 0.005:
        raise RuntimeError("V-groove removed %.4f" % (gv0 - roller.volume))
    print("FH roller vol: %.3f" % roller.volume)

    bcoll = adsk.core.ObjectCollection.create()
    bcoll.add(roller)
    pinp2 = cpats.createInput(bcoll, root.zConstructionAxis)
    pinp2.quantity = cbs("5")
    pinp2.totalAngle = cbs("360 deg")
    pinp2.isSymmetric = False
    pfb = cpats.add(pinp2)
    if (pfb.healthState not in healthy or
            root.bRepBodies.count - n_before_all != 5):
        raise RuntimeError("roller pattern bodies %d"
                           % (root.bRepBodies.count - n_before_all))
    pfb.name = "roller_pattern"
    for i in range(pfb.bodies.count):
        pfb.bodies.item(i).name = "or_roller_%d" % (i + 2)

    print("FH P5 OK: %d bodies total" % root.bRepBodies.count)
