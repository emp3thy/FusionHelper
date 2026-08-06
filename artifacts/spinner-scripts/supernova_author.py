"""Supernova 72 - print-in-place variable-inertia flagship spinner.

Per docs/supernova-72-spec.md. Six free rollers rattle loose in open
radial slots at rest, fly out and seat on the hidden r33 race at speed
(silent, higher inertia), cascade back with an audible rattle as the
spin dies (~2.9 rev/s threshold).

Bodies: sn_stator (hub, diamond journal, finger dimples both caps),
sn_rotor (journal sleeve + scalloped deck, 6 windowed slots, 6
lightening sectors, r33 race), sn_roller_1..6 (dia 8 x 10.4, resting at
r20.5).

Fixed art: journal (base r11, ridge 1.2, radial clearance 0.25 - the
verified recipe scale), scallop spline R=35.3+0.7cos(12t) (NEVER
chamfered), slot/window/sector rects (exact coords; bound_rect2 unusable
for centre-0 rects - measured corner-dim sign bug). Live parameters:
floor/cavity/ceiling stack, roller float gap + dia, chamfers.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["sn_floor_t", "sn_cavity_h", "sn_ceiling_t",
                    "sn_g_float", "sn_roll_d", "sn_cap_ch", "sn_fuse_ch"],
}
INTERFERENCE_ALLOWED = []

# Fixed art constants (cm).
H = 1.4
CAP_R = 1.3
JR = 1.1            # journal base radius
RIDGE_R = 1.22      # ridge peak
CLR = 0.025         # radial journal clearance
BORE_R = JR + CLR       # 1.125
GROOVE_R = RIDGE_R + CLR  # 1.245
RIDGE_Z = (0.58, 0.70, 0.82)
CBORE_R = 1.34      # rotor cap counterbore
CBORE_D = 0.28
SLEEVE_R = 1.6
DECK_R0 = 3.53      # scallop mean radius
SCALLOP_A = 0.07
SCALLOP_N = 12
SLOT_W = 0.9
SLOT_RIN, SLOT_ROUT = 1.6, 3.3
WIN_W = 0.58
BAR_IN, BAR_OUT = 2.275, 2.525   # crossbar band at r24
SECT_RIN, SECT_ROUT = 1.9, 2.9
SECT_HALF = 8.5     # deg
ROLL_REST = 2.05
ROLL_H = 1.04
DIMPLE_RIM = 0.9
DIMPLE_DEPTH = 0.12
SPH_R = (DIMPLE_RIM ** 2 + DIMPLE_DEPTH ** 2) / (2 * DIMPLE_DEPTH)


def _fix_sketch(sk):
    for c in sk.sketchCurves:
        adsk.doEvents()
        if not c.isFixed:
            c.isFixed = True
    for sp in sk.sketchPoints:
        adsk.doEvents()
        if sp.isFullyConstrained or sp.isFixed:
            continue
        sp.isFixed = True


def _polyline(sk, pt, rz_pts, close=True):
    spts = [sk.modelToSketchSpace(pt(r, 0, z)) for r, z in rz_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    if close:
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _fixed_rect(sk, pt, x0, y0, x1, y1, z):
    p0 = sk.modelToSketchSpace(pt(x0, y0, z))
    p1 = sk.modelToSketchSpace(pt(x1, y1, z))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs
    rev = root.features.revolveFeatures
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    up.add("sn_floor_t", cbs("1.2 mm"), "mm", "slot floor thickness")
    up.add("sn_cavity_h", cbs("11.2 mm"), "mm", "slot cavity height")
    up.add("sn_ceiling_t", cbs("1.6 mm"), "mm", "slot ceiling thickness")
    up.add("sn_g_float", cbs("0.3 mm"), "mm", "roller float gap")
    up.add("sn_roll_d", cbs("8 mm"), "mm", "roller dia")
    up.add("sn_cap_ch", cbs("0.4 mm"), "mm", "cap rim chamfer")
    up.add("sn_fuse_ch", cbs("0.3 mm"), "mm", "anti-fuse chamfer")
    print("FH params added")

    # ---- stator (revolve) ---------------------------------------------
    sks = root.sketches.add(root.xZConstructionPlane)
    sks.name = "stator_profile"
    _polyline(sks, pt, [
        (0.0, 0.0), (CAP_R, 0.0), (CAP_R, 0.25), (JR, 0.25),
        (JR, RIDGE_Z[0]), (RIDGE_R, RIDGE_Z[1]), (JR, RIDGE_Z[2]),
        (JR, 1.15), (CAP_R, 1.15), (CAP_R, H), (0.0, H),
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
    stator.name = "sn_stator"
    if not (5.5 < stator.volume < 7.5):
        raise RuntimeError("stator vol %.3f" % stator.volume)
    print("FH stator vol: %.3f" % stator.volume)

    # finger dimples, both cap faces (revolve cuts about the main axis)
    for z_face, z_apex in ((H, H - DIMPLE_DEPTH), (0.0, DIMPLE_DEPTH)):
        adsk.doEvents()
        skd = root.sketches.add(root.xZConstructionPlane)
        skd.name = "dimple_%s" % ("top" if z_face > 0.5 else "bottom")
        zc = z_apex + SPH_R if z_face < 0.5 else z_apex - SPH_R
        # mid point of arc between rim (DIMPLE_RIM, z_face) and apex
        va = (0.0, z_apex - zc)
        vb = (DIMPLE_RIM, z_face - zc)
        ms = (va[0] + vb[0], va[1] + vb[1])
        mn = math.hypot(ms[0], ms[1])
        mid = (SPH_R * ms[0] / mn, zc + SPH_R * ms[1] / mn)
        dl = skd.sketchCurves.sketchLines
        ax_ln = dl.addByTwoPoints(
            skd.modelToSketchSpace(pt(0, 0, z_apex)),
            skd.modelToSketchSpace(pt(0, 0, z_face)))
        face_ln = dl.addByTwoPoints(
            ax_ln.endSketchPoint,
            skd.modelToSketchSpace(pt(DIMPLE_RIM, 0, z_face)))
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
        dfeat = rev.add(di)
        dfeat.name = skd.name + "_cut"
        if v0 - stator.volume < 0.08:
            raise RuntimeError("dimple removed %.4f" % (v0 - stator.volume))
    print("FH dimples done, stator vol: %.3f" % stator.volume)

    # ---- rotor sleeve (revolve) ---------------------------------------
    skr = root.sketches.add(root.xZConstructionPlane)
    skr.name = "rotor_profile"
    _polyline(skr, pt, [
        (SLEEVE_R, 0.0), (CBORE_R, 0.0), (CBORE_R, CBORE_D),
        (BORE_R, CBORE_D), (BORE_R, RIDGE_Z[0]),
        (GROOVE_R, RIDGE_Z[1]), (BORE_R, RIDGE_Z[2]),
        (BORE_R, H - CBORE_D), (CBORE_R, H - CBORE_D), (CBORE_R, H),
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
    rotor.name = "sn_rotor"
    if not (3.0 < rotor.volume < 5.5):
        raise RuntimeError("rotor sleeve vol %.3f" % rotor.volume)
    print("FH rotor sleeve vol: %.3f" % rotor.volume)

    # ---- scalloped deck (fitted spline, joined) -----------------------
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
        raise RuntimeError("no deck annulus profile found")
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

    # ---- seed cuts at azimuth 90: slot cavity, ceiling window, sector -
    plc = ctx.plane_at_z("sn_floor_t", "cavity_floor_plane")
    skc = root.sketches.add(plc)
    skc.name = "slot_seed"
    _fixed_rect(skc, pt, -SLOT_W / 2, SLOT_RIN, SLOT_W / 2, SLOT_ROUT, 0.12)
    _fix_sketch(skc)
    fslot = ctx.blind_cut(ctx.all_profiles(skc), "sn_cavity_h", [rotor],
                          "slot", min_vol_cm3=1.2)
    fslot.name = "slot_seed_cut"

    plw = ctx.plane_at_z("14 mm", "roof_plane")
    skw = root.sketches.add(plw)
    skw.name = "window_seed"
    _fixed_rect(skw, pt, -WIN_W / 2, SLOT_RIN, WIN_W / 2, BAR_IN, 1.4)
    _fixed_rect(skw, pt, -WIN_W / 2, BAR_OUT, WIN_W / 2, SLOT_ROUT, 1.4)
    _fix_sketch(skw)
    fwin = ctx.blind_cut(ctx.all_profiles(skw), "sn_ceiling_t", [rotor],
                         "window", min_vol_cm3=0.08)
    fwin.name = "window_seed_cut"

    sksec = root.sketches.add(root.xYConstructionPlane)
    sksec.name = "sector_seed"
    az = math.radians(120)
    a0, a1 = az - math.radians(SECT_HALF), az + math.radians(SECT_HALF)
    sl = sksec.sketchCurves.sketchLines
    sa = sksec.sketchCurves.sketchArcs
    p_in0 = pt(SECT_RIN * math.cos(a0), SECT_RIN * math.sin(a0), 0)
    p_out0 = pt(SECT_ROUT * math.cos(a0), SECT_ROUT * math.sin(a0), 0)
    p_out1 = pt(SECT_ROUT * math.cos(a1), SECT_ROUT * math.sin(a1), 0)
    p_in1 = pt(SECT_RIN * math.cos(a1), SECT_RIN * math.sin(a1), 0)
    l1 = sl.addByTwoPoints(sksec.modelToSketchSpace(p_in0),
                           sksec.modelToSketchSpace(p_out0))
    mid_out = pt(SECT_ROUT * math.cos(az), SECT_ROUT * math.sin(az), 0)
    arc1 = sa.addByThreePoints(l1.endSketchPoint,
                               sksec.modelToSketchSpace(mid_out),
                               sksec.modelToSketchSpace(p_out1))
    l2 = sl.addByTwoPoints(arc1.endSketchPoint,
                           sksec.modelToSketchSpace(p_in1))
    mid_in = pt(SECT_RIN * math.cos(az), SECT_RIN * math.sin(az), 0)
    sa.addByThreePoints(l2.endSketchPoint,
                        sksec.modelToSketchSpace(mid_in),
                        l1.startSketchPoint)
    _fix_sketch(sksec)
    if sksec.profiles.count != 1:
        raise RuntimeError("sector profiles %d" % sksec.profiles.count)
    fsec = ctx.blind_cut(ctx.all_profiles(sksec), "15 mm", [rotor],
                         "sector", min_vol_cm3=0.7)
    fsec.name = "sector_seed_cut"
    print("FH seed cuts done, rotor vol: %.3f" % rotor.volume)

    # ---- pattern the three cuts x6 ------------------------------------
    v2 = rotor.volume
    coll = adsk.core.ObjectCollection.create()
    coll.add(fslot)
    coll.add(fwin)
    coll.add(fsec)
    cpats = root.features.circularPatternFeatures
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
    print("FH cut pattern done, rotor vol: %.3f" % rotor.volume)

    # ---- roller seed + chamfers + body pattern x6 ---------------------
    plr = ctx.plane_at_z("sn_floor_t + sn_g_float", "roller_floor_plane")
    skro = root.sketches.add(plr)
    skro.name = "roller_seed"
    ctx.bound_circle(skro, (0, ROLL_REST, 0.15), 0.4, "sn_roll_d",
                     x_pos="0 mm", v_pos="20.5 mm")

    def roller_ok(b):
        bb = b.boundingBox
        return (0.4 < b.volume < 0.65 and
                abs((bb.maxPoint.y + bb.minPoint.y) / 2 - ROLL_REST) < 0.05)

    fro, roller = ctx.checked_newbody(ctx.all_profiles(skro), "10.4 mm",
                                      roller_ok, "roller")
    fro.name = "roller_extrude"
    roller.name = "sn_roller_1"

    chf = root.features.chamferFeatures
    rends = adsk.core.ObjectCollection.create()
    for e in roller.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
        g = e.geometry
        r = getattr(g, "radius", None)
        if r is not None and 0.35 < r < 0.45:
            rends.add(e)
    if rends.count != 2:
        raise RuntimeError("roller end edges %d != 2" % rends.count)
    ci0 = chf.createInput2()
    ci0.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        rends, cbs("sn_fuse_ch"), True)
    cf0 = chf.add(ci0)
    cf0.name = "roller_end_chamfer"

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
        pfb.bodies.item(i).name = "sn_roller_%d" % (i + 2)
    print("FH rollers done: %d bodies" % root.bRepBodies.count)

    # ---- chamfers: cap rims 0.4, rotor anti-fuse 0.3 ------------------
    def circle_edges(bod, lo, hi, z_targets):
        out = adsk.core.ObjectCollection.create()
        for e in bod.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            g = e.geometry
            r = getattr(g, "radius", None)
            if r is None or not (lo < r < hi):
                continue
            bb = e.boundingBox
            if abs(bb.maxPoint.z - bb.minPoint.z) > 0.02:
                continue
            if any(abs(bb.minPoint.z - zt) < 0.02 for zt in z_targets):
                out.add(e)
        return out

    caps = circle_edges(stator, 1.25, 1.35, (0.0, H))
    if caps.count != 2:
        raise RuntimeError("cap rim edges %d != 2" % caps.count)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        caps, cbs("sn_cap_ch"), True)
    c1 = chf.add(ci)
    c1.name = "cap_rim_chamfer"

    fuse = circle_edges(rotor, 1.30, 1.38, (0.0,))
    if fuse.count != 1:
        raise RuntimeError("anti-fuse edges %d != 1" % fuse.count)
    ci2 = chf.createInput2()
    ci2.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        fuse, cbs("sn_fuse_ch"), True)
    c2 = chf.add(ci2)
    c2.name = "rotor_antifuse_chamfer"

    print("FH BUILD OK: stator %.3f rotor %.3f roller %.3f cm3, "
          "%d bodies"
          % (stator.volume, rotor.volume, roller.volume,
             root.bRepBodies.count))
