"""Pulsar Bloom continuation: the build client timed out after the arm
merge committed (stator + rotor done, 32 timeline items); the planet
section never ran. This picks up exactly there: cleanup any partial
planet sketch, then planet gear + bore + puck + body pattern x4 +
anti-fuse chamfers. Never re-runs committed steps (double-build hazard).
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["pb_plate_t", "pb_arm_t", "pb_puck_h", "pb_fuse_ch"],
}
INTERFERENCE_ALLOWED = []

RING_N = 56
PL_N = 14
PL_TIP = 0.80
PL_ROOT = 0.575
PL_RP = 0.70
PL_RB = PL_RP * math.cos(math.radians(20))
BACKLASH = 0.012
STATION_R = 2.10
STUB_RIDGE_Z = (0.67, 0.73, 0.79)
PL_Z0 = 0.46
PL_BORE = 0.29
PL_GROOVE = 0.37
PL_BORE_TOP = 1.04
PUCK_R = 0.25
PUCK_OFF = 0.53


def _inv(a):
    return math.tan(a) - a


def _flank_angle(psi_p, rp, rb, r, internal):
    ap = math.acos(rb / rp)
    ar = math.acos(min(1.0, rb / max(r, rb)))
    if internal:
        return psi_p - _inv(ap) + _inv(ar)
    return psi_p + _inv(ap) - _inv(ar)


def _gear_outline(N, r_tip, r_root, rp, rb, psi_p, internal, phase):
    pts = []
    if internal:
        flank_rs = [r_root, (r_root + r_tip) / 2, r_tip]
    else:
        start = max(r_root, rb + 1e-4)
        flank_rs = [start, (start + r_tip) / 2, r_tip]
    for k in range(N):
        c = phase + 2 * math.pi * k / N
        pitch = 2 * math.pi / N
        psi_root = _flank_angle(psi_p, rp, rb, flank_rs[0], internal)
        pts.append((r_root * math.cos(c - pitch / 2),
                    r_root * math.sin(c - pitch / 2)))
        if not internal and r_root < rb:
            pts.append((r_root * math.cos(c - psi_root),
                        r_root * math.sin(c - psi_root)))
        for r in flank_rs:
            a = c - _flank_angle(psi_p, rp, rb, r, internal)
            pts.append((r * math.cos(a), r * math.sin(a)))
        for r in reversed(flank_rs):
            a = c + _flank_angle(psi_p, rp, rb, r, internal)
            pts.append((r * math.cos(a), r * math.sin(a)))
        if not internal and r_root < rb:
            pts.append((r_root * math.cos(c + psi_root),
                        r_root * math.sin(c + psi_root)))
    return pts


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
    pt = ctx.pt
    cbs = ctx.cbs
    rev = root.features.revolveFeatures
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    stator = root.bRepBodies.itemByName("pb_stator")
    rotor = root.bRepBodies.itemByName("pb_rotor")
    if stator is None or rotor is None:
        raise RuntimeError("expected pb_stator + pb_rotor present")
    if root.bRepBodies.count != 2:
        raise RuntimeError("expected exactly 2 bodies, got %d"
                           % root.bRepBodies.count)

    # cleanup: partial planet sketch from the killed run, if any
    for nm in ("planet_gear", "planet_bore", "puck"):
        sk_old = root.sketches.itemByName(nm)
        if sk_old is not None:
            sk_old.deleteMe()
            print("FH removed partial sketch", nm)

    # ---- planet gear ---------------------------------------------------
    skg = root.sketches.add(root.xYConstructionPlane)
    skg.name = "planet_gear"
    psi_pl = (math.pi / (2 * PL_N)
              + (2 * 0.03 * math.tan(math.radians(20))) / PL_N
              - BACKLASH / (2 * PL_RP))
    pl_pts = [(STATION_R + x, y) for x, y in _gear_outline(
        PL_N, PL_TIP, PL_ROOT, PL_RP, PL_RB, psi_pl, False, 0.0)]
    spts = [skg.modelToSketchSpace(pt(x, y, 0)) for x, y in pl_pts]
    lines = skg.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        if i % 16 == 0:
            adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    _fix_sketch(skg)
    if skg.profiles.count != 1:
        raise RuntimeError("planet profiles %d" % skg.profiles.count)
    ginp = ctx.extrudes.createInput(skg.profiles.item(0),
                                    ctx.ops.NewBodyFeatureOperation)
    ginp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        cbs("4.6 mm"))
    ext_g = adsk.fusion.DistanceExtentDefinition.create(cbs("6 mm"))
    ginp.setOneSideExtent(ext_g, ctx.dirs.PositiveExtentDirection)
    fpl = ctx.extrudes.add(ginp)
    fpl.name = "planet_extrude"
    planet = fpl.bodies.item(0)
    planet.name = "pb_planet_1"
    if not (0.5 < planet.volume < 1.2):
        raise RuntimeError("planet vol %.3f" % planet.volume)
    print("FH planet gear vol: %.3f" % planet.volume)

    # ---- blind bore + groove (revolve cut about the local axis) -------
    skpb = root.sketches.add(root.xZConstructionPlane)
    skpb.name = "planet_bore"
    rz = [
        (0.0, PL_Z0), (PL_BORE, PL_Z0),
        (PL_BORE, STUB_RIDGE_Z[0]), (PL_GROOVE, STUB_RIDGE_Z[1]),
        (PL_BORE, STUB_RIDGE_Z[2]), (PL_BORE, PL_BORE_TOP),
        (0.0, PL_BORE_TOP),
    ]
    bpts = [skpb.modelToSketchSpace(pt(STATION_R + r, 0, z))
            for r, z in rz]
    bl = skpb.sketchCurves.sketchLines
    bfirst = bl.addByTwoPoints(bpts[0], bpts[1])
    bprev = bfirst
    for i in range(2, len(bpts)):
        adsk.doEvents()
        bprev = bl.addByTwoPoints(bprev.endSketchPoint, bpts[i])
    bl.addByTwoPoints(bprev.endSketchPoint, bfirst.startSketchPoint)
    _fix_sketch(skpb)
    if skpb.profiles.count != 1:
        raise RuntimeError("bore profiles %d" % skpb.profiles.count)
    axis_line = None
    for ln in skpb.sketchCurves.sketchLines:
        s = skpb.sketchToModelSpace(ln.startSketchPoint.geometry)
        e = skpb.sketchToModelSpace(ln.endSketchPoint.geometry)
        if (abs(s.x - STATION_R) < 1e-4 and abs(e.x - STATION_R) < 1e-4
                and abs(s.y) < 1e-4 and abs(e.y) < 1e-4):
            axis_line = ln
            break
    if axis_line is None:
        raise RuntimeError("bore axis line not found")
    v0 = planet.volume
    binp = rev.createInput(skpb.profiles.item(0), axis_line,
                           ctx.ops.CutFeatureOperation)
    binp.setAngleExtent(False, cbs("360 deg"))
    binp.participantBodies = [planet]
    fb = rev.add(binp)
    fb.name = "planet_bore_cut"
    if v0 - planet.volume < 0.1:
        raise RuntimeError("bore removed %.4f" % (v0 - planet.volume))

    # ---- puck ----------------------------------------------------------
    skpk = root.sketches.add(root.xYConstructionPlane)
    skpk.name = "puck"
    ctx.bound_circle(skpk, (STATION_R + PUCK_OFF, 0, 0), PUCK_R, "5 mm",
                     x_pos="26.3 mm", v_pos="0 mm")
    v1 = planet.volume
    pinp = ctx.extrudes.createInput(ctx.all_profiles(skpk),
                                    ctx.ops.JoinFeatureOperation)
    pinp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        cbs("10.6 mm"))
    ext_p = adsk.fusion.DistanceExtentDefinition.create(cbs("pb_puck_h"))
    pinp.setOneSideExtent(ext_p, ctx.dirs.PositiveExtentDirection)
    pinp.participantBodies = [planet]
    fpk = ctx.extrudes.add(pinp)
    fpk.name = "puck_extrude"
    if planet.volume - v1 < 0.03:
        raise RuntimeError("puck added %.4f" % (planet.volume - v1))
    print("FH planet vol: %.3f" % planet.volume)

    # ---- body pattern x4 ----------------------------------------------
    bcoll = adsk.core.ObjectCollection.create()
    bcoll.add(planet)
    n_before = root.bRepBodies.count
    cpats = root.features.circularPatternFeatures
    pinp2 = cpats.createInput(bcoll, root.zConstructionAxis)
    pinp2.quantity = cbs("4")
    pinp2.totalAngle = cbs("360 deg")
    pinp2.isSymmetric = False
    pfb = cpats.add(pinp2)
    if (pfb.healthState not in healthy or
            root.bRepBodies.count - n_before != 3):
        raise RuntimeError("planet pattern bodies %d"
                           % (root.bRepBodies.count - n_before))
    pfb.name = "planet_pattern"
    for i in range(pfb.bodies.count):
        pfb.bodies.item(i).name = "pb_planet_%d" % (i + 2)
    print("FH planets done: %d bodies" % root.bRepBodies.count)

    # ---- anti-fuse chamfers -------------------------------------------
    chf = root.features.chamferFeatures
    out = adsk.core.ObjectCollection.create()
    for bod, lo, hi in ((stator, 3.25, 3.32), (rotor, 3.30, 3.38)):
        for e in bod.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            g = e.geometry
            r = getattr(g, "radius", None)
            if r is None or not (lo < r < hi):
                continue
            bb = e.boundingBox
            if (abs(bb.maxPoint.z - bb.minPoint.z) < 0.02 and
                    abs(bb.minPoint.z) < 0.02):
                out.add(e)
    if out.count != 2:
        raise RuntimeError("anti-fuse edges %d != 2" % out.count)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        out, cbs("pb_fuse_ch"), True)
    cf = chf.add(ci)
    cf.name = "antifuse_chamfer"

    print("FH BUILD OK: stator %.3f rotor %.3f planet %.3f cm3, %d bodies"
          % (stator.volume, rotor.volume, planet.volume,
             root.bRepBodies.count))
