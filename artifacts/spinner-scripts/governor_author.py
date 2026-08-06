"""The Governor - centrifugal variable-inertia spinner (rank 4).

88 x 12 mm closed-rim disc, 608 bearing pocket with retaining shoulder,
three radial T-slot channels at 120 deg each holding a print-in-place
slider that carries a captive M8 nut. Sliders park inboard; past ~5
rev/s they fly outward - inertia jumps ~25%, the spin note drops.

v1 deviations (documented): 0.3 mm channel detents omitted (sliders
free-slide; snap threshold lost, rattle kept); grip buttons flat-topped
instead of dished; bottom chamfers left to slicer. Slider vertical
stack: 0.1 mm floor gap, 0.3 mm gap under the T-slot lip bridge (the
print-critical one).
"""
import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["gv_seat_d", "gv_pocket_depth", "gv_lead",
                    "gv_chamf_top", "gv_stub_d"],
}
INTERFERENCE_ALLOWED = []

# Fixed art constants (cm).
T = 1.2
BODY_R = 4.4
CH_RIN, CH_ROUT = 1.4, 4.2
BLOCK_Z0 = 0.21
BLOCK_H = 0.66
TOWER_H = 0.30
NUT_AF = 1.29
CAP_X = 6.5


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


def _fixed_rect(sk, pt, x0, y0, x1, y1, z):
    """Fixed-art rectangle at exact model coordinates. bound_rect2 is
    unusable for centre-0 rects: its corner dim expression evaluates
    negative and the solver snaps the corner positive, shifting the rect
    sideways by its full width (probe-confirmed)."""
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
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    up.add("gv_seat_d", cbs("21.85 mm"), "mm", "608 pocket dia")
    up.add("gv_pocket_depth", cbs("7.2 mm"), "mm", "bearing pocket depth")
    up.add("gv_lead", cbs("0.5 mm"), "mm", "pocket lead chamfer")
    up.add("gv_chamf_top", cbs("2 mm"), "mm", "top rim chamfer")
    up.add("gv_stub_d", cbs("8.05 mm"), "mm", "button peg dia")
    print("FH params added")

    # ---- body disc -----------------------------------------------------
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.name = "body_disc"
    ctx.bound_circle(sk, (0, 0, 0), BODY_R, "88 mm",
                     x_pos="0 mm", v_pos="0 mm")

    def body_ok(b):
        return b.boundingBox.maxPoint.z > 1.1 and 65.0 < b.volume < 80.0

    f, body = ctx.checked_newbody(ctx.all_profiles(sk), "12 mm",
                                  body_ok, "gov_body")
    f.name = "body_extrude"
    body.name = "governor_body"

    # ---- bearing bore: through 19 + pocket from top -------------------
    skb = root.sketches.add(root.xYConstructionPlane)
    skb.name = "through_bore"
    circ = skb.sketchCurves.sketchCircles.addByCenterRadius(
        pt(0.05, 0.08, 0), 0.95)
    skb.geometricConstraints.addCoincident(
        circ.centerSketchPoint, skb.originPoint)
    dd = skb.sketchDimensions.addDiameterDimension(circ, pt(1.5, -1.5, 0))
    dd.parameter.expression = "19 mm"
    fb = ctx.blind_cut(ctx.all_profiles(skb), "13 mm", [body],
                       "bore", min_vol_cm3=2.5)
    fb.name = "through_bore_cut"

    plp = ctx.plane_at_z("12 mm", "top_plane")
    skp = root.sketches.add(plp)
    skp.name = "bearing_pocket"
    circ2 = skp.sketchCurves.sketchCircles.addByCenterRadius(
        pt(0.06, 0.09, 0), 1.0925)
    skp.geometricConstraints.addCoincident(
        circ2.centerSketchPoint, skp.originPoint)
    dd2 = skp.sketchDimensions.addDiameterDimension(circ2, pt(1.7, -1.7, 0))
    dd2.parameter.expression = "gv_seat_d"
    fp = ctx.blind_cut(ctx.all_profiles(skp), "gv_pocket_depth", [body],
                       "pocket", min_vol_cm3=0.4)
    fp.name = "bearing_pocket_cut"
    print("FH bore+pocket vol: %.3f" % body.volume)

    # ---- channel seed (base slot + top opening) at 90 deg -------------
    pls = ctx.plane_at_z("2 mm", "slot_floor_plane")
    sks = root.sketches.add(pls)
    sks.name = "slot_seed"
    _fixed_rect(sks, pt, -1.0, CH_RIN, 1.0, CH_ROUT, 0.2)
    _fix_sketch(sks)
    fslot = ctx.blind_cut(ctx.all_profiles(sks), "7 mm", [body],
                          "slot", min_vol_cm3=3.0)
    fslot.name = "slot_seed_cut"

    plo = ctx.plane_at_z("9 mm", "lip_plane")
    sko = root.sketches.add(plo)
    sko.name = "opening_seed"
    _fixed_rect(sko, pt, -0.77, CH_RIN, 0.77, CH_ROUT, 0.9)
    _fix_sketch(sko)
    fop = ctx.blind_cut(ctx.all_profiles(sko), "3.5 mm", [body],
                        "opening", min_vol_cm3=1.0)
    fop.name = "opening_seed_cut"
    print("FH channel seed vol: %.3f" % body.volume)

    v0 = body.volume
    coll = adsk.core.ObjectCollection.create()
    coll.add(fslot)
    coll.add(fop)
    cpats = root.features.circularPatternFeatures
    pinp = cpats.createInput(coll, root.zConstructionAxis)
    pinp.quantity = cbs("3")
    pinp.totalAngle = cbs("360 deg")
    pinp.isSymmetric = False
    popts = adsk.fusion.PatternComputeOptions
    pinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pfc = cpats.add(pinp)
    if pfc.healthState not in healthy or v0 - body.volume < 8.0:
        raise RuntimeError("channel pattern dv=%.3f" % (v0 - body.volume))
    pfc.name = "channel_pattern"
    print("FH channels done vol: %.3f" % body.volume)

    # ---- slider (block + tower + nut pocket), then body pattern x3 ----
    plb = ctx.plane_at_z("2.1 mm", "slider_floor_plane")
    skbl = root.sketches.add(plb)
    skbl.name = "slider_block"
    _fixed_rect(skbl, pt, -0.965, 1.5, 0.965, 3.3, BLOCK_Z0)
    _fix_sketch(skbl)

    def block_ok(b):
        bb = b.boundingBox
        return (bb.maxPoint.z > 0.8 and 2.0 < b.volume < 2.6 and
                abs(bb.maxPoint.x + bb.minPoint.x) < 0.05 and
                abs((bb.maxPoint.y + bb.minPoint.y) / 2 - 2.4) < 0.05)

    fbl, slider = ctx.checked_newbody(ctx.all_profiles(skbl), "6.6 mm",
                                      block_ok, "slider_block")
    fbl.name = "slider_block_extrude"
    slider.name = "gov_slider_a"

    plt = ctx.plane_at_z("2.1 mm + 6.6 mm", "slider_top_plane")
    sktw = root.sketches.add(plt)
    sktw.name = "slider_tower"
    _fixed_rect(sktw, pt, -0.735, 1.5, 0.735, 3.3, 0.87)
    _fix_sketch(sktw)
    vs0 = slider.volume
    tinp = ctx.extrudes.createInput(ctx.all_profiles(sktw),
                                    ctx.ops.JoinFeatureOperation)
    ext = adsk.fusion.DistanceExtentDefinition.create(cbs("3 mm"))
    tinp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
    tinp.participantBodies = [slider]
    ftw = ctx.extrudes.add(tinp)
    ftw.name = "slider_tower_extrude"
    if slider.volume - vs0 < 0.5:
        raise RuntimeError("tower join %.3f" % (slider.volume - vs0))

    # hex nut pocket, cut down from the tower top
    import math as _m
    plh = ctx.plane_at_z("2.1 mm + 6.6 mm + 3 mm", "nut_pocket_plane")
    skh = root.sketches.add(plh)
    skh.name = "nut_pocket"
    rc = NUT_AF / _m.sqrt(3.0)
    vpts = []
    for m in range(6):
        va = _m.radians(90 + 60 * m)
        vpts.append(skh.modelToSketchSpace(
            pt(rc * _m.cos(va), 2.4 + rc * _m.sin(va), 1.17)))
    lines = skh.sketchCurves.sketchLines
    first = lines.addByTwoPoints(vpts[0], vpts[1])
    prev = first
    for m in range(2, 7):
        adsk.doEvents()
        if m < 6:
            prev = lines.addByTwoPoints(prev.endSketchPoint, vpts[m])
        else:
            prev = lines.addByTwoPoints(prev.endSketchPoint,
                                        first.startSketchPoint)
    _fix_sketch(skh)
    if skh.profiles.count != 1:
        raise RuntimeError("hex profiles %d" % skh.profiles.count)
    fh = ctx.blind_cut(ctx.all_profiles(skh), "6.9 mm", [slider],
                       "nutpocket", min_vol_cm3=0.6)
    fh.name = "nut_pocket_cut"
    print("FH slider vol: %.3f" % slider.volume)

    # body pattern x3 (no compute option: body patterns reject it)
    bcoll = adsk.core.ObjectCollection.create()
    bcoll.add(slider)
    n_before = root.bRepBodies.count
    pinp2 = cpats.createInput(bcoll, root.zConstructionAxis)
    pinp2.quantity = cbs("3")
    pinp2.totalAngle = cbs("360 deg")
    pinp2.isSymmetric = False
    pfs = cpats.add(pinp2)
    if (pfs.healthState not in healthy or
            root.bRepBodies.count - n_before != 2):
        raise RuntimeError("slider pattern bodies %d"
                           % (root.bRepBodies.count - n_before))
    pfs.name = "slider_pattern"
    for i in range(pfs.bodies.count):
        pfs.bodies.item(i).name = "gov_slider_%s" % ("bc"[i] if i < 2
                                                     else str(i))
    print("FH sliders patterned: %d bodies" % root.bRepBodies.count)

    # ---- chamfers ------------------------------------------------------
    chf = root.features.chamferFeatures

    def circle_edges(bod, lo, hi, z_at):
        out = adsk.core.ObjectCollection.create()
        for e in bod.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            g = e.geometry
            r = getattr(g, "radius", None)
            if r is None or not (lo < r < hi):
                continue
            bb = e.boundingBox
            if (abs(bb.maxPoint.z - bb.minPoint.z) < 0.02 and
                    abs(bb.minPoint.z - z_at) < 0.02):
                out.add(e)
        return out

    top_rim = circle_edges(body, 4.3, 4.5, T)
    if top_rim.count != 1:
        raise RuntimeError("top rim edges %d != 1" % top_rim.count)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        top_rim, cbs("gv_chamf_top"), True)
    c1 = chf.add(ci)
    c1.name = "top_rim_chamfer"

    mouth = circle_edges(body, 1.02, 1.14, T)
    if mouth.count != 1:
        raise RuntimeError("pocket mouth edges %d != 1" % mouth.count)
    ci2 = chf.createInput2()
    ci2.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        mouth, cbs("gv_lead"), True)
    c2 = chf.add(ci2)
    c2.name = "pocket_lead_chamfer"
    print("FH chamfers done")

    # ---- buttons -------------------------------------------------------
    skd = root.sketches.add(root.xYConstructionPlane)
    skd.name = "button_discs"
    ctx.bound_circle(skd, (CAP_X, 0, 0), 1.0, "20 mm",
                     x_pos="65 mm", v_pos="0 mm")
    ctx.bound_circle(skd, (-CAP_X, 0, 0), 1.0, "20 mm",
                     x_pos="65 mm", v_pos="0 mm")
    dinp = ctx.extrudes.createInput(ctx.all_profiles(skd),
                                    ctx.ops.NewBodyFeatureOperation)
    exd = adsk.fusion.DistanceExtentDefinition.create(cbs("3 mm"))
    dinp.setOneSideExtent(exd, ctx.dirs.PositiveExtentDirection)
    fd = ctx.extrudes.add(dinp)
    fd.name = "button_discs_extrude"
    btns = [fd.bodies.item(i) for i in range(fd.bodies.count)]
    if len(btns) != 2:
        raise RuntimeError("buttons %d != 2" % len(btns))
    btns[0].name = "button_a"
    btns[1].name = "button_b"

    plbo = ctx.plane_at_z("3 mm", "button_boss_plane")
    skbo = root.sketches.add(plbo)
    skbo.name = "button_bosses"
    ctx.bound_circle(skbo, (CAP_X, 0, 0.3), 0.6, "12 mm",
                     x_pos="65 mm", v_pos="0 mm")
    ctx.bound_circle(skbo, (-CAP_X, 0, 0.3), 0.6, "12 mm",
                     x_pos="65 mm", v_pos="0 mm")
    vb0 = sum(b.volume for b in btns)
    binp = ctx.extrudes.createInput(ctx.all_profiles(skbo),
                                    ctx.ops.JoinFeatureOperation)
    exb = adsk.fusion.DistanceExtentDefinition.create(cbs("0.5 mm"))
    binp.setOneSideExtent(exb, ctx.dirs.PositiveExtentDirection)
    binp.participantBodies = btns
    fbo = ctx.extrudes.add(binp)
    fbo.name = "button_boss_extrude"
    if sum(b.volume for b in btns) - vb0 < 0.08:
        raise RuntimeError("boss join too small")

    plpe = ctx.plane_at_z("3 mm + 0.5 mm", "button_peg_plane")
    skpe = root.sketches.add(plpe)
    skpe.name = "button_pegs"
    ctx.bound_circle(skpe, (CAP_X, 0, 0.35), 0.4, "gv_stub_d",
                     x_pos="65 mm", v_pos="0 mm")
    ctx.bound_circle(skpe, (-CAP_X, 0, 0.35), 0.4, "gv_stub_d",
                     x_pos="65 mm", v_pos="0 mm")
    vb1 = sum(b.volume for b in btns)
    sinp = ctx.extrudes.createInput(ctx.all_profiles(skpe),
                                    ctx.ops.JoinFeatureOperation)
    exs = adsk.fusion.DistanceExtentDefinition.create(cbs("3.4 mm"))
    sinp.setOneSideExtent(exs, ctx.dirs.PositiveExtentDirection)
    sinp.participantBodies = btns
    fpe = ctx.extrudes.add(sinp)
    fpe.name = "button_peg_extrude"
    if sum(b.volume for b in btns) - vb1 < 0.2:
        raise RuntimeError("peg join too small")

    print("FH BUILD OK: body %.3f cm3, %d bodies total"
          % (body.volume, root.bRepBodies.count))
