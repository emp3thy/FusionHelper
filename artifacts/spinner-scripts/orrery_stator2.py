"""ORRERY 90 - stator, built the fast way and re-entrant.

The 50-tooth internal ring is NOT drawn as one 400-line outline: that
takes long enough to blow the MCP client timeout, and a timed-out request
is re-queued and runs again, duplicating geometry. Instead the wall is a
plain annulus whose bore sits at the tooth TIP radius, and a single tooth
SPACE is cut and circular-patterned x50 - about ten API calls instead of
four hundred.

Idempotent: every stage checks the committed volume first, so a re-entry
(orphaned retry, or a manual re-run) is a no-op rather than a duplicate.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 9
FH_OPTS = {"liveness": False}
INTERFERENCE_ALLOWED = []

H = 1.45
BASE_R = 2.90
BASE_T = 0.2
WALL_TOP = 1.10
# internal ring gear, module 1.0, 20 deg pressure angle
RING_N = 50
RING_TIP = 2.40
RING_ROOT = 2.625
RING_RP = 2.50
RING_RB = RING_RP * math.cos(math.radians(20))
BACKLASH = 0.012
POST_R, POST_RIDGE = 0.8, 0.92
POST_RIDGE_Z = (0.54, 0.66, 0.78)
STEM_R, HEAD_R = 0.6, 0.9
DIMPLE_RIM, DIMPLE_DEPTH = 0.5, 0.06


def _inv(a):
    return math.tan(a) - a


def _flank(psi_p, r):
    ap = math.acos(RING_RB / RING_RP)
    ar = math.acos(min(1.0, RING_RB / max(r, RING_RB)))
    return psi_p - _inv(ap) + _inv(ar)


def _tooth_space():
    """One space between two internal teeth, centred on the +X axis."""
    psi_p = math.pi / (2 * RING_N) - BACKLASH / (2 * RING_RP)
    half = math.pi / RING_N            # half the angular pitch
    rs = [RING_TIP, (RING_TIP + RING_ROOT) / 2, RING_ROOT]
    pts = []
    for r in rs:                        # one flank, tip -> root
        a = half - _flank(psi_p, r)
        pts.append((r * math.cos(a), r * math.sin(a)))
    for r in reversed(rs):              # the other, root -> tip
        a = -half + _flank(psi_p, r)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def _fix_sketch(sk):
    for c in sk.sketchCurves:
        if not c.isFixed:
            c.isFixed = True
    for sp in sk.sketchPoints:
        if not (sp.isFullyConstrained or sp.isFixed):
            sp.isFixed = True
    adsk.doEvents()


def _poly_xy(sk, pt, xy_pts, z):
    spts = [sk.modelToSketchSpace(pt(x, y, z)) for x, y in xy_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _poly_rz(sk, pt, rz_pts):
    spts = [sk.modelToSketchSpace(pt(r, 0, z)) for r, z in rz_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    adsk.doEvents()


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

    for nm, val, desc in (("or_base_t", "2 mm", "stator base thickness"),
                          ("or_fuse_ch", "0.3 mm", "anti-fuse chamfer")):
        if up.itemByName(nm) is None:
            up.add(nm, cbs(val), "mm", desc)

    body = root.bRepBodies.itemByName("or_stator")
    vol = body.volume if body else 0.0
    print("FH stator resume at %.3f cm3" % vol)

    # drop anything an aborted or duplicated run left behind
    for sk in list(root.sketches):
        adsk.doEvents()
        stale = ("(" in sk.name
                 or (vol < 11.0 and sk.name in ("ring_teeth", "wall_ring",
                                                "tooth_space"))
                 or (vol < 13.0 and sk.name == "post_profile"))
        if stale:
            print("FH dropping stale sketch:", sk.name)
            sk.deleteMe()

    # ---- stage 1: base disc -------------------------------------------
    if vol < 1.0:
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
        fb.bodies.item(0).name = "or_stator"
        print("FH base built")

    body = root.bRepBodies.itemByName("or_stator")

    # ---- stage 2: gear wall = annulus + one patterned tooth space -----
    if body.volume < 11.0:
        skw = root.sketches.add(root.xYConstructionPlane)
        skw.name = "wall_ring"
        ctx.bound_circle(skw, (0, 0, 0), RING_TIP, "48 mm",
                         x_pos="0 mm", v_pos="0 mm")
        ctx.bound_circle(skw, (0, 0, 0), BASE_R, "58 mm",
                         x_pos="0 mm", v_pos="0 mm")
        prof = None
        for p in skw.profiles:
            a = p.areaProperties().area
            if 8.0 < a < 12.0:
                prof = p
                break
        if prof is None:
            raise RuntimeError("no wall annulus profile")
        v0 = body.volume
        winp = ctx.extrudes.createInput(prof, ctx.ops.JoinFeatureOperation)
        winp.startExtent = adsk.fusion.OffsetStartDefinition.create(
            cbs("or_base_t"))
        wext = adsk.fusion.DistanceExtentDefinition.create(
            cbs("11 mm - or_base_t"))
        winp.setOneSideExtent(wext, ctx.dirs.PositiveExtentDirection)
        winp.participantBodies = [body]
        fw = ctx.extrudes.add(winp)
        fw.name = "wall_extrude"
        if body.volume - v0 < 3.0:
            raise RuntimeError("wall added %.3f" % (body.volume - v0))

        # the space must be cut over the WALL's z-band only. Sketching on
        # z0 and cutting upward also perforates the base disc AND leaves
        # the wall solid above the cut - measured: planets then foul the
        # uncut ring from z9 to z11.
        plt = ctx.plane_at_z("or_base_t", "tooth_plane")
        skt = root.sketches.add(plt)
        skt.name = "tooth_space"
        _poly_xy(skt, pt, _tooth_space(), BASE_T)
        _fix_sketch(skt)
        if skt.profiles.count != 1:
            raise RuntimeError("tooth space profiles %d"
                               % skt.profiles.count)
        fcut = ctx.blind_cut(ctx.all_profiles(skt), "11 mm - or_base_t",
                             [body], "tooth", min_vol_cm3=0.001)
        fcut.name = "tooth_space_cut"

        v1 = body.volume
        coll = adsk.core.ObjectCollection.create()
        coll.add(fcut)
        cpats = root.features.circularPatternFeatures
        pinp = cpats.createInput(coll, root.zConstructionAxis)
        pinp.quantity = cbs(str(RING_N))
        pinp.totalAngle = cbs("360 deg")
        pinp.isSymmetric = False
        popts = adsk.fusion.PatternComputeOptions
        pinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
        pf = cpats.add(pinp)
        if pf.healthState not in healthy or v1 - body.volume < 0.3:
            raise RuntimeError("tooth pattern dv=%.4f" % (v1 - body.volume))
        pf.name = "tooth_pattern"
        print("FH ring gear cut, vol %.3f" % body.volume)

    # ---- stage 3: journal post + finger dish ---------------------------
    if body.volume < 13.0:
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
        v2 = body.volume
        pinp2 = rev.createInput(skp.profiles.item(0),
                                root.zConstructionAxis,
                                ctx.ops.JoinFeatureOperation)
        pinp2.setAngleExtent(False, cbs("360 deg"))
        pinp2.participantBodies = [body]
        fp = rev.add(pinp2)
        fp.name = "post_revolve"
        if body.volume - v2 < 1.0:
            raise RuntimeError("post added %.3f" % (body.volume - v2))

        sph = (DIMPLE_RIM ** 2 + DIMPLE_DEPTH ** 2) / (2 * DIMPLE_DEPTH)
        z_ap = H - DIMPLE_DEPTH
        zc = z_ap + sph
        vb = (DIMPLE_RIM, H - zc)
        va = (0.0, z_ap - zc)
        ms = (va[0] + vb[0], va[1] + vb[1])
        mn = math.hypot(ms[0], ms[1])
        mid = (sph * ms[0] / mn, zc + sph * ms[1] / mn)
        skd = root.sketches.add(root.xZConstructionPlane)
        skd.name = "head_dish"
        dl = skd.sketchCurves.sketchLines
        axl = dl.addByTwoPoints(skd.modelToSketchSpace(pt(0, 0, z_ap)),
                                skd.modelToSketchSpace(pt(0, 0, H)))
        fl = dl.addByTwoPoints(
            axl.endSketchPoint,
            skd.modelToSketchSpace(pt(DIMPLE_RIM, 0, H)))
        skd.sketchCurves.sketchArcs.addByThreePoints(
            fl.endSketchPoint,
            skd.modelToSketchSpace(pt(mid[0], 0, mid[1])),
            axl.startSketchPoint)
        _fix_sketch(skd)
        v3 = body.volume
        di = rev.createInput(skd.profiles.item(0), root.zConstructionAxis,
                             ctx.ops.CutFeatureOperation)
        di.setAngleExtent(False, cbs("360 deg"))
        di.participantBodies = [body]
        dfe = rev.add(di)
        dfe.name = "head_dish_cut"
        if v3 - body.volume < 0.01:
            raise RuntimeError("dish removed %.4f" % (v3 - body.volume))

    print("FH ORRERY STATOR OK: %.3f cm3, %d bodies"
          % (body.volume, root.bRepBodies.count))
