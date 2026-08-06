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
FH_OPTS = {"liveness": False}
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

    print("FH P1 OK: stator %.3f cm3, %d bodies"
          % (stator.volume, root.bRepBodies.count))
