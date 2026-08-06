"""ORRERY 90 - part 4: the five planet gears.

15-tooth planets on the rotor's mini diamond stubs, meshing with the
stator's 50-tooth internal ring: 3.33 turns per carrier revolution, and
50/5 = 10 teeth per station so the 72-degree body pattern lands every
station in mesh phase. Each carries an offset puck so the eye reads the
rotation rather than a blur of teeth.

Built as a plain disc at the tooth-tip radius with one tooth SPACE cut
and patterned x15 - far fewer API calls than a 200-line outline, which
is what blew the client timeout on the ring gear.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 8
FH_OPTS = {"only_params": ["or_base_t", "or_fuse_ch"]}
INTERFERENCE_ALLOWED = []

PL_N = 12
PL_TIP = 0.68
PL_ROOT = 0.475
PL_RP = 0.60
PL_RB = PL_RP * math.cos(math.radians(20))
BACKLASH = 0.030
STATION_R = 1.90
C_RAD = 0.0354
STUB_R, STUB_RIDGE = 0.26, 0.34
STUB_RIDGE_Z = (0.66, 0.72, 0.78)
PL_Z0, PL_Z1 = 0.48, 1.06
PL_BORE = STUB_R + C_RAD          # 0.2954
PL_GROOVE = STUB_RIDGE + C_RAD    # 0.3754
PL_BORE_TOP = 1.02
PUCK_R, PUCK_OFF = 0.25, 0.20
PUCK_Z0, PUCK_Z1 = 1.06, 1.35


def _inv(a):
    return math.tan(a) - a


def _flank_angle(psi_p, rp, rb, r):
    ap = math.acos(rb / rp)
    ar = math.acos(min(1.0, rb / max(r, rb)))
    return psi_p + _inv(ap) - _inv(ar)


def _planet_outline(phase):
    pts = []
    start = max(PL_ROOT, PL_RB + 1e-4)
    flank_rs = [start, (start + PL_TIP) / 2, PL_TIP]
    for k in range(PL_N):
        c = phase + 2 * math.pi * k / PL_N
        pitch = 2 * math.pi / PL_N
        psi_p = (math.pi / (2 * PL_N)
                 + (2 * 0.03 * math.tan(math.radians(20))) / PL_N
                 - BACKLASH / (2 * PL_RP))
        psi_root = _flank_angle(psi_p, PL_RP, PL_RB, flank_rs[0])
        pts.append((PL_ROOT * math.cos(c - pitch / 2),
                    PL_ROOT * math.sin(c - pitch / 2)))
        if PL_ROOT < PL_RB:
            pts.append((PL_ROOT * math.cos(c - psi_root),
                        PL_ROOT * math.sin(c - psi_root)))
        for r in flank_rs:
            a = c - _flank_angle(psi_p, PL_RP, PL_RB, r)
            pts.append((r * math.cos(a), r * math.sin(a)))
        for r in reversed(flank_rs):
            a = c + _flank_angle(psi_p, PL_RP, PL_RB, r)
            pts.append((r * math.cos(a), r * math.sin(a)))
        if PL_ROOT < PL_RB:
            pts.append((PL_ROOT * math.cos(c + psi_root),
                        PL_ROOT * math.sin(c + psi_root)))
    return pts


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
    rotor = root.bRepBodies.itemByName("or_rotor")
    if stator is None or rotor is None or root.bRepBodies.count != 2:
        raise RuntimeError("expected or_stator + or_rotor from parts 1-2")
    print("FH P3 start: stator %.3f rotor %.3f"
          % (stator.volume, rotor.volume))

    # ---- planet gear body ---------------------------------------------
    skg = root.sketches.add(root.xYConstructionPlane)
    skg.name = "planet_gear"
    pl_pts = [(STATION_R + x, y) for x, y in _planet_outline(0.0)]
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
        cbs("4.8 mm"))
    ext = adsk.fusion.DistanceExtentDefinition.create(cbs("5.8 mm"))
    ginp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
    fpl = ctx.extrudes.add(ginp)
    fpl.name = "planet_extrude"
    planet = fpl.bodies.item(0)
    planet.name = "or_planet_1"
    if not (0.3 < planet.volume < 1.0):
        raise RuntimeError("planet vol %.3f" % planet.volume)
    print("FH planet gear vol: %.3f" % planet.volume)

    # ---- blind bore + diamond groove ----------------------------------
    skb = root.sketches.add(root.xZConstructionPlane)
    skb.name = "planet_bore"
    rz = [
        (0.0, PL_Z0), (PL_BORE, PL_Z0),
        (PL_BORE, STUB_RIDGE_Z[0]), (PL_GROOVE, STUB_RIDGE_Z[1]),
        (PL_BORE, STUB_RIDGE_Z[2]), (PL_BORE, PL_BORE_TOP),
        (0.0, PL_BORE_TOP),
    ]
    bpts = [skb.modelToSketchSpace(pt(STATION_R + r, 0, z)) for r, z in rz]
    bl = skb.sketchCurves.sketchLines
    bfirst = bl.addByTwoPoints(bpts[0], bpts[1])
    bprev = bfirst
    for i in range(2, len(bpts)):
        adsk.doEvents()
        bprev = bl.addByTwoPoints(bprev.endSketchPoint, bpts[i])
    bl.addByTwoPoints(bprev.endSketchPoint, bfirst.startSketchPoint)
    _fix_sketch(skb)
    if skb.profiles.count != 1:
        raise RuntimeError("bore profiles %d" % skb.profiles.count)
    axis_line = None
    for ln in skb.sketchCurves.sketchLines:
        s = skb.sketchToModelSpace(ln.startSketchPoint.geometry)
        e = skb.sketchToModelSpace(ln.endSketchPoint.geometry)
        if (abs(s.x - STATION_R) < 1e-4 and abs(e.x - STATION_R) < 1e-4
                and abs(s.y) < 1e-4 and abs(e.y) < 1e-4):
            axis_line = ln
            break
    if axis_line is None:
        raise RuntimeError("bore axis line not found")
    v0 = planet.volume
    binp = rev.createInput(skb.profiles.item(0), axis_line,
                           ctx.ops.CutFeatureOperation)
    binp.setAngleExtent(False, cbs("360 deg"))
    binp.participantBodies = [planet]
    fb = rev.add(binp)
    fb.name = "planet_bore_cut"
    if v0 - planet.volume < 0.08:
        raise RuntimeError("bore removed %.4f" % (v0 - planet.volume))

    # ---- offset puck so the rotation reads at speed --------------------
    skp = root.sketches.add(root.xYConstructionPlane)
    skp.name = "puck"
    ctx.bound_circle(skp, (STATION_R + PUCK_OFF, 0, 0), PUCK_R, "5 mm",
                     x_pos="21.0 mm", v_pos="0 mm")
    v1 = planet.volume
    pinp = ctx.extrudes.createInput(ctx.all_profiles(skp),
                                    ctx.ops.JoinFeatureOperation)
    pinp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        cbs("10.6 mm"))
    exp = adsk.fusion.DistanceExtentDefinition.create(cbs("2.9 mm"))
    pinp.setOneSideExtent(exp, ctx.dirs.PositiveExtentDirection)
    pinp.participantBodies = [planet]
    fpk = ctx.extrudes.add(pinp)
    fpk.name = "puck_extrude"
    if planet.volume - v1 < 0.03:
        raise RuntimeError("puck added %.4f" % (planet.volume - v1))
    print("FH planet vol: %.3f" % planet.volume)

    # ---- body pattern x5 (55/5 = 11 teeth per station -> in phase) ----
    bcoll = adsk.core.ObjectCollection.create()
    bcoll.add(planet)
    n_before = root.bRepBodies.count
    cpats = root.features.circularPatternFeatures
    pinp2 = cpats.createInput(bcoll, root.zConstructionAxis)
    pinp2.quantity = cbs("5")
    pinp2.totalAngle = cbs("360 deg")
    pinp2.isSymmetric = False
    pfb = cpats.add(pinp2)
    if (pfb.healthState not in healthy or
            root.bRepBodies.count - n_before != 4):
        raise RuntimeError("planet pattern bodies %d"
                           % (root.bRepBodies.count - n_before))
    pfb.name = "planet_pattern"
    for i in range(pfb.bodies.count):
        pfb.bodies.item(i).name = "or_planet_%d" % (i + 2)

    print("FH BUILD OK: stator %.3f rotor %.3f planet %.3f cm3, %d bodies"
          % (stator.volume, rotor.volume, planet.volume,
             root.bRepBodies.count))
