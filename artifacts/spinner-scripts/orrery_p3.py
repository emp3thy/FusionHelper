"""ORRERY 90 - part 3: outer ring, roller slots, twin V-ways.

The outer ring reaches the build plate outboard of the stator base, so
the roller slots can run open from z0 to the full 14.5 mm - no ceiling,
no bridges, and the rollers are visible from above. Each slot carries a
through-throat at the bottom (so each roller's first layer prints on
glass) and two 45-degree V-ridges that capture the roller against
rattling. Slots sit at 0+72k, interleaved with the arms at 36+72k.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 5
FH_OPTS = {"liveness": False}
INTERFERENCE_ALLOWED = []

RING_RIN, RING_ROUT = 2.95, 4.50
SLOT_RIN, SLOT_ROUT = 2.95, 4.10     # race at r41, rim r41-45
SLOT_HALF = 0.35                     # 7.0 mm slot
THROAT_HALF = 0.23                   # 4.6 mm throat
RAIL_T = 0.12
VWAY_ZS = (0.45, 1.10)
RIDGE_TIP = 0.26                     # protrudes 0.9 mm off the wall
RIDGE_H = SLOT_HALF - RIDGE_TIP


def _fix_sketch(sk):
    for c in sk.sketchCurves:
        if not c.isFixed:
            c.isFixed = True
    for sp in sk.sketchPoints:
        if not (sp.isFullyConstrained or sp.isFixed):
            sp.isFixed = True
    adsk.doEvents()


def _fixed_rect(sk, pt, x0, y0, x1, y1, z):
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        sk.modelToSketchSpace(pt(x0, y0, z)),
        sk.modelToSketchSpace(pt(x1, y1, z)))


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    pt = ctx.pt
    cbs = ctx.cbs
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    rotor = root.bRepBodies.itemByName("or_rotor")
    if rotor is None or root.bRepBodies.count != 2:
        raise RuntimeError("expected or_stator + or_rotor from parts 1-2")
    print("FH P3 start, rotor %.3f" % rotor.volume)

    # ---- outer ring, reaching the plate outboard of the stator --------
    skr = root.sketches.add(root.xYConstructionPlane)
    skr.name = "outer_ring"
    ctx.bound_circle(skr, (0, 0, 0), RING_RIN, "59 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skr, (0, 0, 0), RING_ROUT, "90 mm",
                     x_pos="0 mm", v_pos="0 mm")
    prof = None
    for p in skr.profiles:
        a = p.areaProperties().area
        if 30.0 < a < 45.0:
            prof = p
            break
    if prof is None:
        raise RuntimeError("no outer ring annulus profile")
    v0 = rotor.volume
    rinp = ctx.extrudes.createInput(prof, ctx.ops.JoinFeatureOperation)
    rext = adsk.fusion.DistanceExtentDefinition.create(cbs("14.5 mm"))
    rinp.setOneSideExtent(rext, ctx.dirs.PositiveExtentDirection)
    rinp.participantBodies = [rotor]
    fring = ctx.extrudes.add(rinp)
    fring.name = "outer_ring_extrude"
    if rotor.volume - v0 < 40.0:
        raise RuntimeError("outer ring added %.3f" % (rotor.volume - v0))
    print("FH outer ring joined, rotor %.3f" % rotor.volume)

    # ---- slot cavity, open to the top ---------------------------------
    plc = ctx.plane_at_z("1.2 mm", "cavity_plane")
    skc = root.sketches.add(plc)
    skc.name = "slot_seed"
    _fixed_rect(skc, pt, -SLOT_HALF, SLOT_RIN, SLOT_HALF, SLOT_ROUT, RAIL_T)
    _fix_sketch(skc)
    fslot = ctx.blind_cut(ctx.all_profiles(skc), "14.5 mm - 1.2 mm",
                          [rotor], "slot", min_vol_cm3=1.0)
    fslot.name = "slot_seed_cut"

    # ---- through-throat: puts each roller's first layer on the plate --
    skt = root.sketches.add(root.xYConstructionPlane)
    skt.name = "throat_seed"
    _fixed_rect(skt, pt, -THROAT_HALF, SLOT_RIN, THROAT_HALF, SLOT_ROUT, 0.0)
    _fix_sketch(skt)
    fthr = ctx.blind_cut(ctx.all_profiles(skt), "1.2 mm", [rotor],
                         "throat", min_vol_cm3=0.04)
    fthr.name = "throat_seed_cut"

    # ---- twin 45-degree V-ridges along both slot walls ----------------
    skv = root.sketches.add(root.xZConstructionPlane)
    skv.name = "vway_ridge"
    for zc in VWAY_ZS:
        for sgn in (1, -1):
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
        raise RuntimeError("vway profiles %d != 4" % skv.profiles.count)
    v1 = rotor.volume
    vinp = ctx.extrudes.createInput(ctx.all_profiles(skv),
                                    ctx.ops.JoinFeatureOperation)
    vinp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        cbs("29.5 mm"))
    vext = adsk.fusion.DistanceExtentDefinition.create(cbs("11.5 mm"))
    vinp.setOneSideExtent(vext, ctx.dirs.PositiveExtentDirection)
    vinp.participantBodies = [rotor]
    fvway = ctx.extrudes.add(vinp)
    fvway.name = "vway_ridge_extrude"
    if rotor.volume - v1 < 0.01:
        raise RuntimeError("vway added %.4f" % (rotor.volume - v1))
    print("FH one slot + V-ways done, rotor %.3f" % rotor.volume)

    # ---- pattern cuts x5, then the ridges x5 --------------------------
    cpats = root.features.circularPatternFeatures
    popts = adsk.fusion.PatternComputeOptions
    v2 = rotor.volume
    ccoll = adsk.core.ObjectCollection.create()
    for f in (fslot, fthr):  # fusionhelper: allow R11 — collection add, not a document mutation
        ccoll.add(f)
    cinp = cpats.createInput(ccoll, root.zConstructionAxis)
    cinp.quantity = cbs("5")
    cinp.totalAngle = cbs("360 deg")
    cinp.isSymmetric = False
    cinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pfc = cpats.add(cinp)
    if pfc.healthState not in healthy or v2 - rotor.volume < 4.0:
        raise RuntimeError("slot pattern dv=%.3f" % (v2 - rotor.volume))
    pfc.name = "slot_pattern"

    v3 = rotor.volume
    vcoll = adsk.core.ObjectCollection.create()
    vcoll.add(fvway)
    vinp2 = cpats.createInput(vcoll, root.zConstructionAxis)
    vinp2.quantity = cbs("5")
    vinp2.totalAngle = cbs("360 deg")
    vinp2.isSymmetric = False
    vinp2.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pfv = cpats.add(vinp2)
    if pfv.healthState not in healthy or rotor.volume - v3 < 0.04:
        raise RuntimeError("vway pattern dv=%.4f" % (rotor.volume - v3))
    pfv.name = "vway_pattern"

    print("FH P3 OK: rotor %.3f cm3, %d bodies"
          % (rotor.volume, root.bRepBodies.count))
