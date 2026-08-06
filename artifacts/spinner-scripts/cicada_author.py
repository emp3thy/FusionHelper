"""Cicada 75 - the spinner that talks back (tactile flagship, rank 2).

Two-body PiP on the verified diamond journal with a deliberate 1.6 mm
axial float. Tilt ribbed-cap-down and the rotor's 28-tooth flange loads
the cap's 28-tooth underside corrugation: pitch-coupled growl, analog
brake, audible speedometer (28 clicks/rev). Vertical spin plane rides
the ridge silently. At rest: axial castanet clack.

Spec deviation (fixes an internal inconsistency): cap raised so cap
teeth tips sit at z12.2 giving the stated 0.7 mm print-state tip gap to
the rotor teeth (spec's own z-stack produced 0.1 mm - would fuse).
Reeded cap-edge flutes omitted (cosmetic).

Bodies: ci_stator (core + ridge + toothed cap + dimples), ci_rotor
(float-groove sleeve + toothed flange + 4 spokes + 24-lobe rim).
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["ci_spoke_t", "ci_fuse_ch", "ci_rim_ch"],
}
INTERFERENCE_ALLOWED = []

# Fixed art constants (cm).
H = 1.4
CORE_R = 1.1
RIDGE_R = 1.22
RIDGE_Z = (0.55, 0.70, 0.85)     # 3.0 mm ridge
CLR = 0.025
BORE_R = CORE_R + CLR            # 1.125
GROOVE_R = RIDGE_R + CLR         # 1.245
GROOVE_Z0, GROOVE_Z1 = 0.57, 1.03   # 4.6 mm incl flanks -> 1.6 float
SLEEVE_R = 1.405
SLEEVE_TOP = 1.06
FLANGE_RIN, FLANGE_ROUT = 1.25, 1.53
ROT_TEETH_Z0, ROT_TEETH_Z1 = 1.09, 1.15   # rotor teeth band (tips z11.5)
CAP_TEETH_Z0, CAP_TEETH_Z1 = 1.22, 1.28   # cap teeth band (tips z12.2)
CAP_R = 1.55
CAP_Z0 = 1.28                    # cap disc z12.8-14.0
N_TEETH = 28
TOOTH_HALF_W = 0.06              # 45-deg V, depth 0.6
SPOKE_W = 0.3
RIM_RIN, RIM_ROUT = 3.05, 3.75
RIM_MEAN, RIM_AMP, RIM_N = 3.63, 0.12, 24


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


def _polyline(sk, pt, rz_pts):
    spts = [sk.modelToSketchSpace(pt(r, 0, z)) for r, z in rz_pts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _fixed_rect(sk, pt, x0, y0, x1, y1, z):
    p0 = sk.modelToSketchSpace(pt(x0, y0, z))
    p1 = sk.modelToSketchSpace(pt(x1, y1, z))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)


def _axis_dimple(root, ctx, body, rim_r, depth, z_face, into_minus_z):
    """Spherical finger dimple centered on the main axis."""
    pt, cbs = ctx.pt, ctx.cbs
    sph_r = (rim_r ** 2 + depth ** 2) / (2 * depth)
    if into_minus_z:          # top-face dimple: apex below face
        z_apex = z_face - depth
        zc = z_apex + sph_r   # sphere centre above
    else:                     # bottom-face dimple: apex above face
        z_apex = z_face + depth
        zc = z_apex - sph_r   # sphere centre below
    skd = root.sketches.add(root.xZConstructionPlane)
    skd.name = "dimple_z%.0f" % (z_face * 10)
    va = (0.0, z_apex - zc)
    vb = (rim_r, z_face - zc)
    ms = (va[0] + vb[0], va[1] + vb[1])
    mn = math.hypot(ms[0], ms[1])
    mid = (sph_r * ms[0] / mn, zc + sph_r * ms[1] / mn)
    dl = skd.sketchCurves.sketchLines
    ax_ln = dl.addByTwoPoints(skd.modelToSketchSpace(pt(0, 0, z_apex)),
                              skd.modelToSketchSpace(pt(0, 0, z_face)))
    face_ln = dl.addByTwoPoints(ax_ln.endSketchPoint,
                                skd.modelToSketchSpace(pt(rim_r, 0, z_face)))
    skd.sketchCurves.sketchArcs.addByThreePoints(
        face_ln.endSketchPoint,
        skd.modelToSketchSpace(pt(mid[0], 0, mid[1])),
        ax_ln.startSketchPoint)
    _fix_sketch(skd)
    if skd.profiles.count != 1:
        raise RuntimeError("dimple profiles %d" % skd.profiles.count)
    v0 = body.volume
    rev = root.features.revolveFeatures
    di = rev.createInput(skd.profiles.item(0), root.zConstructionAxis,
                         ctx.ops.CutFeatureOperation)
    di.setAngleExtent(False, cbs("360 deg"))
    di.participantBodies = [body]
    df = rev.add(di)
    df.name = skd.name + "_cut"
    if v0 - body.volume < 0.02:
        raise RuntimeError("dimple removed %.4f" % (v0 - body.volume))


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

    up.add("ci_spoke_t", cbs("3 mm"), "mm", "spoke thickness")
    up.add("ci_fuse_ch", cbs("0.3 mm"), "mm", "anti-fuse chamfer")
    up.add("ci_rim_ch", cbs("0.5 mm"), "mm", "rim inner edge chamfer")
    print("FH params added")

    # ---- stator (revolve): core + ridge + toothed cap -----------------
    sks = root.sketches.add(root.xZConstructionPlane)
    sks.name = "stator_profile"
    _polyline(sks, pt, [
        (0.0, 0.0), (CORE_R, 0.0),
        (CORE_R, RIDGE_Z[0]), (RIDGE_R, RIDGE_Z[1]), (CORE_R, RIDGE_Z[2]),
        (CORE_R, CAP_TEETH_Z0),
        (FLANGE_ROUT, CAP_TEETH_Z0), (FLANGE_ROUT, CAP_Z0),
        (CAP_R, CAP_Z0), (CAP_R, H), (0.0, H),
    ])
    _fix_sketch(sks)
    if sks.profiles.count != 1:
        raise RuntimeError("stator profiles %d" % sks.profiles.count)
    rinp = rev.createInput(sks.profiles.item(0), root.zConstructionAxis,
                           ctx.ops.NewBodyFeatureOperation)
    rinp.setAngleExtent(False, cbs("360 deg"))
    rf = rev.add(rinp)
    rf.name = "stator_revolve"
    stator = rf.bodies.item(0)
    stator.name = "ci_stator"
    if not (5.5 < stator.volume < 8.0):
        raise RuntimeError("stator vol %.3f" % stator.volume)
    _axis_dimple(root, ctx, stator, 0.7, 0.10, H, True)     # cap top d14
    _axis_dimple(root, ctx, stator, 0.6, 0.08, 0.0, False)  # bottom d12
    print("FH stator vol: %.3f" % stator.volume)

    # ---- rotor (revolve): float-groove sleeve + toothed flange --------
    skr = root.sketches.add(root.xZConstructionPlane)
    skr.name = "rotor_profile"
    _polyline(skr, pt, [
        (BORE_R, 0.0), (SLEEVE_R, 0.0),
        (SLEEVE_R, 0.94), (FLANGE_ROUT, 1.065), (FLANGE_ROUT, ROT_TEETH_Z1),
        (FLANGE_RIN, ROT_TEETH_Z1), (FLANGE_RIN, SLEEVE_TOP),
        (BORE_R, SLEEVE_TOP),
        (BORE_R, GROOVE_Z1), (GROOVE_R, GROOVE_Z1),
        (GROOVE_R, GROOVE_Z0), (BORE_R, GROOVE_Z0 - 0.12),
    ])
    _fix_sketch(skr)
    if skr.profiles.count != 1:
        raise RuntimeError("rotor profiles %d" % skr.profiles.count)
    rinp2 = rev.createInput(skr.profiles.item(0), root.zConstructionAxis,
                            ctx.ops.NewBodyFeatureOperation)
    rinp2.setAngleExtent(False, cbs("360 deg"))
    rf2 = rev.add(rinp2)
    rf2.name = "rotor_revolve"
    rotor = rf2.bodies.item(0)
    rotor.name = "ci_rotor"
    if not (1.6 < rotor.volume < 3.2):
        raise RuntimeError("rotor sleeve vol %.3f" % rotor.volume)
    print("FH rotor sleeve vol: %.3f" % rotor.volume)

    # ---- V-groove tooth cuts (seed pair + pattern x28) ----------------
    planes = root.constructionPlanes
    pin = planes.createInput()
    pin.setByOffset(root.xZConstructionPlane,
                    cbs("%.2f mm" % ((FLANGE_RIN + FLANGE_ROUT) / 2 * 10)))
    plv = planes.add(pin)
    plv.name = "tooth_band_plane"
    y_pl = plv.geometry.origin.y

    def v_groove_cut(name, z_open, z_apex, body):
        skv = root.sketches.add(plv)
        skv.name = name
        tri = [(-TOOTH_HALF_W, z_open), (TOOTH_HALF_W, z_open),
               (0.0, z_apex)]
        spts = [skv.modelToSketchSpace(pt(x, y_pl, z)) for x, z in tri]
        tl = skv.sketchCurves.sketchLines
        l1 = tl.addByTwoPoints(spts[0], spts[1])
        l2 = tl.addByTwoPoints(l1.endSketchPoint, spts[2])
        tl.addByTwoPoints(l2.endSketchPoint, l1.startSketchPoint)
        _fix_sketch(skv)
        if skv.profiles.count != 1:
            raise RuntimeError("%s profiles %d" % (name, skv.profiles.count))
        f = ctx.sym_cut(ctx.all_profiles(skv), "3.2 mm", [body],
                        min_vol_cm3=0.0008)
        f.name = name + "_cut"
        return f

    f_cap = v_groove_cut("cap_tooth", CAP_TEETH_Z0, CAP_TEETH_Z1, stator)
    f_rot = v_groove_cut("rotor_tooth", ROT_TEETH_Z1, ROT_TEETH_Z0, rotor)

    v0 = stator.volume + rotor.volume
    coll = adsk.core.ObjectCollection.create()
    coll.add(f_cap)
    coll.add(f_rot)
    cpats = root.features.circularPatternFeatures
    pinp = cpats.createInput(coll, root.zConstructionAxis)
    pinp.quantity = cbs(str(N_TEETH))
    pinp.totalAngle = cbs("360 deg")
    pinp.isSymmetric = False
    popts = adsk.fusion.PatternComputeOptions
    pinp.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pfc = cpats.add(pinp)
    dv = v0 - (stator.volume + rotor.volume)
    if pfc.healthState not in healthy or dv < 0.02:
        raise RuntimeError("tooth pattern dv=%.4f" % dv)
    pfc.name = "tooth_pattern"
    print("FH teeth done (pattern removed %.4f cm3)" % dv)

    # ---- spokes (4, axis-aligned fixed rects, one join) ---------------
    sksp = root.sketches.add(root.xYConstructionPlane)
    sksp.name = "spokes"
    _fixed_rect(sksp, pt, SLEEVE_R - 0.05, -SPOKE_W / 2, RIM_RIN + 0.05,
                SPOKE_W / 2, 0)
    _fixed_rect(sksp, pt, -(RIM_RIN + 0.05), -SPOKE_W / 2,
                -(SLEEVE_R - 0.05), SPOKE_W / 2, 0)
    _fixed_rect(sksp, pt, -SPOKE_W / 2, SLEEVE_R - 0.05, SPOKE_W / 2,
                RIM_RIN + 0.05, 0)
    _fixed_rect(sksp, pt, -SPOKE_W / 2, -(RIM_RIN + 0.05), SPOKE_W / 2,
                -(SLEEVE_R - 0.05), 0)
    _fix_sketch(sksp)
    v1 = rotor.volume
    spinp = ctx.extrudes.createInput(ctx.all_profiles(sksp),
                                     ctx.ops.JoinFeatureOperation)
    ext = adsk.fusion.DistanceExtentDefinition.create(cbs("ci_spoke_t"))
    spinp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
    spinp.participantBodies = [rotor]
    fsp = ctx.extrudes.add(spinp)
    fsp.name = "spoke_extrude"
    if rotor.volume - v1 < 0.4:
        raise RuntimeError("spokes added %.3f" % (rotor.volume - v1))
    print("FH spokes joined, rotor vol: %.3f" % rotor.volume)

    # ---- rim (24-lobe sinusoid outline + inner circle) ----------------
    skrim = root.sketches.add(root.xYConstructionPlane)
    skrim.name = "rim_outline"
    pts_c = adsk.core.ObjectCollection.create()
    n = 96
    for i in range(n + 1):
        th = 2 * math.pi * (i % n) / n
        r = RIM_MEAN + RIM_AMP * math.cos(RIM_N * th)
        pts_c.add(skrim.modelToSketchSpace(
            pt(r * math.cos(th), r * math.sin(th), 0)))
    skrim.sketchCurves.sketchFittedSplines.add(pts_c)
    ctx.bound_circle(skrim, (0, 0, 0), RIM_RIN, "61 mm",
                     x_pos="0 mm", v_pos="0 mm")
    _fix_sketch(skrim)
    rim_prof = None
    for p in skrim.profiles:
        a = p.areaProperties().area
        if 12.0 < a < 18.0:
            rim_prof = p
            break
    if rim_prof is None:
        raise RuntimeError("no rim annulus profile")
    v2 = rotor.volume
    rinp3 = ctx.extrudes.createInput(rim_prof, ctx.ops.JoinFeatureOperation)
    ext2 = adsk.fusion.DistanceExtentDefinition.create(cbs("14 mm"))
    rinp3.setOneSideExtent(ext2, ctx.dirs.PositiveExtentDirection)
    rinp3.participantBodies = [rotor]
    frim = ctx.extrudes.add(rinp3)
    frim.name = "rim_extrude"
    if rotor.volume - v2 < 14.0:
        raise RuntimeError("rim added %.3f" % (rotor.volume - v2))
    print("FH rim joined, rotor vol: %.3f" % rotor.volume)

    # ---- chamfers: rim inner edges + anti-fuse pair -------------------
    chf = root.features.chamferFeatures

    def circle_edges(bod, lo, hi, z_targets):
        out = adsk.core.ObjectCollection.create()
        for e in bod.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            g = e.geometry
            r = getattr(g, "radius", None)
            if r is None or not (lo < r < hi):
                continue
            bb = e.boundingBox
            if abs(bb.maxPoint.z - bb.minPoint.z) > 0.02:
                continue
            if any(abs(bb.minPoint.z - zt) < 0.02 for zt in z_targets):
                out.add(e)
        return out

    rim_edges = circle_edges(rotor, 3.0, 3.1, (H,))
    if rim_edges.count < 1:
        raise RuntimeError("rim inner top edge missing")
    ci1 = chf.createInput2()
    ci1.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        rim_edges, cbs("ci_rim_ch"), True)
    c1 = chf.add(ci1)
    c1.name = "rim_inner_chamfer"

    fuse = circle_edges(stator, 1.05, 1.15, (0.0,))
    for e in circle_edges(rotor, 1.10, 1.16, (0.0,)):  # fusionhelper: allow R11 — collection add, not a document mutation
        fuse.add(e)
    if fuse.count != 2:
        raise RuntimeError("anti-fuse edges %d != 2" % fuse.count)
    ci2 = chf.createInput2()
    ci2.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        fuse, cbs("ci_fuse_ch"), True)
    c2 = chf.add(ci2)
    c2.name = "antifuse_chamfer"

    print("FH BUILD OK: stator %.3f rotor %.3f cm3, %d bodies"
          % (stator.volume, rotor.volume, root.bRepBodies.count))
