"""ORRERY 90 - part 2: rotor inner structure.

Hub on the diamond journal, carrier, five planet stubs, five risers that
climb inboard of the ring-gear tooth tips, and five arms that reach over
the gear wall to meet the outer ring (built in part 3). Risers and arms
sit at 36+72k so they interleave with the roller slots at 0+72k - the
whole rotor is 5-fold symmetric, so balance is exact by construction.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 4
FH_OPTS = {"liveness": False}
INTERFERENCE_ALLOWED = []

C_RAD = 0.0354                 # -> 0.25 mm normal on the 45-deg flanks
POST_R, POST_RIDGE = 0.8, 0.92
POST_RIDGE_Z = (0.54, 0.66, 0.78)
HUB_BORE = POST_R + C_RAD
HUB_GROOVE = POST_RIDGE + C_RAD
HUB_OD = 1.10
HUB_Z0, HUB_Z1 = 0.24, 1.09
CARRIER_ROUT = 2.05
STATION_R = 1.90
STUB_R, STUB_RIDGE = 0.26, 0.34
STUB_Z0, STUB_Z1 = 0.44, 1.00
STUB_RIDGE_Z = (0.66, 0.72, 0.78)
RISER_R0, RISER_R1, RISER_W = 2.00, 2.30, 0.40
ARM_R0, ARM_R1, ARM_W = 2.10, 3.10, 0.55
SPOKE_AZ = 36.0


def _fix_sketch(sk):
    i = 0
    for c in sk.sketchCurves:
        i += 1
        if i % 40 == 0:
            adsk.doEvents()
        if not c.isFixed:
            c.isFixed = True
    for sp in sk.sketchPoints:
        i += 1
        if i % 40 == 0:
            adsk.doEvents()
        if sp.isFullyConstrained or sp.isFixed:
            continue
        sp.isFixed = True


def _poly_xy(sk, pt, xy_pts, z):
    spts = [sk.modelToSketchSpace(pt(x, y, z)) for x, y in xy_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _poly_rz(sk, pt, rz_pts, x_off=0.0):
    spts = [sk.modelToSketchSpace(pt(x_off + r, 0, z)) for r, z in rz_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    return lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _sector_rect(r0, r1, half_w, az_deg):
    a = math.radians(az_deg)
    rh = (math.cos(a), math.sin(a))
    th = (-math.sin(a), math.cos(a))
    return [(r * rh[0] + s * half_w * th[0],
             r * rh[1] + s * half_w * th[1])
            for r, s in ((r0, -1), (r1, -1), (r1, 1), (r0, 1))]


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    pt = ctx.pt
    cbs = ctx.cbs
    rev = root.features.revolveFeatures
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    stator = root.bRepBodies.itemByName("or_stator")
    if stator is None or root.bRepBodies.count != 1:
        raise RuntimeError("expected exactly or_stator from part 1")
    print("FH P2 start, stator %.3f" % stator.volume)

    def ext_join(prof, dist, target, min_dv, name, start=None):
        v0 = target.volume
        inp = ctx.extrudes.createInput(prof, ctx.ops.JoinFeatureOperation)
        if start is not None:
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
                cbs(start))
        e = adsk.fusion.DistanceExtentDefinition.create(cbs(dist))
        inp.setOneSideExtent(e, ctx.dirs.PositiveExtentDirection)
        inp.participantBodies = [target]
        f = ctx.extrudes.add(inp)
        f.name = name
        if target.volume - v0 < min_dv:
            raise RuntimeError("%s added %.4f" % (name, target.volume - v0))
        return f

    # ---- hub on the journal -------------------------------------------
    skh = root.sketches.add(root.xZConstructionPlane)
    skh.name = "hub_profile"
    _poly_rz(skh, pt, [
        (HUB_BORE, HUB_Z0), (HUB_OD, HUB_Z0), (HUB_OD, HUB_Z1),
        (HUB_BORE, HUB_Z1),
        (HUB_BORE, POST_RIDGE_Z[2]), (HUB_GROOVE, POST_RIDGE_Z[1]),
        (HUB_BORE, POST_RIDGE_Z[0]),
    ])
    _fix_sketch(skh)
    if skh.profiles.count != 1:
        raise RuntimeError("hub profiles %d" % skh.profiles.count)
    hinp = rev.createInput(skh.profiles.item(0), root.zConstructionAxis,
                           ctx.ops.NewBodyFeatureOperation)
    hinp.setAngleExtent(False, cbs("360 deg"))
    fh = rev.add(hinp)
    fh.name = "hub_revolve"
    rotor = fh.bodies.item(0)
    rotor.name = "or_rotor"
    print("FH hub vol: %.3f" % rotor.volume)

    # ---- carrier -------------------------------------------------------
    plc = ctx.plane_at_z("2.4 mm", "carrier_plane")
    skc = root.sketches.add(plc)
    skc.name = "carrier"
    ctx.bound_circle(skc, (0, 0, 0.24), HUB_BORE, "16.708 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skc, (0, 0, 0.24), CARRIER_ROUT, "41 mm",
                     x_pos="0 mm", v_pos="0 mm")
    prof_c = None
    for p in skc.profiles:
        a = p.areaProperties().area
        if 9.0 < a < 16.0:
            prof_c = p
            break
    if prof_c is None:
        raise RuntimeError("no carrier annulus profile")
    ext_join(prof_c, "2 mm", rotor, 1.5, "carrier_extrude")

    # ---- planet stub at station 0 --------------------------------------
    sks = root.sketches.add(root.xZConstructionPlane)
    sks.name = "stub_profile"
    axis_ln = _poly_rz(sks, pt, [
        (0.0, STUB_Z0), (STUB_R, STUB_Z0),
        (STUB_R, STUB_RIDGE_Z[0]), (STUB_RIDGE, STUB_RIDGE_Z[1]),
        (STUB_R, STUB_RIDGE_Z[2]), (STUB_R, STUB_Z1), (0.0, STUB_Z1),
    ], x_off=STATION_R)
    _fix_sketch(sks)
    if sks.profiles.count != 1:
        raise RuntimeError("stub profiles %d" % sks.profiles.count)
    v0 = rotor.volume
    sinp = rev.createInput(sks.profiles.item(0), axis_ln,
                           ctx.ops.JoinFeatureOperation)
    sinp.setAngleExtent(False, cbs("360 deg"))
    sinp.participantBodies = [rotor]
    fstub = rev.add(sinp)
    fstub.name = "stub_revolve"
    if rotor.volume - v0 < 0.04:
        raise RuntimeError("stub added %.4f" % (rotor.volume - v0))

    # ---- riser (climbs inboard of the ring tooth tips) -----------------
    plr = ctx.plane_at_z("4.4 mm", "riser_plane")
    skr = root.sketches.add(plr)
    skr.name = "riser"
    _poly_xy(skr, pt, _sector_rect(RISER_R0, RISER_R1, RISER_W / 2,
                                   SPOKE_AZ), 0.44)
    _fix_sketch(skr)
    friser = ext_join(ctx.all_profiles(skr), "6.9 mm", rotor, 0.04,
                      "riser_extrude")

    # ---- arm (reaches over the gear wall to the outer ring) -----------
    pla = ctx.plane_at_z("11.3 mm", "arm_plane")
    ska = root.sketches.add(pla)
    ska.name = "arm"
    _poly_xy(ska, pt, _sector_rect(ARM_R0, ARM_R1, ARM_W / 2,
                                   SPOKE_AZ), 1.13)
    _fix_sketch(ska)
    farm = ext_join(ctx.all_profiles(ska), "3.2 mm", rotor, 0.15,
                    "arm_extrude")
    print("FH one spoke done, rotor vol: %.3f" % rotor.volume)

    # ---- pattern the spoke features x5 ---------------------------------
    v1 = rotor.volume
    coll = adsk.core.ObjectCollection.create()
    for f in (fstub, friser, farm):  # fusionhelper: allow R11 — collection add, not a document mutation
        coll.add(f)
    cpats = root.features.circularPatternFeatures
    pinp = cpats.createInput(coll, root.zConstructionAxis)
    pinp.quantity = cbs("5")
    pinp.totalAngle = cbs("360 deg")
    pinp.isSymmetric = False
    popts = adsk.fusion.PatternComputeOptions
    pinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pf = cpats.add(pinp)
    if pf.healthState not in healthy or rotor.volume - v1 < 0.8:
        raise RuntimeError("spoke pattern dv=%.3f" % (rotor.volume - v1))
    pf.name = "spoke_pattern"

    print("FH P2 OK: rotor %.3f cm3, %d bodies"
          % (rotor.volume, root.bRepBodies.count))
