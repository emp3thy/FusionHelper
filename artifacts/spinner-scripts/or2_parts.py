"""ORRERY mk2 - the moving parts: 5 planets + 6 rollers.

Planets stand on the build plate between sun and ring, located by their
two meshes and retained axially by a mid-height bulge that sits in the
recesses cut into both the sun and the ring. Rollers stand on the plate
through the slot throats and are captured by the twin V-ways.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 6
FH_OPTS = {"only_params": ["o2_gear_top", "o2_roll_d", "o2_stub_d",
                           "o2_fuse_ch"]}
INTERFERENCE_ALLOWED = []

PANG = math.radians(20)
BACKLASH = 0.035   # as thin as a 10-tooth planet allows before
                   # the teeth go pointed; swallows chord error
PL_N, PL_RP, PL_TIP, PL_ROOT = 10, 0.50, 0.60, 0.375
STATION_R = 1.50
PL_BAND = 0.65
BAND = (0.51, 0.56, 0.61)
GEAR_TOP = 1.10
N_PLANET = 5
# rollers
ROLL_REST = 2.55
SLOT_HALF, ROLL_HALF = 0.35, 0.30
GROOVE_TIP, GROOVE_OUT = 0.235, 0.40
GROOVE_FLANK = GROOVE_OUT - GROOVE_TIP
VWAY_ZS = (0.45, 1.10)
N_SLOT = 6


def _inv(a):
    return math.tan(a) - a


def _psi(N, rp, r):
    rb = rp * math.cos(PANG)
    ap = math.acos(min(1.0, rb / rp))
    ar = math.acos(min(1.0, rb / max(r, rb)))
    return math.pi / (2 * N) - BACKLASH / (2 * rp) + _inv(ap) - _inv(ar)


def tooth_space():
    # PHASE: offset by half a tooth pitch. The sun and ring were both cut
    # with a SPACE centred on the +X axis; without this the planet also
    # presents a space at each contact line, so the flanking teeth
    # overlap instead of meshing.
    half = math.pi / PL_N
    phase = half
    rs = [PL_ROOT + (PL_TIP - PL_ROOT) * i / 4.0
          for i in range(5)]      # 5 samples per flank
    pts = []
    for r in rs:
        a = phase + half - _psi(PL_N, PL_RP, r)
        pts.append((r * math.cos(a), r * math.sin(a)))
    for r in reversed(rs):
        a = phase - (half - _psi(PL_N, PL_RP, r))
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def _fix(sk):
    for c in sk.sketchCurves:
        if not c.isFixed:
            c.isFixed = True
    for sp in sk.sketchPoints:
        if not (sp.isFullyConstrained or sp.isFixed):
            sp.isFixed = True
    adsk.doEvents()


def _poly_xy(sk, pt, pts, z):
    sp = [sk.modelToSketchSpace(pt(x, y, z)) for x, y in pts]
    ln = sk.sketchCurves.sketchLines
    first = ln.addByTwoPoints(sp[0], sp[1])
    prev = first
    for i in range(2, len(sp)):
        prev = ln.addByTwoPoints(prev.endSketchPoint, sp[i])
    ln.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


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
    popts = adsk.fusion.PatternComputeOptions
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    if root.bRepBodies.count != 2:
        raise RuntimeError("expected stator+rotor, got %d"
                           % root.bRepBodies.count)

    def body_pattern(seed, n, expect, name, prefix):
        before = root.bRepBodies.count
        coll = adsk.core.ObjectCollection.create()
        coll.add(seed)
        pin = cpats.createInput(coll, root.zConstructionAxis)
        pin.quantity = cbs(str(n))
        pin.totalAngle = cbs("360 deg")
        pin.isSymmetric = False
        pf = cpats.add(pin)
        if (pf.healthState not in healthy
                or root.bRepBodies.count - before != expect):
            raise RuntimeError("%s pattern added %d bodies"
                               % (name, root.bRepBodies.count - before))
        pf.name = name
        for i in range(pf.bodies.count):
            pf.bodies.item(i).name = "%s%d" % (prefix, i + 2)

    # ================= PLANETS ========================================
    skp = root.sketches.add(root.xYConstructionPlane)
    skp.name = "planet_disc"
    ctx.bound_circle(skp, (0, 0, 0), PL_TIP, "12 mm",
                     x_pos="0 mm", v_pos="0 mm")

    def planet_ok(b):
        bb = b.boundingBox
        return (0.8 < b.volume < 1.6 and
                abs((bb.maxPoint.x + bb.minPoint.x) / 2) < 0.05)

    fp, planet = ctx.checked_newbody(ctx.all_profiles(skp), "o2_gear_top",
                                     planet_ok, "planet")
    fp.name = "planet_extrude"
    planet.name = "o2_planet_1"

    skpt = root.sketches.add(root.xYConstructionPlane)
    skpt.name = "planet_tooth_space"
    _poly_xy(skpt, pt, tooth_space(), 0.0)
    _fix(skpt)
    fpc = ctx.blind_cut(ctx.all_profiles(skpt), "o2_gear_top", [planet],
                        "planet_tooth", min_vol_cm3=0.0005)
    fpc.name = "planet_tooth_cut"
    # built at the origin so the teeth pattern about Z; the finished
    # planet is translated out to its station afterwards. (A local
    # construction axis would be the obvious route, but
    # constructionAxes.add raises "Environment is not supported" here.)
    v0 = planet.volume
    tcoll = adsk.core.ObjectCollection.create()
    tcoll.add(fpc)
    tin = cpats.createInput(tcoll, root.zConstructionAxis)
    tin.quantity = cbs(str(PL_N))
    tin.totalAngle = cbs("360 deg")
    tin.isSymmetric = False
    tin.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    ptf = cpats.add(tin)
    if ptf.healthState not in healthy or v0 - planet.volume < 0.02:
        raise RuntimeError("planet tooth pattern dv=%.4f"
                           % (v0 - planet.volume))
    ptf.name = "planet_tooth_pattern"

    # retention bulge: 45-deg cones either side of a short land
    skb = root.sketches.add(root.xZConstructionPlane)
    skb.name = "planet_bulge"
    bl = skb.sketchCurves.sketchLines
    tri = [(PL_TIP, BAND[0]), (PL_BAND, BAND[1]), (PL_TIP, BAND[2])]
    sp = [skb.modelToSketchSpace(pt(r, 0, z)) for r, z in tri]
    a = bl.addByTwoPoints(sp[0], sp[1])
    b = bl.addByTwoPoints(a.endSketchPoint, sp[2])
    bl.addByTwoPoints(b.endSketchPoint, a.startSketchPoint)
    _fix(skb)
    prof = None
    for p in skb.profiles:
        if p.areaProperties().area < 0.02:
            prof = p
            break
    if prof is None:
        raise RuntimeError("no planet bulge profile")
    vb = planet.volume
    bin_ = rev.createInput(prof, root.zConstructionAxis,
                           ctx.ops.JoinFeatureOperation)
    bin_.setAngleExtent(False, cbs("360 deg"))
    bin_.participantBodies = [planet]
    fb = rev.add(bin_)
    fb.name = "planet_bulge_revolve"
    if planet.volume - vb < 0.002:
        raise RuntimeError("bulge added %.4f" % (planet.volume - vb))
    mv = adsk.core.ObjectCollection.create()
    mv.add(planet)
    minp = root.features.moveFeatures.createInput2(mv)
    minp.defineAsTranslateXYZ(cbs("15 mm"), cbs("0 mm"), cbs("0 mm"), True)
    root.features.moveFeatures.add(minp).name = "planet_to_station"
    bb = planet.boundingBox
    cx = (bb.maxPoint.x + bb.minPoint.x) / 2
    if abs(cx - STATION_R) > 0.05:
        raise RuntimeError("planet centre x %.3f, wanted %.3f"
                           % (cx, STATION_R))
    print("FH planet %.3f cm3 at station %.2f mm" % (planet.volume, cx * 10))
    body_pattern(planet, N_PLANET, N_PLANET - 1, "planet_pattern",
                 "o2_planet_")

    # ================= ROLLERS ========================================
    plr = ctx.plane_at_z("1.2 mm", "roller_base_plane")
    skro = root.sketches.add(plr)
    skro.name = "roller_body"
    ctx.bound_circle(skro, (0, ROLL_REST, 0.12), ROLL_HALF, "o2_roll_d",
                     x_pos="0 mm", v_pos="25.5 mm")

    def roller_ok(b):
        bb = b.boundingBox
        return (0.25 < b.volume < 0.50 and
                abs((bb.maxPoint.y + bb.minPoint.y) / 2 - ROLL_REST) < 0.05)

    fro, roller = ctx.checked_newbody(ctx.all_profiles(skro),
                                      "14.5 mm - 1.2 mm", roller_ok,
                                      "roller")
    fro.name = "roller_body_extrude"
    roller.name = "o2_roller_1"

    skst = root.sketches.add(root.xYConstructionPlane)
    skst.name = "roller_stub"
    ctx.bound_circle(skst, (0, ROLL_REST, 0), 0.17, "o2_stub_d",
                     x_pos="0 mm", v_pos="25.5 mm")
    vs = roller.volume
    sin_ = ctx.extrudes.createInput(ctx.all_profiles(skst),
                                    ctx.ops.JoinFeatureOperation)
    sin_.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(cbs("1.2 mm")),
        ctx.dirs.PositiveExtentDirection)
    sin_.participantBodies = [roller]
    fst = ctx.extrudes.add(sin_)
    fst.name = "roller_stub_extrude"
    if roller.volume - vs < 0.005:
        raise RuntimeError("stub added %.4f" % (roller.volume - vs))

    seat = _circle_edges(roller, 0.25, 0.35, (0.12,))
    if seat.count != 1:
        raise RuntimeError("roller seat edge %d != 1" % seat.count)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        seat, cbs("( o2_roll_d - o2_stub_d ) / 2"), True)
    chf.add(ci).name = "roller_seat_cone"

    skg = root.sketches.add(root.yZConstructionPlane)
    skg.name = "roller_vgroove"
    gl = skg.sketchCurves.sketchLines
    for zc in VWAY_ZS:
        gt = [(GROOVE_OUT, zc - GROOVE_FLANK), (GROOVE_TIP, zc),
              (GROOVE_OUT, zc + GROOVE_FLANK)]
        gp = [skg.modelToSketchSpace(pt(0, ROLL_REST + r, z))
              for r, z in gt]
        ga = gl.addByTwoPoints(gp[0], gp[1])
        gb = gl.addByTwoPoints(ga.endSketchPoint, gp[2])
        gl.addByTwoPoints(gb.endSketchPoint, ga.startSketchPoint)
    gax = gl.addByTwoPoints(
        skg.modelToSketchSpace(pt(0, ROLL_REST, 0.0)),
        skg.modelToSketchSpace(pt(0, ROLL_REST, 1.45)))
    gax.isConstruction = True
    _fix(skg)
    gprof = adsk.core.ObjectCollection.create()
    for p in skg.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
        if p.areaProperties().area < 0.05:
            gprof.add(p)
    if gprof.count != 2:
        raise RuntimeError("roller groove profiles %d != 2" % gprof.count)
    vg = roller.volume
    gin = rev.createInput(gprof, gax, ctx.ops.CutFeatureOperation)
    gin.setAngleExtent(False, cbs("360 deg"))
    gin.participantBodies = [roller]
    rev.add(gin).name = "roller_vgroove_cut"
    if vg - roller.volume < 0.005:
        raise RuntimeError("groove removed %.4f" % (vg - roller.volume))
    print("FH roller %.3f cm3" % roller.volume)
    body_pattern(roller, N_SLOT, N_SLOT - 1, "roller_pattern",
                 "o2_roller_")

    print("FH PARTS OK: %d bodies total" % root.bRepBodies.count)
