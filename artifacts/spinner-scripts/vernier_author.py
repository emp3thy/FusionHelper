"""Vernier Contra-Ring - two-rotor coaxial ring spinner (rank 3).

Rotor A: hub with 608 through-seat, 36-slot web, outer wall carrying a
45-degree annular diamond ridge. Rotor B: heavy outer flywheel ring
printed in place around A (0.5 mm joint), 30-window vernier band, solid
rim, 12 OD scallops. Counter-spun, 36 vs 30 slots beat a 6-node moire.
Plus two press-fit caps.

v1 deviations from spec (documented): 6 top-face dome nubs omitted
(cosmetic finger pads); bottom 0.5 chamfers left to slicer elephant-foot
compensation (chamfering post-pattern outlines died with
ASM_BL_CAP_COMPLEX on the Comet build).
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["vr_seat_d", "vr_lead", "vr_slot_w", "vr_win_w",
                    "vr_stem_d"],
}
INTERFERENCE_ALLOWED = []

# Fixed art constants (cm).
T = 0.8
A_OUT = 2.7        # rotor A outer wall radius
RIDGE_APEX = 2.9
B_BORE = 2.75      # rotor B bore (0.5 mm radial joint gap)
B_OUT = 4.3
WIN_RIN, WIN_ROUT = 3.0, 3.9
SLOT_RIN, SLOT_ROUT = 1.6, 2.55
SCALLOP_R = 0.8    # scallop cutter radius (8 mm chord radius)
SCALLOP_POS = 4.9  # cutter centre radius -> 2 mm deep notch
CAP_X = 6.0

HEALTHY = None  # set in run() (needs adsk at runtime)


def _annulus_profile(sk, area_lo, area_hi):
    for p in sk.profiles:
        a = p.areaProperties().area
        if area_lo < a < area_hi:
            return p
    raise RuntimeError("no profile with area in (%.1f, %.1f)"
                       % (area_lo, area_hi))


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


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    up.add("vr_seat_d", cbs("21.9 mm"), "mm", "608 through-seat dia")
    up.add("vr_lead", cbs("0.5 mm"), "mm", "seat lead chamfer")
    up.add("vr_slot_w", cbs("1.6 mm"), "mm", "rotor A slot width")
    up.add("vr_win_w", cbs("2.2 mm"), "mm", "rotor B window width")
    up.add("vr_stem_d", cbs("8.1 mm"), "mm", "cap stem dia")
    print("FH params added")

    def circ_pattern_cut(feat, n, watch, min_dv, name):
        v0 = watch.volume
        coll = adsk.core.ObjectCollection.create()
        coll.add(feat)
        cpats = root.features.circularPatternFeatures
        pinp = cpats.createInput(coll, root.zConstructionAxis)
        pinp.quantity = cbs(str(n))
        pinp.totalAngle = cbs("360 deg")
        pinp.isSymmetric = False
        popts = adsk.fusion.PatternComputeOptions
        pinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
        pf = cpats.add(pinp)
        if pf.healthState not in healthy or v0 - watch.volume < min_dv:
            raise RuntimeError("%s pattern invalid dv=%.4f"
                               % (name, v0 - watch.volume))
        pf.name = name
        return pf

    # ---- rotor A: annulus + ridge -------------------------------------
    ska = root.sketches.add(root.xYConstructionPlane)
    ska.name = "rotor_a_annulus"
    ctx.bound_circle(ska, (0, 0, 0), 1.095, "vr_seat_d",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(ska, (0, 0, 0), A_OUT, "54 mm",
                     x_pos="0 mm", v_pos="0 mm")
    prof_a = _annulus_profile(ska, 15.0, 22.0)
    inp = ctx.extrudes.createInput(prof_a, ctx.ops.NewBodyFeatureOperation)
    ext = adsk.fusion.DistanceExtentDefinition.create(cbs("8 mm"))
    inp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
    fa = ctx.extrudes.add(inp)
    fa.name = "rotor_a_extrude"
    rotor_a = fa.bodies.item(0)
    rotor_a.name = "vernier_rotor_a"

    skr = root.sketches.add(root.xZConstructionPlane)
    skr.name = "ridge_profile"
    rpts = [(A_OUT, 0.2), (RIDGE_APEX, 0.4), (A_OUT, 0.6)]
    spts = [skr.modelToSketchSpace(pt(x, 0, z)) for x, z in rpts]
    rl = skr.sketchCurves.sketchLines
    l1 = rl.addByTwoPoints(spts[0], spts[1])
    l2 = rl.addByTwoPoints(l1.endSketchPoint, spts[2])
    rl.addByTwoPoints(l2.endSketchPoint, l1.startSketchPoint)
    _fix_sketch(skr)
    if skr.profiles.count != 1:
        raise RuntimeError("ridge profiles %d" % skr.profiles.count)
    v0 = rotor_a.volume
    rev = root.features.revolveFeatures
    rinp = rev.createInput(skr.profiles.item(0), root.zConstructionAxis,
                           ctx.ops.JoinFeatureOperation)
    rinp.setAngleExtent(False, cbs("360 deg"))
    rinp.participantBodies = [rotor_a]
    rfj = rev.add(rinp)
    rfj.name = "ridge_join"
    if rotor_a.volume - v0 < 0.2:
        raise RuntimeError("ridge added %.4f cm3" % (rotor_a.volume - v0))
    print("FH rotor A + ridge vol: %.3f" % rotor_a.volume)

    # ---- rotor A slots (seed + pattern x36) ---------------------------
    sks = root.sketches.add(root.xYConstructionPlane)
    sks.name = "slot_seed"
    mid = (SLOT_RIN + SLOT_ROUT) / 2
    ctx.bound_rect2(sks, (0, mid, 0), 0.08, (SLOT_ROUT - SLOT_RIN) / 2,
                    u_size="vr_slot_w", v_size="9.5 mm",
                    u_pos=("0 mm", "vr_slot_w / 2"),
                    v_pos=("%.2f mm" % (mid * 10), "4.75 mm"))
    fslot = ctx.blind_cut(ctx.all_profiles(sks), "9 mm", [rotor_a],
                          "slot", min_vol_cm3=0.05)
    fslot.name = "slot_seed_cut"
    circ_pattern_cut(fslot, 36, rotor_a, 3.0, "slot_pattern")
    print("FH slots done vol: %.3f" % rotor_a.volume)

    # ---- rotor B: annulus + groove ------------------------------------
    skb = root.sketches.add(root.xYConstructionPlane)
    skb.name = "rotor_b_annulus"
    ctx.bound_circle(skb, (0, 0, 0), B_BORE, "55 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skb, (0, 0, 0), B_OUT, "86 mm",
                     x_pos="0 mm", v_pos="0 mm")
    prof_b = _annulus_profile(skb, 30.0, 40.0)
    inp2 = ctx.extrudes.createInput(prof_b, ctx.ops.NewBodyFeatureOperation)
    ext2 = adsk.fusion.DistanceExtentDefinition.create(cbs("8 mm"))
    inp2.setOneSideExtent(ext2, ctx.dirs.PositiveExtentDirection)
    fbx = ctx.extrudes.add(inp2)
    fbx.name = "rotor_b_extrude"
    rotor_b = fbx.bodies.item(0)
    rotor_b.name = "vernier_rotor_b"

    skg = root.sketches.add(root.xZConstructionPlane)
    skg.name = "groove_profile"
    off = 0.05 / math.sin(math.radians(45))   # 0.5 mm normal offset
    gpts = [(B_BORE, 0.4 - 0.2 - off), (RIDGE_APEX + off, 0.4),
            (B_BORE, 0.4 + 0.2 + off)]
    gspts = [skg.modelToSketchSpace(pt(x, 0, z)) for x, z in gpts]
    gl = skg.sketchCurves.sketchLines
    g1 = gl.addByTwoPoints(gspts[0], gspts[1])
    g2 = gl.addByTwoPoints(g1.endSketchPoint, gspts[2])
    gl.addByTwoPoints(g2.endSketchPoint, g1.startSketchPoint)
    _fix_sketch(skg)
    if skg.profiles.count != 1:
        raise RuntimeError("groove profiles %d" % skg.profiles.count)
    v1 = rotor_b.volume
    rinp2 = rev.createInput(skg.profiles.item(0), root.zConstructionAxis,
                            ctx.ops.CutFeatureOperation)
    rinp2.setAngleExtent(False, cbs("360 deg"))
    rinp2.participantBodies = [rotor_b]
    rfg = rev.add(rinp2)
    rfg.name = "groove_cut"
    if v1 - rotor_b.volume < 0.2:
        raise RuntimeError("groove removed %.4f" % (v1 - rotor_b.volume))
    print("FH rotor B + groove vol: %.3f" % rotor_b.volume)

    # ---- rotor B windows (seed + pattern x30) -------------------------
    skw = root.sketches.add(root.xYConstructionPlane)
    skw.name = "window_seed"
    wmid = (WIN_RIN + WIN_ROUT) / 2
    ctx.bound_rect2(skw, (0, wmid, 0), 0.11, (WIN_ROUT - WIN_RIN) / 2,
                    u_size="vr_win_w", v_size="9 mm",
                    u_pos=("0 mm", "vr_win_w / 2"),
                    v_pos=("%.2f mm" % (wmid * 10), "4.5 mm"))
    fwin = ctx.blind_cut(ctx.all_profiles(skw), "9 mm", [rotor_b],
                         "window", min_vol_cm3=0.08)
    fwin.name = "window_seed_cut"
    circ_pattern_cut(fwin, 30, rotor_b, 3.5, "window_pattern")
    print("FH windows done vol: %.3f" % rotor_b.volume)

    # ---- rotor B OD scallops (seed + pattern x12) ---------------------
    skc = root.sketches.add(root.xYConstructionPlane)
    skc.name = "scallop_seed"
    ctx.bound_circle(skc, (0, SCALLOP_POS, 0), SCALLOP_R, "16 mm",
                     x_pos="0 mm", v_pos="49 mm")
    fsc = ctx.blind_cut(ctx.all_profiles(skc), "9 mm", [rotor_b],
                        "scallop", min_vol_cm3=0.05)
    fsc.name = "scallop_seed_cut"
    circ_pattern_cut(fsc, 12, rotor_b, 0.5, "scallop_pattern")
    print("FH scallops done vol: %.3f" % rotor_b.volume)

    # ---- seat lead chamfers -------------------------------------------
    chf = root.features.chamferFeatures
    out = adsk.core.ObjectCollection.create()
    for e in rotor_a.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
        g = e.geometry
        r = getattr(g, "radius", None)
        if r is None or not (1.02 < r < 1.14):
            continue
        bb = e.boundingBox
        if (abs(bb.maxPoint.z - bb.minPoint.z) < 0.02 and
                (abs(bb.minPoint.z) < 0.02 or
                 abs(bb.maxPoint.z - T) < 0.02)):
            out.add(e)
    if out.count != 2:
        raise RuntimeError("seat edges %d != 2" % out.count)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        out, cbs("vr_lead"), True)
    cf = chf.add(ci)
    cf.name = "seat_lead_chamfer"

    # ---- caps ----------------------------------------------------------
    skd = root.sketches.add(root.xYConstructionPlane)
    skd.name = "cap_discs"
    ctx.bound_circle(skd, (CAP_X, 0, 0), 1.0, "20 mm",
                     x_pos="60 mm", v_pos="0 mm")
    ctx.bound_circle(skd, (-CAP_X, 0, 0), 1.0, "20 mm",
                     x_pos="60 mm", v_pos="0 mm")
    dinp = ctx.extrudes.createInput(ctx.all_profiles(skd),
                                    ctx.ops.NewBodyFeatureOperation)
    exd = adsk.fusion.DistanceExtentDefinition.create(cbs("4 mm"))
    dinp.setOneSideExtent(exd, ctx.dirs.PositiveExtentDirection)
    fd = ctx.extrudes.add(dinp)
    fd.name = "cap_discs_extrude"
    caps = [fd.bodies.item(i) for i in range(fd.bodies.count)]
    if len(caps) != 2:
        raise RuntimeError("caps %d != 2" % len(caps))
    caps[0].name = "cap_a"
    caps[1].name = "cap_b"

    plb = ctx.plane_at_z("4 mm", "cap_boss_plane")
    skbo = root.sketches.add(plb)
    skbo.name = "cap_bosses"
    ctx.bound_circle(skbo, (CAP_X, 0, 0.4), 0.575, "11.5 mm",
                     x_pos="60 mm", v_pos="0 mm")
    ctx.bound_circle(skbo, (-CAP_X, 0, 0.4), 0.575, "11.5 mm",
                     x_pos="60 mm", v_pos="0 mm")
    vb0 = sum(b.volume for b in caps)
    binp = ctx.extrudes.createInput(ctx.all_profiles(skbo),
                                    ctx.ops.JoinFeatureOperation)
    exb = adsk.fusion.DistanceExtentDefinition.create(cbs("0.7 mm"))
    binp.setOneSideExtent(exb, ctx.dirs.PositiveExtentDirection)
    binp.participantBodies = caps
    fbos = ctx.extrudes.add(binp)
    fbos.name = "cap_boss_extrude"
    if sum(b.volume for b in caps) - vb0 < 0.1:
        raise RuntimeError("boss join too small")

    pls = ctx.plane_at_z("4 mm + 0.7 mm", "cap_stem_plane")
    skst = root.sketches.add(pls)
    skst.name = "cap_stems"
    ctx.bound_circle(skst, (CAP_X, 0, 0.47), 0.405, "vr_stem_d",
                     x_pos="60 mm", v_pos="0 mm")
    ctx.bound_circle(skst, (-CAP_X, 0, 0.47), 0.405, "vr_stem_d",
                     x_pos="60 mm", v_pos="0 mm")
    vb1 = sum(b.volume for b in caps)
    sinp = ctx.extrudes.createInput(ctx.all_profiles(skst),
                                    ctx.ops.JoinFeatureOperation)
    exs = adsk.fusion.DistanceExtentDefinition.create(cbs("3.4 mm"))
    sinp.setOneSideExtent(exs, ctx.dirs.PositiveExtentDirection)
    sinp.participantBodies = caps
    fst = ctx.extrudes.add(sinp)
    fst.name = "cap_stem_extrude"
    if sum(b.volume for b in caps) - vb1 < 0.2:
        raise RuntimeError("stem join too small")

    print("FH BUILD OK: A %.3f + B %.3f cm3, %d bodies"
          % (rotor_a.volume, rotor_b.volume, root.bRepBodies.count))
