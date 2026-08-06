"""Supernova 72 rev D - captured V-way, open-top slots.

FIX 1 (rollers must never fuse). Research verdict: a 0.30 mm gap is
below the 2x-layer-height floor, is not an integer multiple of layer
height (so it quantises to 0.2 or 0.4 unpredictably), and the roller's
first layer was a dia-8 free-floating island with no anchors - it droops
and welds. Available break-free force is ~3.3 mN at 3 rev/s; any weld is
newtons. So the roller is now referenced to the BUILD PLATE, the trick
print-in-place roller-bearing spinners use: the slot floor becomes two
radial rails with a 6.0 mm through-slot between them, and each roller
carries a dia-4.6 pilot stub that reaches the plate through it. The
roller's first layer is a solid disc ON GLASS - no floating island
anywhere, minimum air gap 0.70 mm horizontal. On plate release each
roller settles 0.70 mm until its 45-degree cone seats on the two rail
edges: a self-centring V, two line contacts, extrusion lines running
along the direction of travel.

FIX 2 (no 90-degree overhangs on the stator). The top cap underside was
a flat 2 mm annular ledge (column r11 -> cap r13 at z11.5). It is now a
45-degree cone, z9.4 -> z11.4. The rotor's mating counterbore ceilings -
both of them - become 45-degree cones too (required: a coned stator cap
clashes with a flat rotor counterbore). The bottom finger dimple is
deleted: a shallow spherical dimple on a BOTTOM face is a near-flat
unsupported ceiling at its apex, which violates the 45-degree rule. The
top dimple stays (a cut into a top face has no overhang at all).

Every stator surface is now vertical, a top face, or 45 degrees.

FIX 3 (rev C, from the rev B PRINT). Rev B slid freely - plate
referencing worked - but the rollers RATTLED instead of tracking: located
only by gravity on two rail edges, each had ~1.1 mm of vertical play and
~1.0 mm laterally, so it could bounce and cock. Rev C captures them with
the same 45-degree joint the journal uses: TWO V-ridges run the length of
both slot walls, and each roller carries two matching circumferential
V-grooves. Two spaced constraints stop it cocking, which single
mid-height capture would not. Vertical play drops to 0.25 mm and the roller can no longer
tilt. Normal flank clearance is 0.177 mm - the value the rev B print
demonstrated slides freely.

The roller now rides the V-way at its printed height and never settles
onto the rails, so the pilot stub stays flush at z0 instead of
protruding. The stub is purely a printability device now: it is what puts
the first layer on the build plate.

FIX 4 (rev D). The slot ceiling was the last 90-degree overhang in the
design - its underside bridged the slot at z12.4 and was the only face
class still failing the 45-degree audit. It existed solely to stop the
rollers escaping upward, and the twin V-ways now do that job. So the
ceiling is gone: the slots run open to the full 14 mm height, and each
roller is full height too, flush with the rotor top. The slot stays
0.5 mm wider than the roller on each side.

Net effect: zero overhangs steeper than 45 degrees anywhere, no bridges
at all, and the rollers are fully visible from above instead of hidden
under a roof.

Bodies: sn3_stator, sn3_rotor, sn3_roller_1..6.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["sn_rail_t", "sn_roll_d",
                    "sn_stub_d", "sn_cap_ch", "sn_fuse_ch"],
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
ROLL_REST = 2.05
# 45-deg V-way: ridge on both slot walls, groove around the roller.
VWAY_ZS = (0.45, 1.10)  # two apex heights, 6.5 mm apart
SLOT_HALF = 0.45       # slot wall
RIDGE_TIP = 0.36       # ridge protrudes 0.9 mm off the wall
ROLL_HALF = 0.40
GROOVE_TIP = 0.335     # groove 0.65 mm deep -> 0.25 mm vertical play
RIDGE_H = SLOT_HALF - RIDGE_TIP        # 0.06
GROOVE_H = ROLL_HALF - GROOVE_TIP      # 0.085
# the groove cut must overshoot the roller surface, so it still crosses
# it if sn_roll_d grows (else a leftover ring fouls the wall ridge)
GROOVE_OUT = 0.50
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
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs
    rev = root.features.revolveFeatures
    chf = root.features.chamferFeatures
    cpats = root.features.circularPatternFeatures
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    up.add("sn_rail_t", cbs("1.2 mm"), "mm", "rail thickness = stub height")
    up.add("sn_roll_d", cbs("8 mm"), "mm", "roller body dia")
    up.add("sn_stub_d", cbs("4.6 mm"), "mm", "roller pilot stub dia")
    up.add("sn_cap_ch", cbs("0.4 mm"), "mm", "cap rim chamfer")
    up.add("sn_fuse_ch", cbs("0.3 mm"), "mm", "anti-fuse chamfer")
    print("FH params added")

    # ================= STATOR (all faces vertical / top / 45 deg) =====
    sks = root.sketches.add(root.xZConstructionPlane)
    sks.name = "stator_profile"
    _polyline(sks, pt, [
        (0.0, 0.0), (CAP_R, 0.0), (CAP_R, 0.25), (JR, 0.25),
        (JR, RIDGE_Z[0]), (RIDGE_R, RIDGE_Z[1]), (JR, RIDGE_Z[2]),
        (JR, CONE_Z0), (CAP_R, CONE_Z1), (CAP_R, H), (0.0, H),
    ])
    _fix_sketch(sks)
    if sks.profiles.count != 1:
        raise RuntimeError("stator profiles %d" % sks.profiles.count)
    rinp = rev.createInput(sks.profiles.item(0), root.zConstructionAxis,
                           ctx.ops.NewBodyFeatureOperation)
    rinp.setAngleExtent(False, cbs("360 deg"))
    rf = rev.add(rinp)
    rf.name = "stator_revolve"
    stator = rf.bodies.item(0)
    stator.name = "sn3_stator"
    if not (5.0 < stator.volume < 8.0):
        raise RuntimeError("stator vol %.3f" % stator.volume)

    # top finger dimple only (a bottom dimple's apex is a flat ceiling)
    sph_r = (DIMPLE_RIM ** 2 + DIMPLE_DEPTH ** 2) / (2 * DIMPLE_DEPTH)
    z_apex = H - DIMPLE_DEPTH
    zc = z_apex + sph_r
    va = (0.0, z_apex - zc)
    vb = (DIMPLE_RIM, H - zc)
    ms = (va[0] + vb[0], va[1] + vb[1])
    mn = math.hypot(ms[0], ms[1])
    mid = (sph_r * ms[0] / mn, zc + sph_r * ms[1] / mn)
    skd = root.sketches.add(root.xZConstructionPlane)
    skd.name = "top_dimple"
    dl = skd.sketchCurves.sketchLines
    ax_ln = dl.addByTwoPoints(skd.modelToSketchSpace(pt(0, 0, z_apex)),
                              skd.modelToSketchSpace(pt(0, 0, H)))
    face_ln = dl.addByTwoPoints(
        ax_ln.endSketchPoint, skd.modelToSketchSpace(pt(DIMPLE_RIM, 0, H)))
    skd.sketchCurves.sketchArcs.addByThreePoints(
        face_ln.endSketchPoint,
        skd.modelToSketchSpace(pt(mid[0], 0, mid[1])),
        ax_ln.startSketchPoint)
    _fix_sketch(skd)
    if skd.profiles.count != 1:
        raise RuntimeError("dimple profiles %d" % skd.profiles.count)
    v0 = stator.volume
    di = rev.createInput(skd.profiles.item(0), root.zConstructionAxis,
                         ctx.ops.CutFeatureOperation)
    di.setAngleExtent(False, cbs("360 deg"))
    di.participantBodies = [stator]
    dfe = rev.add(di)
    dfe.name = "top_dimple_cut"
    if v0 - stator.volume < 0.08:
        raise RuntimeError("dimple removed %.4f" % (v0 - stator.volume))
    print("FH stator vol: %.3f" % stator.volume)

    # ================= ROTOR sleeve (coned counterbore ceilings) ======
    skr = root.sketches.add(root.xZConstructionPlane)
    skr.name = "rotor_profile"
    _polyline(skr, pt, [
        (SLEEVE_R, 0.0), (CBORE_R, 0.0), (CBORE_R, CB_LOW_TOP),
        (BORE_R, CB_LOW_CONE),
        (BORE_R, RIDGE_Z[0]), (GROOVE_R, RIDGE_Z[1]), (BORE_R, RIDGE_Z[2]),
        (BORE_R, CB_UP_CONE), (CBORE_R, CB_UP_TOP), (CBORE_R, H),
        (SLEEVE_R, H),
    ])
    _fix_sketch(skr)
    if skr.profiles.count != 1:
        raise RuntimeError("rotor profiles %d" % skr.profiles.count)
    rinp2 = rev.createInput(skr.profiles.item(0), root.zConstructionAxis,
                            ctx.ops.NewBodyFeatureOperation)
    rinp2.setAngleExtent(False, cbs("360 deg"))
    rf2 = rev.add(rinp2)
    rf2.name = "rotor_sleeve_revolve"
    rotor = rf2.bodies.item(0)
    rotor.name = "sn3_rotor"
    if not (3.0 < rotor.volume < 6.0):
        raise RuntimeError("rotor sleeve vol %.3f" % rotor.volume)
    print("FH rotor sleeve vol: %.3f" % rotor.volume)

    # ---- scalloped deck ------------------------------------------------
    skdk = root.sketches.add(root.xYConstructionPlane)
    skdk.name = "deck_outline"
    pts = adsk.core.ObjectCollection.create()
    n = 72
    for i in range(n + 1):
        th = 2 * math.pi * (i % n) / n
        r = DECK_R0 + SCALLOP_A * math.cos(SCALLOP_N * th)
        pts.add(skdk.modelToSketchSpace(
            pt(r * math.cos(th), r * math.sin(th), 0)))
    skdk.sketchCurves.sketchFittedSplines.add(pts)
    ctx.bound_circle(skdk, (0, 0, 0), SLEEVE_R, "32 mm",
                     x_pos="0 mm", v_pos="0 mm")
    _fix_sketch(skdk)
    deck_prof = None
    for p in skdk.profiles:
        a = p.areaProperties().area
        if 28.0 < a < 34.0:
            deck_prof = p
            break
    if deck_prof is None:
        raise RuntimeError("no deck annulus profile")
    v1 = rotor.volume
    dinp = ctx.extrudes.createInput(deck_prof, ctx.ops.JoinFeatureOperation)
    ext = adsk.fusion.DistanceExtentDefinition.create(cbs("14 mm"))
    dinp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
    dinp.participantBodies = [rotor]
    fdk = ctx.extrudes.add(dinp)
    fdk.name = "deck_extrude"
    if rotor.volume - v1 < 35.0:
        raise RuntimeError("deck added %.3f" % (rotor.volume - v1))
    print("FH deck joined, rotor vol: %.3f" % rotor.volume)

    # ---- seed cuts at azimuth 90 --------------------------------------
    plc = ctx.plane_at_z("sn_rail_t", "cavity_floor_plane")
    skc = root.sketches.add(plc)
    skc.name = "slot_seed"
    _fixed_rect(skc, pt, -SLOT_W / 2, SLOT_RIN, SLOT_W / 2, SLOT_ROUT, 0.12)
    _fix_sketch(skc)
    fslot = ctx.blind_cut(ctx.all_profiles(skc),
                          "14 mm - sn_rail_t", [rotor],
                          "slot", min_vol_cm3=1.5)
    fslot.name = "slot_seed_cut"

    # the through-slot: rails either side, roller stub reaches the plate
    skth = root.sketches.add(root.xYConstructionPlane)
    skth.name = "throat_seed"
    _fixed_rect(skth, pt, -THROAT_W / 2, SLOT_RIN, THROAT_W / 2,
                SLOT_ROUT, 0.0)
    _fix_sketch(skth)
    fthr = ctx.blind_cut(ctx.all_profiles(skth), "sn_rail_t", [rotor],
                         "throat", min_vol_cm3=0.08)
    fthr.name = "throat_seed_cut"

    sksec = root.sketches.add(root.xYConstructionPlane)
    sksec.name = "sector_seed"
    az = math.radians(120)
    a0, a1 = az - math.radians(SECT_HALF), az + math.radians(SECT_HALF)
    sl = sksec.sketchCurves.sketchLines
    sa = sksec.sketchCurves.sketchArcs
    l1 = sl.addByTwoPoints(
        sksec.modelToSketchSpace(pt(SECT_RIN * math.cos(a0),
                                    SECT_RIN * math.sin(a0), 0)),
        sksec.modelToSketchSpace(pt(SECT_ROUT * math.cos(a0),
                                    SECT_ROUT * math.sin(a0), 0)))
    arc1 = sa.addByThreePoints(
        l1.endSketchPoint,
        sksec.modelToSketchSpace(pt(SECT_ROUT * math.cos(az),
                                    SECT_ROUT * math.sin(az), 0)),
        sksec.modelToSketchSpace(pt(SECT_ROUT * math.cos(a1),
                                    SECT_ROUT * math.sin(a1), 0)))
    l2 = sl.addByTwoPoints(
        arc1.endSketchPoint,
        sksec.modelToSketchSpace(pt(SECT_RIN * math.cos(a1),
                                    SECT_RIN * math.sin(a1), 0)))
    sa.addByThreePoints(
        l2.endSketchPoint,
        sksec.modelToSketchSpace(pt(SECT_RIN * math.cos(az),
                                    SECT_RIN * math.sin(az), 0)),
        l1.startSketchPoint)
    _fix_sketch(sksec)
    if sksec.profiles.count != 1:
        raise RuntimeError("sector profiles %d" % sksec.profiles.count)
    fsec = ctx.blind_cut(ctx.all_profiles(sksec), "15 mm", [rotor],
                         "sector", min_vol_cm3=0.7)
    fsec.name = "sector_seed_cut"

    # V-ridge along both slot walls (45 deg, self-supporting both flanks)
    skv = root.sketches.add(root.xZConstructionPlane)
    skv.name = "vway_ridge"
    for zc in VWAY_ZS:
        for sgn in (1, -1):
            adsk.doEvents()
            tri = [(sgn * SLOT_HALF, zc - RIDGE_H),
                   (sgn * RIDGE_TIP, zc),
                   (sgn * SLOT_HALF, zc + RIDGE_H)]
            spts = [skv.modelToSketchSpace(pt(x, 0, z)) for x, z in tri]
            vl = skv.sketchCurves.sketchLines
            a = vl.addByTwoPoints(spts[0], spts[1])
            b = vl.addByTwoPoints(a.endSketchPoint, spts[2])
            vl.addByTwoPoints(b.endSketchPoint, a.startSketchPoint)
    _fix_sketch(skv)
    if skv.profiles.count != 4:
        raise RuntimeError("vway ridge profiles %d != 4" % skv.profiles.count)
    vr0 = rotor.volume
    vinp = ctx.extrudes.createInput(ctx.all_profiles(skv),
                                    ctx.ops.JoinFeatureOperation)
    vinp.startExtent = adsk.fusion.OffsetStartDefinition.create(cbs("16 mm"))
    vext = adsk.fusion.DistanceExtentDefinition.create(cbs("17 mm"))
    vinp.setOneSideExtent(vext, ctx.dirs.PositiveExtentDirection)
    vinp.participantBodies = [rotor]
    fvway = ctx.extrudes.add(vinp)
    fvway.name = "vway_ridge_extrude"
    if rotor.volume - vr0 < 0.010:
        raise RuntimeError("vway ridge added %.4f" % (rotor.volume - vr0))
    print("FH seed cuts + V-ridge done, rotor vol: %.3f" % rotor.volume)

    v2 = rotor.volume
    coll = adsk.core.ObjectCollection.create()
    for f in (fslot, fthr, fsec):  # fusionhelper: allow R11 — collection add, not a document mutation
        coll.add(f)
    pinp = cpats.createInput(coll, root.zConstructionAxis)
    pinp.quantity = cbs("6")
    pinp.totalAngle = cbs("360 deg")
    pinp.isSymmetric = False
    popts = adsk.fusion.PatternComputeOptions
    pinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pfc = cpats.add(pinp)
    if pfc.healthState not in healthy or v2 - rotor.volume < 12.0:
        raise RuntimeError("cut pattern dv=%.3f" % (v2 - rotor.volume))
    pfc.name = "cutout_pattern"

    v3 = rotor.volume
    vcoll = adsk.core.ObjectCollection.create()
    vcoll.add(fvway)
    vpinp = cpats.createInput(vcoll, root.zConstructionAxis)
    vpinp.quantity = cbs("6")
    vpinp.totalAngle = cbs("360 deg")
    vpinp.isSymmetric = False
    vpinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pfv = cpats.add(vpinp)
    if pfv.healthState not in healthy or rotor.volume - v3 < 0.04:
        raise RuntimeError("vway pattern dv=%.4f" % (rotor.volume - v3))
    pfv.name = "vway_pattern"
    print("FH cut + V-way patterns done, rotor vol: %.3f" % rotor.volume)

    # ================= ROLLER (body + plate-reaching pilot stub) ======
    plr = ctx.plane_at_z("sn_rail_t", "roller_base_plane")
    skro = root.sketches.add(plr)
    skro.name = "roller_body"
    ctx.bound_circle(skro, (0, ROLL_REST, 0.12), 0.4, "sn_roll_d",
                     x_pos="0 mm", v_pos="20.5 mm")

    def roller_ok(b):
        bb = b.boundingBox
        return (0.50 < b.volume < 0.80 and
                abs((bb.maxPoint.y + bb.minPoint.y) / 2 - ROLL_REST) < 0.05)

    fro, roller = ctx.checked_newbody(
        ctx.all_profiles(skro),
        "14 mm - sn_rail_t", roller_ok, "roller")
    fro.name = "roller_body_extrude"
    roller.name = "sn3_roller_1"

    skst = root.sketches.add(root.xYConstructionPlane)
    skst.name = "roller_stub"
    ctx.bound_circle(skst, (0, ROLL_REST, 0), 0.23, "sn_stub_d",
                     x_pos="0 mm", v_pos="20.5 mm")
    vs0 = roller.volume
    sinp = ctx.extrudes.createInput(ctx.all_profiles(skst),
                                    ctx.ops.JoinFeatureOperation)
    exs = adsk.fusion.DistanceExtentDefinition.create(cbs("sn_rail_t"))
    sinp.setOneSideExtent(exs, ctx.dirs.PositiveExtentDirection)
    sinp.participantBodies = [roller]
    fst = ctx.extrudes.add(sinp)
    fst.name = "roller_stub_extrude"
    if roller.volume - vs0 < 0.01:
        raise RuntimeError("stub added %.4f" % (roller.volume - vs0))

    # 45-deg seat cone: chamfer the body's lower rim down to the stub
    seat = _circle_edges(roller, 0.35, 0.45, (0.12,))
    if seat.count != 1:
        raise RuntimeError("roller seat edge %d != 1" % seat.count)
    ci0 = chf.createInput2()
    ci0.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        seat, cbs("( sn_roll_d - sn_stub_d ) / 2"), True)
    cf0 = chf.add(ci0)
    cf0.name = "roller_seat_cone"

    # matching circumferential V-groove, revolved about the roller axis
    skgv = root.sketches.add(root.yZConstructionPlane)
    skgv.name = "roller_vgroove"
    gl = skgv.sketchCurves.sketchLines
    for zc in VWAY_ZS:
        adsk.doEvents()
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
        skgv.modelToSketchSpace(pt(0, ROLL_REST, 1.4)))
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
    if gv0 - roller.volume < 0.010:
        raise RuntimeError("V-groove removed %.4f" % (gv0 - roller.volume))
    print("FH roller + V-groove vol: %.3f" % roller.volume)

    bcoll = adsk.core.ObjectCollection.create()
    bcoll.add(roller)
    n_before = root.bRepBodies.count
    pinp2 = cpats.createInput(bcoll, root.zConstructionAxis)
    pinp2.quantity = cbs("6")
    pinp2.totalAngle = cbs("360 deg")
    pinp2.isSymmetric = False
    pfb = cpats.add(pinp2)
    if (pfb.healthState not in healthy or
            root.bRepBodies.count - n_before != 5):
        raise RuntimeError("roller pattern bodies %d"
                           % (root.bRepBodies.count - n_before))
    pfb.name = "roller_pattern"
    for i in range(pfb.bodies.count):
        pfb.bodies.item(i).name = "sn3_roller_%d" % (i + 2)
    print("FH rollers done: %d bodies" % root.bRepBodies.count)

    # ---- chamfers: cap rims, anti-fuse pair ---------------------------
    caps = _circle_edges(stator, 1.25, 1.35, (0.0, H))
    if caps.count != 2:
        raise RuntimeError("cap rim edges %d != 2" % caps.count)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        caps, cbs("sn_cap_ch"), True)
    c1 = chf.add(ci)
    c1.name = "cap_rim_chamfer"

    fuse = _circle_edges(rotor, 1.30, 1.38, (0.0,))
    if fuse.count != 1:
        raise RuntimeError("anti-fuse edges %d != 1" % fuse.count)
    ci2 = chf.createInput2()
    ci2.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        fuse, cbs("sn_fuse_ch"), True)
    c2 = chf.add(ci2)
    c2.name = "rotor_antifuse_chamfer"

    print("FH BUILD OK: stator %.3f rotor %.3f roller %.3f cm3, %d bodies"
          % (stator.volume, rotor.volume, roller.volume,
             root.bRepBodies.count))
