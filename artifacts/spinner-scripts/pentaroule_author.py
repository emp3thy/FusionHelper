"""Pentaroule 60 - Reuleaux pentagon constant-width fidget spinner.

Silhouette: rounded Reuleaux pentagon, constant width W=60 mm, corner
radius rho=3 mm - drawn as fixed art (exact analytic construction; the
tangency condition d = W - 2*rho is what makes it constant-width, so the
profile is computed, not dimension-driven). Print-tunable quantities are
user parameters: seat diameter, pocket floor/height, chamfers, stem.

Bodies: spinner (608 seat, 5 hex nut pockets, 5 top dimples), cap_a,
cap_b (press-fit grip caps, printed separately, placed clear of the
spinner).
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": [
        "pr_t", "pr_seat_d", "pr_lead", "pr_chamf",
        "pr_pocket_floor", "pr_pocket_h", "pr_stem_d",
    ],
}
INTERFERENCE_ALLOWED = []

# Fixed art constants (cm) - the constant-width construction.
W = 6.0          # constant width
RHO = 0.3        # corner radius
RS = W - RHO     # side arc radius (5.7)
D = W - 2 * RHO  # pentagon diagonal (5.4)
POCKET_R = 1.95  # nut pocket centre radius
NUT_AF = 1.33    # hex pocket across-flats
DIMPLE_R = 2.4   # dimple centre radius
SPHERE_R = 1.1   # dimple sphere radius
DIMPLE_DEPTH = 0.12
CAP_X = 5.5      # cap placement offset


def _unit(vx, vy):
    n = math.hypot(vx, vy)
    return (vx / n, vy / n)


def _reuleaux_segments():
    """10 (center, radius, start, end) tuples ordered CCW; consecutive
    endpoints coincide exactly by construction."""
    rv = D / (2.0 * math.sin(math.radians(72)))
    verts = []
    for k in range(5):
        a = math.radians(90 + 72 * k)
        verts.append((rv * math.cos(a), rv * math.sin(a)))
    segs = []
    for k in range(5):
        vk = verts[k]
        for other in (verts[(k + 2) % 5], verts[(k + 3) % 5]):
            u = _unit(other[0] - vk[0], other[1] - vk[1])
            segs.append(("side_pt", vk, RS,
                         (vk[0] + RS * u[0], vk[1] + RS * u[1])))
    # side arc k: endpoints are the two points computed above
    sides = []
    for k in range(5):
        p1 = segs[2 * k][3]
        p2 = segs[2 * k + 1][3]
        sides.append((verts[k], RS, p1, p2))
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
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        return math.atan2(my, mx)

    ordered = sorted(allsegs, key=midaz)
    # orient each so start joins previous end
    chained = []
    for i, seg in enumerate(ordered):
        c, r, p1, p2 = seg
        if i == 0:
            # orient CCW: sweep from p1 must be positive and small
            a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
            a2 = math.atan2(p2[1] - c[1], p2[0] - c[0])
            if (a2 - a1) % (2 * math.pi) > math.pi:
                p1, p2 = p2, p1
        else:
            prev_end = chained[-1][3]
            d1 = math.hypot(p1[0] - prev_end[0], p1[1] - prev_end[1])
            d2 = math.hypot(p2[0] - prev_end[0], p2[1] - prev_end[1])
            if d2 < d1:
                p1, p2 = p2, p1
            if min(d1, d2) > 1e-6:
                raise RuntimeError(
                    "segment %d does not chain (gap %.6f)" % (i, min(d1, d2)))
        chained.append((c, r, p1, p2))
    # closure
    gap = math.hypot(chained[-1][3][0] - chained[0][2][0],
                     chained[-1][3][1] - chained[0][2][1])
    if gap > 1e-6:
        raise RuntimeError("profile not closed (gap %.6f)" % gap)
    return chained


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs

    # ---- parameter table first ----------------------------------------
    up.add("pr_t", cbs("9 mm"), "mm", "spinner thickness")
    up.add("pr_seat_d", cbs("21.9 mm"), "mm", "608 seat dia (PLA press)")
    up.add("pr_lead", cbs("0.5 mm"), "mm", "bore lead-in chamfer")
    up.add("pr_chamf", cbs("1.2 mm"), "mm", "perimeter chamfer")
    up.add("pr_pocket_floor", cbs("1.6 mm"), "mm", "nut pocket floor")
    up.add("pr_pocket_h", cbs("6.8 mm"), "mm", "nut pocket height")
    up.add("pr_stem_d", cbs("8.1 mm"), "mm", "cap stem dia (inner race)")
    print("FH params added")

    # ---- Reuleaux profile (fixed art) ---------------------------------
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.name = "reuleaux_profile"
    arcs = sk.sketchCurves.sketchArcs
    drawn = []
    for c, r, p1, p2 in _reuleaux_segments():
        adsk.doEvents()
        a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
        a2 = math.atan2(p2[1] - c[1], p2[0] - c[0])
        sweep = (a2 - a1) % (2 * math.pi)
        if not (0.5 < sweep < 0.8):
            raise RuntimeError("bad sweep %.4f" % sweep)
        cs = sk.modelToSketchSpace(pt(c[0], c[1], 0))
        ps = sk.modelToSketchSpace(pt(p1[0], p1[1], 0))
        drawn.append(arcs.addByCenterStartSweep(cs, ps, sweep))
    for a in drawn:
        adsk.doEvents()
        a.isFixed = True
    if sk.profiles.count != 1:
        raise RuntimeError("expected 1 profile, got %d" % sk.profiles.count)
    area = sk.profiles.item(0).areaProperties().area
    if not (25.0 < area < 28.5):
        raise RuntimeError("profile area %.3f out of range" % area)
    print("FH profile area cm2: %.3f" % area)

    def body_up(b):
        bb = b.boundingBox
        return bb.maxPoint.z > 0.85 and 20.0 < b.volume < 30.0

    f, spinner = ctx.checked_newbody(
        ctx.all_profiles(sk), "pr_t", body_up, "spinner")
    f.name = "spinner_extrude"
    spinner.name = "pentaroule_body"
    print("FH body vol cm3: %.3f" % spinner.volume)

    # ---- bearing bore -------------------------------------------------
    skb = root.sketches.add(root.xYConstructionPlane)
    skb.name = "bore"
    circ = skb.sketchCurves.sketchCircles.addByCenterRadius(
        pt(0.05, 0.08, 0), 1.0)
    skb.geometricConstraints.addCoincident(
        circ.centerSketchPoint, skb.originPoint)
    dd = skb.sketchDimensions.addDiameterDimension(circ, pt(1.8, -1.8, 0))
    dd.parameter.expression = "pr_seat_d"
    fb = ctx.blind_cut(ctx.all_profiles(skb), "pr_t + 1 mm", [spinner],
                       "bore", min_vol_cm3=2.5)
    fb.name = "bore_cut"
    print("FH bore done vol: %.3f" % spinner.volume)

    # ---- hex nut pockets (internal, sealed by print pause) ------------
    pl = ctx.plane_at_z("pr_pocket_floor", "pocket_floor_plane")
    skp = root.sketches.add(pl)
    skp.name = "nut_pockets"
    rc = NUT_AF / math.sqrt(3.0)
    lines = skp.sketchCurves.sketchLines
    hex_lines = []
    for k in range(5):
        theta = math.radians(126 + 72 * k)
        cx = POCKET_R * math.cos(theta)
        cy = POCKET_R * math.sin(theta)
        vpts = []
        for m in range(6):
            va = theta + math.radians(30 + 60 * m)
            wpt = pt(cx + rc * math.cos(va), cy + rc * math.sin(va), 0.16)
            vpts.append(skp.modelToSketchSpace(wpt))
        first = lines.addByTwoPoints(vpts[0], vpts[1])
        hex_lines.append(first)
        prev = first
        for m in range(1, 6):
            adsk.doEvents()
            if m < 5:
                ln = lines.addByTwoPoints(prev.endSketchPoint, vpts[m + 1])
            else:
                ln = lines.addByTwoPoints(prev.endSketchPoint,
                                          first.startSketchPoint)
            hex_lines.append(ln)
            prev = ln
    for ln in hex_lines:
        adsk.doEvents()
        ln.isFixed = True
    if skp.profiles.count != 5:
        raise RuntimeError("expected 5 hex profiles, got %d"
                           % skp.profiles.count)
    fp = ctx.blind_cut(ctx.all_profiles(skp), "pr_pocket_h", [spinner],
                       "pockets", min_vol_cm3=4.0)
    fp.name = "nut_pocket_cut"
    print("FH pockets done vol: %.3f" % spinner.volume)

    # ---- dimple seed (spherical cap, revolve cut) + circular pattern --
    skd = root.sketches.add(root.yZConstructionPlane)
    skd.name = "dimple_seed_profile"
    # model points (cm): axis at (0, DIMPLE_R), sphere centre z
    zc = 0.9 - DIMPLE_DEPTH + SPHERE_R          # 1.88
    rim = math.sqrt(SPHERE_R ** 2 - (zc - 0.9) ** 2)   # 0.5
    a_pt = pt(0, DIMPLE_R, 0.9 - DIMPLE_DEPTH)  # sphere bottom on axis
    t_pt = pt(0, DIMPLE_R, 0.9)                 # axis at top face
    e_pt = pt(0, DIMPLE_R + rim, 0.9)           # rim on top face
    # mid point of arc E->A on circle centre (0, DIMPLE_R, zc) r SPHERE_R
    ve = (e_pt.y - DIMPLE_R, e_pt.z - zc)
    va = (a_pt.y - DIMPLE_R, a_pt.z - zc)
    ms = (ve[0] + va[0], ve[1] + va[1])
    mn = math.hypot(ms[0], ms[1])
    m_pt = pt(0, DIMPLE_R + SPHERE_R * ms[0] / mn,
              zc + SPHERE_R * ms[1] / mn)
    dl = skd.sketchCurves.sketchLines
    axis_ln = dl.addByTwoPoints(skd.modelToSketchSpace(a_pt),
                                skd.modelToSketchSpace(t_pt))
    top_ln = dl.addByTwoPoints(axis_ln.endSketchPoint,
                               skd.modelToSketchSpace(e_pt))
    arc = skd.sketchCurves.sketchArcs.addByThreePoints(
        top_ln.endSketchPoint, skd.modelToSketchSpace(m_pt),
        axis_ln.startSketchPoint)
    for ent in (axis_ln, top_ln, arc):
        adsk.doEvents()
        ent.isFixed = True
    if skd.profiles.count != 1:
        raise RuntimeError("dimple profile count %d" % skd.profiles.count)
    v0 = spinner.volume
    rev = root.features.revolveFeatures
    rinp = rev.createInput(skd.profiles.item(0), axis_ln,
                           ctx.ops.CutFeatureOperation)
    rinp.setAngleExtent(False, cbs("360 deg"))
    rinp.participantBodies = [spinner]
    rf = rev.add(rinp)
    rf.name = "dimple_seed"
    if v0 - spinner.volume < 0.03:
        raise RuntimeError("dimple seed removed %.4f cm3"
                           % (v0 - spinner.volume))
    print("FH dimple seed cut: %.4f cm3" % (v0 - spinner.volume))

    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)
    v1 = spinner.volume
    coll = adsk.core.ObjectCollection.create()
    coll.add(rf)
    cpats = root.features.circularPatternFeatures
    pinp = cpats.createInput(coll, root.zConstructionAxis)
    pinp.quantity = cbs("5")
    pinp.totalAngle = cbs("360 deg")
    pinp.isSymmetric = False
    popts = adsk.fusion.PatternComputeOptions
    pinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pf = cpats.add(pinp)
    if pf.healthState not in healthy or v1 - spinner.volume < 0.15:
        raise RuntimeError("dimple pattern invalid (hs=%s dv=%.4f)"
                           % (pf.healthState, v1 - spinner.volume))
    pf.name = "dimple_pattern"
    print("FH dimples done vol: %.3f" % spinner.volume)

    # ---- chamfers (last) ----------------------------------------------
    chf = root.features.chamferFeatures

    def edge_set(radius_lo, radius_hi):
        out = adsk.core.ObjectCollection.create()
        for e in spinner.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            g = e.geometry
            r = getattr(g, "radius", None)
            if r is None or not (radius_lo < r < radius_hi):
                continue
            bb = e.boundingBox
            zmin, zmax = bb.minPoint.z, bb.maxPoint.z
            flat = abs(zmax - zmin) < 0.02
            at_face = (abs(zmin) < 0.02 or
                       abs(zmax - 0.9) < 0.02)
            if flat and at_face:
                out.add(e)
        return out

    per_edges = edge_set(5.55, 5.85)
    for e in edge_set(0.25, 0.35):  # fusionhelper: allow R11 — collection add, not a document mutation
        per_edges.add(e)
    if per_edges.count < 16:
        raise RuntimeError("perimeter edge set %d < 16" % per_edges.count)
    cinp = chf.createInput2()
    cinp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        per_edges, cbs("pr_chamf"), True)
    cf1 = chf.add(cinp)
    cf1.name = "perimeter_chamfer"

    bore_edges = edge_set(1.02, 1.14)
    if bore_edges.count != 2:
        raise RuntimeError("bore edge set %d != 2" % bore_edges.count)
    cinp2 = chf.createInput2()
    cinp2.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        bore_edges, cbs("pr_lead"), True)
    cf2 = chf.add(cinp2)
    cf2.name = "bore_lead_chamfer"
    print("FH chamfers done vol: %.3f" % spinner.volume)

    # ---- grip caps (2, printed separately, placed clear) --------------
    skc = root.sketches.add(root.xYConstructionPlane)
    skc.name = "cap_discs"
    ctx.bound_circle(skc, (CAP_X, 0, 0), 1.0, "20 mm",
                     x_pos="55 mm", v_pos="0 mm")
    ctx.bound_circle(skc, (-CAP_X, 0, 0), 1.0, "20 mm",
                     x_pos="55 mm", v_pos="0 mm")
    dinp = ctx.extrudes.createInput(ctx.all_profiles(skc),
                                    ctx.ops.NewBodyFeatureOperation)
    ext = adsk.fusion.DistanceExtentDefinition.create(cbs("3.3 mm"))
    dinp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
    fdisc = ctx.extrudes.add(dinp)
    fdisc.name = "cap_discs_extrude"
    caps = [fdisc.bodies.item(i) for i in range(fdisc.bodies.count)]
    if len(caps) != 2:
        raise RuntimeError("expected 2 cap bodies, got %d" % len(caps))
    caps[0].name = "cap_a"
    caps[1].name = "cap_b"

    plb = ctx.plane_at_z("3.3 mm", "cap_boss_plane")
    skboss = root.sketches.add(plb)
    skboss.name = "cap_bosses"
    ctx.bound_circle(skboss, (CAP_X, 0, 0.33), 0.55, "11 mm",
                     x_pos="55 mm", v_pos="0 mm")
    ctx.bound_circle(skboss, (-CAP_X, 0, 0.33), 0.55, "11 mm",
                     x_pos="55 mm", v_pos="0 mm")
    vcaps0 = sum(b.volume for b in caps)
    binp = ctx.extrudes.createInput(ctx.all_profiles(skboss),
                                    ctx.ops.JoinFeatureOperation)
    ext2 = adsk.fusion.DistanceExtentDefinition.create(cbs("0.7 mm"))
    binp.setOneSideExtent(ext2, ctx.dirs.PositiveExtentDirection)
    binp.participantBodies = caps
    fboss = ctx.extrudes.add(binp)
    fboss.name = "cap_boss_extrude"
    if sum(b.volume for b in caps) - vcaps0 < 0.10:
        raise RuntimeError("boss join added too little volume")

    pls = ctx.plane_at_z("3.3 mm + 0.7 mm", "cap_stem_plane")
    skstem = root.sketches.add(pls)
    skstem.name = "cap_stems"
    ctx.bound_circle(skstem, (CAP_X, 0, 0.4), 0.405, "pr_stem_d",
                     x_pos="55 mm", v_pos="0 mm")
    ctx.bound_circle(skstem, (-CAP_X, 0, 0.4), 0.405, "pr_stem_d",
                     x_pos="55 mm", v_pos="0 mm")
    vcaps1 = sum(b.volume for b in caps)
    sinp = ctx.extrudes.createInput(ctx.all_profiles(skstem),
                                    ctx.ops.JoinFeatureOperation)
    ext3 = adsk.fusion.DistanceExtentDefinition.create(cbs("3 mm"))
    sinp.setOneSideExtent(ext3, ctx.dirs.PositiveExtentDirection)
    sinp.participantBodies = caps
    fstem = ctx.extrudes.add(sinp)
    fstem.name = "cap_stem_extrude"
    if sum(b.volume for b in caps) - vcaps1 < 0.2:
        raise RuntimeError("stem join added too little volume")
    print("FH caps done: %.3f + %.3f cm3"
          % (caps[0].volume, caps[1].volume))

    print("FH BUILD OK: spinner %.3f cm3, %d bodies"
          % (spinner.volume, root.bRepBodies.count))
