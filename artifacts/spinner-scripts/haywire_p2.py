"""HAYWIRE GEARWORKS 76 - part 2: the rotor (the "failed print").

Hub sleeve on the 45-degree diamond journal, a hidden carrier, five
risers, and then the illusion: five 60-degree rim chunks with 12-degree
daylight gaps between them, each held on by nothing that looks
structural - two wandering strands plus a third that is deliberately
snapped short of the chunk it should be holding. Repeated five times so
it reads as a systematic print failure rather than a one-off.

The strands are actually 9.5 mm2 in section and deflect ~0.003 mm. The
gaps are also the windows you watch the five planet gears through.

Journal clearance is 0.354 mm RADIAL, which is the 0.25 mm true NORMAL
clearance on 45-degree flanks (a radial 0.25 would give only 0.177).
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 2
FH_OPTS = {"liveness": False}
INTERFERENCE_ALLOWED = []

H = 1.45
C_RAD = 0.0354                 # radial offset -> 0.25 normal on 45 deg
POST_R, POST_RIDGE = 0.8, 0.92
POST_RIDGE_Z = (0.54, 0.66, 0.78)
HUB_BORE = POST_R + C_RAD      # 0.8354
HUB_GROOVE = POST_RIDGE + C_RAD
HUB_OD = 1.10
HUB_Z0, HUB_Z1 = 0.24, 1.09
CARRIER_ROUT = 2.40
CARRIER_Z0, CARRIER_Z1 = 0.24, 0.44
STATION_R = 2.05
STUB_R, STUB_RIDGE = 0.26, 0.34
STUB_Z0, STUB_Z1 = 0.44, 1.00
STUB_RIDGE_Z = (0.66, 0.72, 0.78)
RISER_R0, RISER_R1, RISER_W = 2.20, 2.60, 0.40
RISER_AZ = 36.0
RISER_Z0, RISER_Z1 = 0.44, 1.13
WEB_Z0, WEB_Z1 = 1.13, 1.40
CHUNK_RIN, CHUNK_ROUT = 3.21, 3.80
CHUNK_HALF = 30.0              # 60 deg chunk, 12 deg gap


def _polar(r, deg):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a))


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


def _poly_xy(sk, pt, xy_pts, z):
    spts = [sk.modelToSketchSpace(pt(x, y, z)) for x, y in xy_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        if i % 12 == 0:
            adsk.doEvents()
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
    out = []
    for r, s in ((r0, -1), (r1, -1), (r1, 1), (r0, 1)):
        out.append((r * rh[0] + s * half_w * th[0],
                    r * rh[1] + s * half_w * th[1]))
    return out


def _strand(waypoints, width):
    """Closed polygon around a polar centreline, offset +-width/2."""
    cl = [_polar(r, d) for r, d in waypoints]
    n = len(cl)
    left, right = [], []
    for i in range(n):
        if i == 0:
            tx, ty = cl[1][0] - cl[0][0], cl[1][1] - cl[0][1]
        elif i == n - 1:
            tx, ty = cl[-1][0] - cl[-2][0], cl[-1][1] - cl[-2][1]
        else:
            tx, ty = cl[i + 1][0] - cl[i - 1][0], cl[i + 1][1] - cl[i - 1][1]
        m = math.hypot(tx, ty)
        nx, ny = -ty / m * width / 2, tx / m * width / 2
        left.append((cl[i][0] + nx, cl[i][1] + ny))
        right.append((cl[i][0] - nx, cl[i][1] - ny))
    return left + right[::-1]


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    pt = ctx.pt
    cbs = ctx.cbs
    rev = root.features.revolveFeatures
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    stator = root.bRepBodies.itemByName("hw_stator")
    if stator is None or root.bRepBodies.count != 1:
        raise RuntimeError("expected exactly hw_stator from part 1")
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

    # ---- hub sleeve on the journal ------------------------------------
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
    rotor.name = "hw_rotor"
    print("FH hub vol: %.3f" % rotor.volume)

    # ---- carrier annulus ----------------------------------------------
    plc = ctx.plane_at_z("2.4 mm", "carrier_plane")
    skc = root.sketches.add(plc)
    skc.name = "carrier"
    ctx.bound_circle(skc, (0, 0, CARRIER_Z0), HUB_BORE, "16.708 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skc, (0, 0, CARRIER_Z0), CARRIER_ROUT, "48 mm",
                     x_pos="0 mm", v_pos="0 mm")
    prof_c = None
    for p in skc.profiles:
        a = p.areaProperties().area
        if 15.0 < a < 20.0:
            prof_c = p
            break
    if prof_c is None:
        raise RuntimeError("no carrier annulus profile")
    ext_join(prof_c, "2 mm", rotor, 2.0, "carrier_extrude")

    # ---- stub at station 0 (revolve about its own axis) ---------------
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

    # ---- riser at 36 deg ----------------------------------------------
    plr = ctx.plane_at_z("4.4 mm", "riser_plane")
    skr = root.sketches.add(plr)
    skr.name = "riser"
    _poly_xy(skr, pt, _sector_rect(RISER_R0, RISER_R1, RISER_W / 2,
                                   RISER_AZ), RISER_Z0)
    _fix_sketch(skr)
    friser = ext_join(ctx.all_profiles(skr), "6.9 mm", rotor, 0.05,
                      "riser_extrude")

    # ---- web strands: two carriers + one snapped decoy ----------------
    plw = ctx.plane_at_z("11.3 mm", "web_plane")
    skw = root.sketches.add(plw)
    skw.name = "web_strands"
    _poly_xy(skw, pt, _strand([(2.60, 36), (2.85, 28), (3.05, 22),
                               (3.21, 16)], 0.35), WEB_Z0)
    _poly_xy(skw, pt, _strand([(2.60, 36), (2.85, 44), (3.05, 50),
                               (3.21, 56)], 0.32), WEB_Z0)
    _poly_xy(skw, pt, _strand([(2.60, 36), (2.85, 34), (3.00, 31)],
                              0.20), WEB_Z0)
    _fix_sketch(skw)
    if skw.profiles.count < 3:
        raise RuntimeError("web profiles %d < 3" % skw.profiles.count)
    fweb = ext_join(ctx.all_profiles(skw), "2.7 mm", rotor, 0.05,
                    "web_extrude")

    # ---- one shattered chunk ------------------------------------------
    skk = root.sketches.add(root.xYConstructionPlane)
    skk.name = "chunk"
    outer = [(CHUNK_ROUT, -CHUNK_HALF), (3.64, -12), (CHUNK_ROUT, 4),
             (3.58, 20), (3.76, CHUNK_HALF)]
    lines = skk.sketchCurves.sketchLines
    p_in0 = skk.modelToSketchSpace(
        pt(*_polar(CHUNK_RIN, -CHUNK_HALF), 0))
    seq = [p_in0] + [skk.modelToSketchSpace(pt(*_polar(r, d), 0))
                     for r, d in outer]
    seq.append(skk.modelToSketchSpace(
        pt(*_polar(CHUNK_RIN, CHUNK_HALF), 0)))
    first = lines.addByTwoPoints(seq[0], seq[1])
    prev = first
    for i in range(2, len(seq)):
        adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, seq[i])
    skk.sketchCurves.sketchArcs.addByThreePoints(
        prev.endSketchPoint,
        skk.modelToSketchSpace(pt(*_polar(CHUNK_RIN, 0), 0)),
        first.startSketchPoint)
    _fix_sketch(skk)
    if skk.profiles.count != 1:
        raise RuntimeError("chunk profiles %d" % skk.profiles.count)
    fchunk = ext_join(ctx.all_profiles(skk), "14.5 mm", rotor, 2.0,
                      "chunk_extrude")
    print("FH one cell done, rotor vol: %.3f" % rotor.volume)

    # ---- pattern the cell features x5 ---------------------------------
    v1 = rotor.volume
    coll = adsk.core.ObjectCollection.create()
    for f in (fstub, friser, fweb, fchunk):  # fusionhelper: allow R11 — collection add, not a document mutation
        coll.add(f)
    cpats = root.features.circularPatternFeatures
    pinp = cpats.createInput(coll, root.zConstructionAxis)
    pinp.quantity = cbs("5")
    pinp.totalAngle = cbs("360 deg")
    pinp.isSymmetric = False
    popts = adsk.fusion.PatternComputeOptions
    pinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pf = cpats.add(pinp)
    if pf.healthState not in healthy or rotor.volume - v1 < 9.0:
        raise RuntimeError("cell pattern dv=%.3f" % (rotor.volume - v1))
    pf.name = "cell_pattern"

    print("FH P2 OK: rotor %.3f cm3, %d bodies"
          % (rotor.volume, root.bRepBodies.count))
