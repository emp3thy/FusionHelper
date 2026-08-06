"""Pulsar Bloom 78 - hidden-planetary hypotrochoid spinner (rank 3).

Stator: base disc + 56T internal ring gear wall + center diamond-journal
post with stem/cap-head. Rotor: fluted skirt + carrier plate + hub
sleeve + 4 risers + 4 arms + 4 mini diamond stubs. Four 14T planets
(profile-shifted, backlashed) ride the stubs; each carries an offset
puck. Carrier spin rolls the planets inside the fixed ring: the four
pucks trace a 4-lobed hypotrochoid - a breathing square fixed in the
hand's frame.

Gear outlines are fixed art: involute flanks approximated by 3-point
chords (leaderboard G-Man teeth are 'involute-ish'), backlash 0.12 mm
modeled, ring spaces centered on planet stations (56/4 integer => all
four stations mesh in phase; body-pattern rotation by 90 deg preserves
mesh AND radial puck aim).

Bodies: pb_stator, pb_rotor, pb_planet_1..4.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["pb_plate_t", "pb_arm_t", "pb_puck_h", "pb_fuse_ch"],
}
INTERFERENCE_ALLOWED = []

# Fixed art constants (cm).
H = 1.45
BASE_R = 3.29
BASE_T = 0.2
WALL_RIN, WALL_ROUT = 2.94, 3.28
TEETH_Z0, TEETH_Z1 = 0.24, 1.03
WALL_TOP = 1.10
# ring gear (internal, m=1 mm, 20 deg)
RING_N = 56
RING_TIP = 2.70
RING_ROOT = 2.94
RING_RP = 2.80
RING_RB = RING_RP * math.cos(math.radians(20))
# planet gear (external, 14T, +0.3 shift per spec tip/root)
PL_N = 14
PL_TIP = 0.80
PL_ROOT = 0.575
PL_RP = 0.70
PL_RB = PL_RP * math.cos(math.radians(20))
BACKLASH = 0.012
STATION_R = 2.10
# center journal post
POST_R = 0.8
POST_RIDGE = 0.92
POST_RIDGE_Z = (0.54, 0.66, 0.78)
STEM_R = 0.6
HEAD_R = 0.9
# rotor
SKIRT_RIN = 3.34
SKIRT_MEAN, SKIRT_AMP, SKIRT_N = 3.825, 0.075, 12
SKIRT_TOP = 1.33
PLATE_RIN, PLATE_ROUT = 1.105, 2.67
HUB_BORE = 0.825
HUB_GROOVE = 0.945
HUB_OD = 1.105
RISER_R0, RISER_R1, RISER_W = 2.25, 2.65, 0.4
ARM_R0, ARM_R1, ARM_W = 2.25, 3.50, 0.8
# stubs + planet bore
STUB_R = 0.26
STUB_RIDGE = 0.34
STUB_Z0, STUB_Z1 = 0.43, 1.03
STUB_RIDGE_Z = (0.67, 0.73, 0.79)
PL_Z0, PL_Z1 = 0.46, 1.06
PL_BORE = 0.29
PL_GROOVE = 0.37
PL_BORE_TOP = 1.04
PUCK_R = 0.25
PUCK_OFF = 0.53


def _inv(a):
    return math.tan(a) - a


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


def _polyline_pts(sk, pt, xy_pts, z):
    spts = [sk.modelToSketchSpace(pt(x, y, z)) for x, y in xy_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        if i % 8 == 0:
            adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _rz_polyline(sk, pt, rz_pts, x_axis_offset=0.0):
    """Half-profile polyline on a vertical plane; r offsets from the
    local axis at x = x_axis_offset."""
    spts = [sk.modelToSketchSpace(pt(x_axis_offset + r, 0, z))
            for r, z in rz_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    return first


def _flank_angle(psi_p, rp, rb, r, internal):
    ap = math.acos(rb / rp)
    ar = math.acos(min(1.0, rb / max(r, rb)))
    if internal:
        return psi_p - _inv(ap) + _inv(ar)
    return psi_p + _inv(ap) - _inv(ar)


def _gear_outline(N, r_tip, r_root, rp, rb, psi_p, internal,
                  phase):
    """CCW point list. External: teeth outward (tip>root). Internal:
    teeth inward (tip<root), outline used as an inner boundary."""
    pts = []
    lo, hi = (r_tip, r_root) if internal else (r_root, r_tip)
    # radii sampled along the flank from root side to tip side
    if internal:
        flank_rs = [r_root, (r_root + r_tip) / 2, r_tip]
    else:
        start = max(r_root, rb + 1e-4)
        flank_rs = [start, (start + r_tip) / 2, r_tip]
    for k in range(N):
        c = phase + 2 * math.pi * k / N
        pitch = 2 * math.pi / N
        # root point before the tooth
        psi_root = _flank_angle(psi_p, rp, rb, flank_rs[0], internal)
        pts.append((r_root * math.cos(c - pitch / 2),
                    r_root * math.sin(c - pitch / 2)))
        if not internal and r_root < rb:
            pts.append((r_root * math.cos(c - psi_root),
                        r_root * math.sin(c - psi_root)))
        for r in flank_rs:
            a = c - _flank_angle(psi_p, rp, rb, r, internal)
            pts.append((r * math.cos(a), r * math.sin(a)))
        psi_tip = _flank_angle(psi_p, rp, rb, flank_rs[-1], internal)
        for r in reversed(flank_rs):
            a = c + _flank_angle(psi_p, rp, rb, r, internal)
            pts.append((r * math.cos(a), r * math.sin(a)))
        if not internal and r_root < rb:
            pts.append((r_root * math.cos(c + psi_root),
                        r_root * math.sin(c + psi_root)))
    return pts


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs
    rev = root.features.revolveFeatures
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    up.add("pb_plate_t", cbs("2 mm"), "mm", "carrier plate thickness")
    up.add("pb_arm_t", cbs("2 mm"), "mm", "arm thickness")
    up.add("pb_puck_h", cbs("2.9 mm"), "mm", "puck height")
    up.add("pb_fuse_ch", cbs("0.3 mm"), "mm", "anti-fuse chamfer")
    print("FH params added")

    def annulus_prof(sk, lo, hi):
        for p in sk.profiles:
            a = p.areaProperties().area
            if lo < a < hi:
                return p
        raise RuntimeError("no annulus profile (%.1f-%.1f)" % (lo, hi))

    def extrude_join(prof, dist_expr, target, min_dv, name,
                     start_expr=None):
        v0 = target.volume
        inp = ctx.extrudes.createInput(prof, ctx.ops.JoinFeatureOperation)
        if start_expr is not None:
            inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
                cbs(start_expr))
        ext = adsk.fusion.DistanceExtentDefinition.create(cbs(dist_expr))
        inp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
        inp.participantBodies = [target]
        f = ctx.extrudes.add(inp)
        f.name = name
        if target.volume - v0 < min_dv:
            raise RuntimeError("%s added %.4f" % (name, target.volume - v0))
        return f

    # ================= STATOR =========================================
    skb = root.sketches.add(root.xYConstructionPlane)
    skb.name = "base_disc"
    ctx.bound_circle(skb, (0, 0, 0), BASE_R, "65.8 mm",
                     x_pos="0 mm", v_pos="0 mm")
    dinp = ctx.extrudes.createInput(skb.profiles.item(0),
                                    ctx.ops.NewBodyFeatureOperation)
    ext = adsk.fusion.DistanceExtentDefinition.create(cbs("2 mm"))
    dinp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
    fb = ctx.extrudes.add(dinp)
    fb.name = "base_extrude"
    stator = fb.bodies.item(0)
    stator.name = "pb_stator"

    # ring wall: smooth band, toothed band, counterbore band
    skw1 = root.sketches.add(root.xYConstructionPlane)
    skw1.name = "wall_smooth"
    ctx.bound_circle(skw1, (0, 0, 0), WALL_RIN, "58.8 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skw1, (0, 0, 0), WALL_ROUT, "65.6 mm",
                     x_pos="0 mm", v_pos="0 mm")
    prof_w = annulus_prof(skw1, 5.0, 8.0)
    extrude_join(prof_w, "0.4 mm", stator, 0.2, "wall_lower",
                 start_expr="2 mm")

    # toothed band: outer circle + internal-tooth outline
    skt = root.sketches.add(root.xYConstructionPlane)
    skt.name = "ring_teeth"
    psi_ring = (math.pi / (2 * RING_N)
                - (2 * 0.03 * math.tan(math.radians(20))) / RING_N
                - BACKLASH / (2 * RING_RP))
    ring_pts = _gear_outline(RING_N, RING_TIP, RING_ROOT, RING_RP,
                             RING_RB, psi_ring, True,
                             math.pi / RING_N)
    _polyline_pts(skt, pt, ring_pts, 0.0)
    ctx.bound_circle(skt, (0, 0, 0), WALL_ROUT, "65.6 mm",
                     x_pos="0 mm", v_pos="0 mm")
    _fix_sketch(skt)
    prof_t = annulus_prof(skt, 5.0, 9.5)
    extrude_join(prof_t, "7.9 mm", stator, 3.5, "ring_teeth_extrude",
                 start_expr="2.4 mm")

    skw2 = root.sketches.add(root.xYConstructionPlane)
    skw2.name = "wall_counterbore"
    ctx.bound_circle(skw2, (0, 0, 0), WALL_RIN, "58.8 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skw2, (0, 0, 0), WALL_ROUT, "65.6 mm",
                     x_pos="0 mm", v_pos="0 mm")
    prof_w2 = annulus_prof(skw2, 5.0, 8.0)
    extrude_join(prof_w2, "0.7 mm", stator, 0.3, "wall_upper",
                 start_expr="10.3 mm")
    print("FH stator wall done vol: %.3f" % stator.volume)

    # center post (revolve join): column + ridge + stem + cap head
    skp = root.sketches.add(root.xZConstructionPlane)
    skp.name = "post_profile"
    _rz_polyline(skp, pt, [
        (0.0, BASE_T), (POST_R, BASE_T),
        (POST_R, POST_RIDGE_Z[0]), (POST_RIDGE, POST_RIDGE_Z[1]),
        (POST_R, POST_RIDGE_Z[2]), (POST_R, 1.09),
        (STEM_R, 1.09), (STEM_R, 1.30),
        (HEAD_R, 1.30), (HEAD_R, H), (0.0, H),
    ])
    _fix_sketch(skp)
    if skp.profiles.count != 1:
        raise RuntimeError("post profiles %d" % skp.profiles.count)
    v0 = stator.volume
    pinp = rev.createInput(skp.profiles.item(0), root.zConstructionAxis,
                           ctx.ops.JoinFeatureOperation)
    pinp.setAngleExtent(False, cbs("360 deg"))
    pinp.participantBodies = [stator]
    fpost = rev.add(pinp)
    fpost.name = "post_revolve"
    if stator.volume - v0 < 1.0:
        raise RuntimeError("post added %.3f" % (stator.volume - v0))
    print("FH stator vol: %.3f" % stator.volume)

    # ================= ROTOR ==========================================
    # hub sleeve (revolve, new body - becomes pb_rotor after arms merge)
    skh = root.sketches.add(root.xZConstructionPlane)
    skh.name = "hub_profile"
    _rz_polyline(skh, pt, [
        (HUB_BORE, 0.23), (HUB_OD, 0.23), (HUB_OD, 1.09),
        (HUB_BORE, 1.09),
        (HUB_BORE, POST_RIDGE_Z[2]), (HUB_GROOVE, POST_RIDGE_Z[1]),
        (HUB_BORE, POST_RIDGE_Z[0]),
    ])
    _fix_sketch(skh)
    if skh.profiles.count != 1:
        raise RuntimeError("hub profiles %d" % skh.profiles.count)
    hinp = rev.createInput(skh.profiles.item(0), root.zConstructionAxis,
                           ctx.ops.NewBodyFeatureOperation)
    hinp.setAngleExtent(False, cbs("360 deg"))
    fhub = rev.add(hinp)
    fhub.name = "hub_revolve"
    rotor = fhub.bodies.item(0)
    rotor.name = "pb_rotor"

    # carrier plate
    plp = ctx.plane_at_z("2.3 mm", "plate_plane")
    skpl = root.sketches.add(plp)
    skpl.name = "carrier_plate"
    ctx.bound_circle(skpl, (0, 0, 0.23), PLATE_RIN, "22.1 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skpl, (0, 0, 0.23), PLATE_ROUT, "53.4 mm",
                     x_pos="0 mm", v_pos="0 mm")
    prof_pl = annulus_prof(skpl, 15.0, 22.0)
    extrude_join(prof_pl, "pb_plate_t", rotor, 2.5, "plate_extrude")

    # risers x4 at 45+90k (rotated fixed rects)
    plr = ctx.plane_at_z("4.3 mm", "riser_plane")
    skri = root.sketches.add(plr)
    skri.name = "risers"
    for k in range(4):
        az = math.radians(45 + 90 * k)
        rhat = (math.cos(az), math.sin(az))
        that = (-math.sin(az), math.cos(az))
        corners = []
        for r, s in ((RISER_R0, -1), (RISER_R1, -1),
                     (RISER_R1, 1), (RISER_R0, 1)):
            corners.append((r * rhat[0] + s * RISER_W / 2 * that[0],
                            r * rhat[1] + s * RISER_W / 2 * that[1]))
        _polyline_pts(skri, pt, corners, 0.43)
    _fix_sketch(skri)
    extrude_join(ctx.all_profiles(skri), "7 mm", rotor, 0.3,
                 "riser_extrude")
    print("FH rotor core vol: %.3f" % rotor.volume)

    # stubs x4 on the two principal vertical planes
    for az_deg, plane, sgn in ((0, root.xZConstructionPlane, 1),
                               (180, root.xZConstructionPlane, -1),
                               (90, root.yZConstructionPlane, 1),
                               (270, root.yZConstructionPlane, -1)):
        adsk.doEvents()
        sk_st = root.sketches.add(plane)
        sk_st.name = "stub_%d" % az_deg
        if plane == root.xZConstructionPlane:
            mk = lambda r, z: pt(sgn * (STATION_R + r), 0, z)
        else:
            mk = lambda r, z: pt(0, sgn * (STATION_R + r), z)
        spts = [sk_st.modelToSketchSpace(mk(r, z)) for r, z in [
            (0.0, STUB_Z0), (STUB_R, STUB_Z0),
            (STUB_R, STUB_RIDGE_Z[0]), (STUB_RIDGE, STUB_RIDGE_Z[1]),
            (STUB_R, STUB_RIDGE_Z[2]), (STUB_R, STUB_Z1),
            (0.0, STUB_Z1),
        ]]
        lines = sk_st.sketchCurves.sketchLines
        first = lines.addByTwoPoints(spts[0], spts[1])
        prev = first
        for i in range(2, len(spts)):
            adsk.doEvents()
            prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
        axis_ln = lines.addByTwoPoints(prev.endSketchPoint,
                                       first.startSketchPoint)
        _fix_sketch(sk_st)
        if sk_st.profiles.count != 1:
            raise RuntimeError("stub %d profiles %d"
                               % (az_deg, sk_st.profiles.count))
        v1 = rotor.volume
        sinp = rev.createInput(sk_st.profiles.item(0), axis_ln,
                               ctx.ops.JoinFeatureOperation)
        sinp.setAngleExtent(False, cbs("360 deg"))
        sinp.participantBodies = [rotor]
        fst = rev.add(sinp)
        fst.name = "stub_%d_revolve" % az_deg
        if rotor.volume - v1 < 0.04:
            raise RuntimeError("stub %d added %.4f"
                               % (az_deg, rotor.volume - v1))
    print("FH stubs done vol: %.3f" % rotor.volume)

    # skirt (separate body until arms merge)
    sksk = root.sketches.add(root.xYConstructionPlane)
    sksk.name = "skirt_outline"
    pts_c = adsk.core.ObjectCollection.create()
    n = 96
    for i in range(n + 1):
        th = 2 * math.pi * (i % n) / n
        r = SKIRT_MEAN + SKIRT_AMP * math.cos(SKIRT_N * th)
        pts_c.add(sksk.modelToSketchSpace(
            pt(r * math.cos(th), r * math.sin(th), 0)))
    sksk.sketchCurves.sketchFittedSplines.add(pts_c)
    ctx.bound_circle(sksk, (0, 0, 0), SKIRT_RIN, "66.8 mm",
                     x_pos="0 mm", v_pos="0 mm")
    _fix_sketch(sksk)
    prof_sk = annulus_prof(sksk, 8.0, 13.0)
    skinp = ctx.extrudes.createInput(prof_sk,
                                     ctx.ops.NewBodyFeatureOperation)
    ext_sk = adsk.fusion.DistanceExtentDefinition.create(cbs("13.3 mm"))
    skinp.setOneSideExtent(ext_sk, ctx.dirs.PositiveExtentDirection)
    fsk = ctx.extrudes.add(skinp)
    fsk.name = "skirt_extrude"
    skirt = fsk.bodies.item(0)
    if not (10.0 < skirt.volume < 18.0):
        raise RuntimeError("skirt vol %.3f" % skirt.volume)

    # arms x4 at 45+90k, z11.3-13.3, merge hub-core and skirt
    pla = ctx.plane_at_z("11.3 mm", "arm_plane")
    ska = root.sketches.add(pla)
    ska.name = "arms"
    for k in range(4):
        az = math.radians(45 + 90 * k)
        rhat = (math.cos(az), math.sin(az))
        that = (-math.sin(az), math.cos(az))
        corners = []
        for r, s in ((ARM_R0, -1), (ARM_R1, -1), (ARM_R1, 1), (ARM_R0, 1)):
            corners.append((r * rhat[0] + s * ARM_W / 2 * that[0],
                            r * rhat[1] + s * ARM_W / 2 * that[1]))
        _polyline_pts(ska, pt, corners, 1.13)
    _fix_sketch(ska)
    v2 = rotor.volume + skirt.volume
    ainp = ctx.extrudes.createInput(ctx.all_profiles(ska),
                                    ctx.ops.JoinFeatureOperation)
    ext_a = adsk.fusion.DistanceExtentDefinition.create(cbs("pb_arm_t"))
    ainp.setOneSideExtent(ext_a, ctx.dirs.PositiveExtentDirection)
    ainp.participantBodies = [rotor, skirt]
    farm = ctx.extrudes.add(ainp)
    farm.name = "arm_extrude"
    rotor = root.bRepBodies.itemByName("pb_rotor")
    if rotor is None:
        raise RuntimeError("rotor lost after arm merge")
    if rotor.volume < v2:
        raise RuntimeError("arm merge lost volume (%.3f < %.3f)"
                           % (rotor.volume, v2))
    print("FH rotor merged vol: %.3f, bodies %d"
          % (rotor.volume, root.bRepBodies.count))

    # ================= PLANETS ========================================
    skg = root.sketches.add(root.xYConstructionPlane)
    skg.name = "planet_gear"
    psi_pl = (math.pi / (2 * PL_N)
              + (2 * 0.03 * math.tan(math.radians(20))) / PL_N
              - BACKLASH / (2 * PL_RP))
    pl_pts = [(STATION_R + x, y) for x, y in _gear_outline(
        PL_N, PL_TIP, PL_ROOT, PL_RP, PL_RB, psi_pl, False, 0.0)]
    _polyline_pts(skg, pt, pl_pts, 0.0)
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

    # blind bore + groove (revolve cut about the station-0 local axis)
    skpb = root.sketches.add(root.xZConstructionPlane)
    skpb.name = "planet_bore"
    bore_first = _rz_polyline(skpb, pt, [
        (0.0, PL_Z0), (PL_BORE, PL_Z0),
        (PL_BORE, STUB_RIDGE_Z[0]), (PL_GROOVE, STUB_RIDGE_Z[1]),
        (PL_BORE, STUB_RIDGE_Z[2]), (PL_BORE, PL_BORE_TOP),
        (0.0, PL_BORE_TOP),
    ], x_axis_offset=STATION_R)
    _fix_sketch(skpb)
    if skpb.profiles.count != 1:
        raise RuntimeError("planet bore profiles %d" % skpb.profiles.count)
    axis_line = None
    for ln in skpb.sketchCurves.sketchLines:
        s = skpb.sketchToModelSpace(ln.startSketchPoint.geometry)
        e = skpb.sketchToModelSpace(ln.endSketchPoint.geometry)
        if (abs(s.x - STATION_R) < 1e-4 and abs(e.x - STATION_R) < 1e-4
                and abs(s.y) < 1e-4 and abs(e.y) < 1e-4):
            axis_line = ln
            break
    if axis_line is None:
        raise RuntimeError("planet bore axis line not found")
    v3 = planet.volume
    binp = rev.createInput(skpb.profiles.item(0), axis_line,
                           ctx.ops.CutFeatureOperation)
    binp.setAngleExtent(False, cbs("360 deg"))
    binp.participantBodies = [planet]
    fbore = rev.add(binp)
    fbore.name = "planet_bore_cut"
    if v3 - planet.volume < 0.1:
        raise RuntimeError("bore removed %.4f" % (v3 - planet.volume))

    # puck
    skpk = root.sketches.add(root.xYConstructionPlane)
    skpk.name = "puck"
    ctx.bound_circle(skpk, (STATION_R + PUCK_OFF, 0, 0), PUCK_R, "5 mm",
                     x_pos="26.3 mm", v_pos="0 mm")
    extrude_join(ctx.all_profiles(skpk), "pb_puck_h", planet, 0.03,
                 "puck_extrude", start_expr="10.6 mm")
    print("FH planet vol: %.3f" % planet.volume)

    # body pattern x4 (90 deg spacing preserves mesh: 56/4 integer)
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

    # ---- anti-fuse chamfers at the bed-level radial gap ---------------
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
