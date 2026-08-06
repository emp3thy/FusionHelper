"""Pentaroule 60 PiP - bearingless print-in-place variant.

Reuleaux pentagon rotor (constant width 60 mm) spinning on a printed
diamond-profile journal around a fixed stator disc. Zero hardware: no
bearing, no nuts. The journal (base r 11, ridge 1.2, radial clearance
0.25 mm) is fixed art - per-printer clearance retunes are a constant
edit + fresh-doc rerun, mirroring how leaderboard PiP designs ship
clearance variants. Live parameters are the two chamfers.

Bodies: pentaroule_rotor, pip_stator (0.25 mm radial gap, printed as
one plate).
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {"only_params": ["pp_chamf", "pp_pip_foot"]}
INTERFERENCE_ALLOWED = []

# Fixed art constants (cm).
W = 6.0
RHO = 0.3
RS = W - RHO
D = W - 2 * RHO
T = 0.9
JR = 1.1          # journal base radius
JD = 0.12         # diamond ridge depth
CLR = 0.025       # radial clearance (the per-printer tuning constant)
DIMPLE_R = 2.4
SPHERE_R = 1.1
DIMPLE_DEPTH = 0.12


def _unit(vx, vy):
    n = math.hypot(vx, vy)
    return (vx / n, vy / n)


def _reuleaux_segments():
    rv = D / (2.0 * math.sin(math.radians(72)))
    verts = []
    for k in range(5):
        a = math.radians(90 + 72 * k)
        verts.append((rv * math.cos(a), rv * math.sin(a)))
    sides = []
    for k in range(5):
        vk = verts[k]
        pts = []
        for other in (verts[(k + 2) % 5], verts[(k + 3) % 5]):
            u = _unit(other[0] - vk[0], other[1] - vk[1])
            pts.append((vk[0] + RS * u[0], vk[1] + RS * u[1]))
        sides.append((vk, RS, pts[0], pts[1]))
    corners = []
    for j in range(5):
        vj = verts[j]
        pts = []
        for far in (verts[(j - 2) % 5], verts[(j - 3) % 5]):
            u = _unit(vj[0] - far[0], vj[1] - far[1])
            pts.append((vj[0] + RHO * u[0], vj[1] + RHO * u[1]))
        corners.append((vj, RHO, pts[0], pts[1]))
    allsegs = sides + corners

    def midaz(seg):
        c, r, p1, p2 = seg
        return math.atan2((p1[1] + p2[1]) / 2, (p1[0] + p2[0]) / 2)

    ordered = sorted(allsegs, key=midaz)
    chained = []
    for i, seg in enumerate(ordered):
        c, r, p1, p2 = seg
        if i == 0:
            a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
            a2 = math.atan2(p2[1] - c[1], p2[0] - c[0])
            if (a2 - a1) % (2 * math.pi) > math.pi:
                p1, p2 = p2, p1
        else:
            pe = chained[-1][3]
            d1 = math.hypot(p1[0] - pe[0], p1[1] - pe[1])
            d2 = math.hypot(p2[0] - pe[0], p2[1] - pe[1])
            if d2 < d1:
                p1, p2 = p2, p1
            if min(d1, d2) > 1e-6:
                raise RuntimeError("segment %d gap %.6f" % (i, min(d1, d2)))
        chained.append((c, r, p1, p2))
    gap = math.hypot(chained[-1][3][0] - chained[0][2][0],
                     chained[-1][3][1] - chained[0][2][1])
    if gap > 1e-6:
        raise RuntimeError("profile not closed (%.6f)" % gap)
    return chained


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


def _journal_polyline(sk, pt, base_r):
    """Closed journal half-section on a vertical plane through the axis:
    axis seg + bottom + wall with diamond bulge + top. Returns nothing;
    caller uses sk.profiles."""
    mpts = [
        (0.0, 0.0), (base_r, 0.0), (base_r, T / 3),
        (base_r + JD, T / 2), (base_r, 2 * T / 3),
        (base_r, T), (0.0, T),
    ]
    spts = [sk.modelToSketchSpace(pt(x, 0, z)) for x, z in mpts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    made = [first]
    for i in range(2, len(spts)):
        adsk.doEvents()
        ln = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
        made.append(ln)
        prev = ln
    made.append(lines.addByTwoPoints(prev.endSketchPoint,
                                     first.startSketchPoint))
    return made[-1]  # the axis segment (last closing line)


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs

    up.add("pp_chamf", cbs("1.2 mm"), "mm", "perimeter chamfer")
    up.add("pp_pip_foot", cbs("0.3 mm"), "mm",
           "anti-fuse chamfer at the PiP gap, both parts")
    print("FH params added")

    # ---- rotor: Reuleaux profile + extrude ----------------------------
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.name = "reuleaux_profile"
    arcs = sk.sketchCurves.sketchArcs
    for c, r, p1, p2 in _reuleaux_segments():
        adsk.doEvents()
        a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
        a2 = math.atan2(p2[1] - c[1], p2[0] - c[0])
        sweep = (a2 - a1) % (2 * math.pi)
        if not (0.5 < sweep < 0.8):
            raise RuntimeError("bad sweep %.4f" % sweep)
        arcs.addByCenterStartSweep(
            sk.modelToSketchSpace(pt(c[0], c[1], 0)),
            sk.modelToSketchSpace(pt(p1[0], p1[1], 0)), sweep)
    _fix_sketch(sk)
    if sk.profiles.count != 1:
        raise RuntimeError("profiles %d != 1" % sk.profiles.count)

    def rotor_ok(b):
        return b.boundingBox.maxPoint.z > 0.85 and 20.0 < b.volume < 30.0

    f, rotor = ctx.checked_newbody(ctx.all_profiles(sk), "9 mm",
                                   rotor_ok, "rotor")
    f.name = "rotor_extrude"
    rotor.name = "pentaroule_rotor"
    print("FH rotor vol: %.3f" % rotor.volume)

    # ---- journal cavity (revolve cut, female = base + clearance) ------
    skj = root.sketches.add(root.xZConstructionPlane)
    skj.name = "journal_cavity"
    axis_ln = _journal_polyline(skj, pt, JR + CLR)
    _fix_sketch(skj)
    if skj.profiles.count != 1:
        raise RuntimeError("cavity profiles %d != 1" % skj.profiles.count)
    v0 = rotor.volume
    rev = root.features.revolveFeatures
    rinp = rev.createInput(skj.profiles.item(0), axis_ln,
                           ctx.ops.CutFeatureOperation)
    rinp.setAngleExtent(False, cbs("360 deg"))
    rinp.participantBodies = [rotor]
    rf = rev.add(rinp)
    rf.name = "journal_cavity_cut"
    if v0 - rotor.volume < 3.0:
        raise RuntimeError("cavity cut removed %.3f cm3" % (v0 - rotor.volume))
    print("FH cavity cut: %.3f cm3" % (v0 - rotor.volume))

    # ---- dimples (seed + circular pattern), as v1 ---------------------
    skd = root.sketches.add(root.yZConstructionPlane)
    skd.name = "dimple_seed_profile"
    zc = T - DIMPLE_DEPTH + SPHERE_R
    rim = math.sqrt(SPHERE_R ** 2 - (zc - T) ** 2)
    a_pt = pt(0, DIMPLE_R, T - DIMPLE_DEPTH)
    t_pt = pt(0, DIMPLE_R, T)
    e_pt = pt(0, DIMPLE_R + rim, T)
    ve = (rim, T - zc)
    va = (0.0, T - DIMPLE_DEPTH - zc)
    ms = (ve[0] + va[0], ve[1] + va[1])
    mn = math.hypot(ms[0], ms[1])
    m_pt = pt(0, DIMPLE_R + SPHERE_R * ms[0] / mn, zc + SPHERE_R * ms[1] / mn)
    dl = skd.sketchCurves.sketchLines
    ax2 = dl.addByTwoPoints(skd.modelToSketchSpace(a_pt),
                            skd.modelToSketchSpace(t_pt))
    top2 = dl.addByTwoPoints(ax2.endSketchPoint,
                             skd.modelToSketchSpace(e_pt))
    skd.sketchCurves.sketchArcs.addByThreePoints(
        top2.endSketchPoint, skd.modelToSketchSpace(m_pt),
        ax2.startSketchPoint)
    _fix_sketch(skd)
    if skd.profiles.count != 1:
        raise RuntimeError("dimple profiles %d" % skd.profiles.count)
    v1 = rotor.volume
    rinp2 = rev.createInput(skd.profiles.item(0), ax2,
                            ctx.ops.CutFeatureOperation)
    rinp2.setAngleExtent(False, cbs("360 deg"))
    rinp2.participantBodies = [rotor]
    rf2 = rev.add(rinp2)
    rf2.name = "dimple_seed"
    if v1 - rotor.volume < 0.03:
        raise RuntimeError("dimple removed %.4f" % (v1 - rotor.volume))

    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)
    v2 = rotor.volume
    coll = adsk.core.ObjectCollection.create()
    coll.add(rf2)
    cpats = root.features.circularPatternFeatures
    pinp = cpats.createInput(coll, root.zConstructionAxis)
    pinp.quantity = cbs("5")
    pinp.totalAngle = cbs("360 deg")
    pinp.isSymmetric = False
    popts = adsk.fusion.PatternComputeOptions
    pinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pf = cpats.add(pinp)
    if pf.healthState not in healthy or v2 - rotor.volume < 0.15:
        raise RuntimeError("dimple pattern invalid dv=%.4f"
                           % (v2 - rotor.volume))
    pf.name = "dimple_pattern"
    print("FH dimples done vol: %.3f" % rotor.volume)

    # ---- stator (revolve new body, male journal) ----------------------
    sks = root.sketches.add(root.xZConstructionPlane)
    sks.name = "stator_profile"
    axis_s = _journal_polyline(sks, pt, JR)
    _fix_sketch(sks)
    if sks.profiles.count != 1:
        raise RuntimeError("stator profiles %d" % sks.profiles.count)
    rinp3 = rev.createInput(sks.profiles.item(0), axis_s,
                            ctx.ops.NewBodyFeatureOperation)
    rinp3.setAngleExtent(False, cbs("360 deg"))
    rf3 = rev.add(rinp3)
    rf3.name = "stator_revolve"
    stator = rf3.bodies.item(0)
    stator.name = "pip_stator"
    if not (3.0 < stator.volume < 4.5):
        raise RuntimeError("stator vol %.3f" % stator.volume)
    print("FH stator vol: %.3f" % stator.volume)

    # ---- chamfers ------------------------------------------------------
    chf = root.features.chamferFeatures

    def edge_set(body, radius_lo, radius_hi, z_targets):
        out = adsk.core.ObjectCollection.create()
        for e in body.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            g = e.geometry
            r = getattr(g, "radius", None)
            if r is None or not (radius_lo < r < radius_hi):
                continue
            bb = e.boundingBox
            if abs(bb.maxPoint.z - bb.minPoint.z) > 0.02:
                continue
            if any(abs(bb.minPoint.z - zt) < 0.02 for zt in z_targets):
                out.add(e)
        return out

    per = edge_set(rotor, 5.55, 5.85, (0.0, T))
    for e in edge_set(rotor, 0.25, 0.35, (0.0, T)):  # fusionhelper: allow R11 — collection add, not a document mutation
        per.add(e)
    if per.count < 16:
        raise RuntimeError("perimeter edges %d < 16" % per.count)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        per, cbs("pp_chamf"), True)
    c1 = chf.add(ci)
    c1.name = "perimeter_chamfer"

    pip_edges = edge_set(rotor, 1.05, 1.20, (0.0,))
    for e in edge_set(stator, 1.02, 1.18, (0.0,)):  # fusionhelper: allow R11 — collection add, not a document mutation
        pip_edges.add(e)
    if pip_edges.count != 2:
        raise RuntimeError("pip gap edges %d != 2" % pip_edges.count)
    ci2 = chf.createInput2()
    ci2.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        pip_edges, cbs("pp_pip_foot"), True)
    c2 = chf.add(ci2)
    c2.name = "pip_gap_foot_chamfer"
    print("FH BUILD OK: rotor %.3f + stator %.3f cm3, %d bodies"
          % (rotor.volume, stator.volume, root.bRepBodies.count))
