"""ORRERY 90 - part 1: the stator.

A spinner with three kinds of motion at once. Inboard, a 50-tooth
internal ring drives five planet gears that whirl 3.33 turns per
revolution. Outboard, five cylinders sit in radial slots and fly out
5.5 mm under centrifugal force, locking against the rim race and going
silent. Twelve bodies, ten of them moving, all print-in-place.

Part 1 builds the stator: base disc, 50-tooth internal ring gear wall,
and the print-proven 45-degree diamond journal post. 50/5 = 10 teeth per
station, so every planet station meshes in phase.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {"liveness": False}
INTERFERENCE_ALLOWED = []

# ---- fixed art (cm) ----
H = 1.45
BASE_R = 2.90
BASE_T = 0.2
WALL_RIN, WALL_ROUT = 2.625, 2.90
TEETH_Z0 = 0.24
WALL_TOP = 1.10
# internal ring gear, module 1.0, 20 deg
RING_N = 50
RING_TIP = 2.40
RING_ROOT = 2.625
RING_RP = 2.50
RING_RB = RING_RP * math.cos(math.radians(20))
BACKLASH = 0.012
# centre journal post (verified 45-deg diamond recipe)
POST_R = 0.8
POST_RIDGE = 0.92
POST_RIDGE_Z = (0.54, 0.66, 0.78)
STEM_R = 0.6
HEAD_R = 0.9
DIMPLE_RIM, DIMPLE_DEPTH = 0.5, 0.06


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
        if i % 16 == 0:
            adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _poly_rz(sk, pt, rz_pts):
    spts = [sk.modelToSketchSpace(pt(r, 0, z)) for r, z in rz_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs
    rev = root.features.revolveFeatures

    up.add("or_base_t", cbs("2 mm"), "mm", "stator base thickness")
    up.add("or_fuse_ch", cbs("0.3 mm"), "mm", "anti-fuse chamfer")
    print("FH params added")

    def annulus_prof(sk, lo, hi):
        for p in sk.profiles:
            a = p.areaProperties().area
            if lo < a < hi:
                return p
        raise RuntimeError("no annulus profile (%.1f-%.1f)" % (lo, hi))

    # ---- base disc ----------------------------------------------------
    skb = root.sketches.add(root.xYConstructionPlane)
    skb.name = "base_disc"
    ctx.bound_circle(skb, (0, 0, 0), BASE_R, "58 mm",
                     x_pos="0 mm", v_pos="0 mm")
    dinp = ctx.extrudes.createInput(skb.profiles.item(0),
                                    ctx.ops.NewBodyFeatureOperation)
    ext = adsk.fusion.DistanceExtentDefinition.create(cbs("or_base_t"))
    dinp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
    fb = ctx.extrudes.add(dinp)
    fb.name = "base_extrude"
    stator = fb.bodies.item(0)
    stator.name = "or_stator"
    print("FH base vol: %.3f" % stator.volume)

    # ---- 55-tooth internal ring gear wall ------------------------------
    skt = root.sketches.add(root.xYConstructionPlane)
    skt.name = "ring_teeth"
    psi_ring = (math.pi / (2 * RING_N)
                - BACKLASH / (2 * RING_RP))
    ring_pts = _gear_outline(RING_N, RING_TIP, RING_ROOT, RING_RP,
                             RING_RB, psi_ring, True, math.pi / RING_N)
    _poly_xy(skt, pt, ring_pts, 0.0)
    ctx.bound_circle(skt, (0, 0, 0), WALL_ROUT, "58 mm",
                     x_pos="0 mm", v_pos="0 mm")
    _fix_sketch(skt)
    prof_t = annulus_prof(skt, 4.0, 10.0)
    v0 = stator.volume
    tinp = ctx.extrudes.createInput(prof_t, ctx.ops.JoinFeatureOperation)
    tinp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        cbs("or_base_t"))
    ext2 = adsk.fusion.DistanceExtentDefinition.create(
        cbs("11 mm - or_base_t"))
    tinp.setOneSideExtent(ext2, ctx.dirs.PositiveExtentDirection)
    tinp.participantBodies = [stator]
    ftt = ctx.extrudes.add(tinp)
    ftt.name = "ring_teeth_extrude"
    if stator.volume - v0 < 3.0:
        raise RuntimeError("ring teeth added %.3f" % (stator.volume - v0))
    print("FH ring gear vol: %.3f" % stator.volume)

    # ---- centre journal post (all faces vertical / top / 45 deg) ------
    skp = root.sketches.add(root.xZConstructionPlane)
    skp.name = "post_profile"
    _poly_rz(skp, pt, [
        (0.0, BASE_T), (POST_R, BASE_T),
        (POST_R, POST_RIDGE_Z[0]), (POST_RIDGE, POST_RIDGE_Z[1]),
        (POST_R, POST_RIDGE_Z[2]), (POST_R, 1.09),
        (STEM_R, 1.09), (STEM_R, H - (HEAD_R - STEM_R)),
        (HEAD_R, H), (0.0, H),
    ])
    _fix_sketch(skp)
    if skp.profiles.count != 1:
        raise RuntimeError("post profiles %d" % skp.profiles.count)
    v1 = stator.volume
    pinp = rev.createInput(skp.profiles.item(0), root.zConstructionAxis,
                           ctx.ops.JoinFeatureOperation)
    pinp.setAngleExtent(False, cbs("360 deg"))
    pinp.participantBodies = [stator]
    fpost = rev.add(pinp)
    fpost.name = "post_revolve"
    if stator.volume - v1 < 1.0:
        raise RuntimeError("post added %.3f" % (stator.volume - v1))

    # top finger dish (a cut into a top face - no overhang)
    sph_r = (DIMPLE_RIM ** 2 + DIMPLE_DEPTH ** 2) / (2 * DIMPLE_DEPTH)
    z_apex = H - DIMPLE_DEPTH
    zc = z_apex + sph_r
    va = (0.0, z_apex - zc)
    vb = (DIMPLE_RIM, H - zc)
    ms = (va[0] + vb[0], va[1] + vb[1])
    mn = math.hypot(ms[0], ms[1])
    mid = (sph_r * ms[0] / mn, zc + sph_r * ms[1] / mn)
    skd = root.sketches.add(root.xZConstructionPlane)
    skd.name = "head_dish"
    dl = skd.sketchCurves.sketchLines
    ax_ln = dl.addByTwoPoints(skd.modelToSketchSpace(pt(0, 0, z_apex)),
                              skd.modelToSketchSpace(pt(0, 0, H)))
    face_ln = dl.addByTwoPoints(
        ax_ln.endSketchPoint, skd.modelToSketchSpace(pt(DIMPLE_RIM, 0, H)))
    skd.sketchCurves.sketchArcs.addByThreePoints(
        face_ln.endSketchPoint,
        skd.modelToSketchSpace(pt(mid[0], 0, mid[1])),
        ax_ln.startSketchPoint)
    _fix_sketch(skd)
    if skd.profiles.count != 1:
        raise RuntimeError("dish profiles %d" % skd.profiles.count)
    v2 = stator.volume
    di = rev.createInput(skd.profiles.item(0), root.zConstructionAxis,
                         ctx.ops.CutFeatureOperation)
    di.setAngleExtent(False, cbs("360 deg"))
    di.participantBodies = [stator]
    dfe = rev.add(di)
    dfe.name = "head_dish_cut"
    if v2 - stator.volume < 0.01:
        raise RuntimeError("dish removed %.4f" % (v2 - stator.volume))

    print("FH ORRERY P1 OK: stator %.3f cm3, %d bodies"
          % (stator.volume, root.bRepBodies.count))
