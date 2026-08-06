"""Pulsar Bloom 78 ornament pass - engraved detail plus the two finger
dimples the spec called for and the build skipped. Zero functional
change:
 (1) 12 radial flutes on the skirt top face, phased on the silhouette
     crests (12-fold = matches the skirt lobes, balance-neutral);
 (2) a framing ring groove inboard of them;
 (3) 4 chevron ticks on the arm top faces (4-fold, matches the carrier);
 (4) spec's pinch dimples: cap head top (dia 10 x 0.6) and stator base
     underside (dia 20 x 0.8) - comfort, no envelope change.
All top-face cuts (no new overhangs), all clear of gears, journals and
puck swing. Depth: pb_engrave_d.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 3
FH_OPTS = {
    "only_params": ["pb_plate_t", "pb_arm_t", "pb_puck_h", "pb_fuse_ch",
                    "pb_engrave_d"],
}
INTERFERENCE_ALLOWED = []

SKIRT_TOP = 1.33
ARM_TOP = 1.33
H = 1.45
FLUTE_R0, FLUTE_R1, FLUTE_W = 3.46, 3.75, 0.18   # skirt band 33.4-39.0
RING_IN, RING_OUT = 3.38, 3.43
TICK_R0, TICK_R1, TICK_W = 2.60, 3.20, 0.20      # on the arms (8 wide)


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


def _radial_bars(sk, pt, n, r0, r1, w, phase_deg, z):
    for k in range(n):
        az = math.radians(phase_deg + 360.0 * k / n)
        rhat = (math.cos(az), math.sin(az))
        that = (-math.sin(az), math.cos(az))
        corners = []
        for r, s in ((r0, -1), (r1, -1), (r1, 1), (r0, 1)):
            corners.append((r * rhat[0] + s * w / 2 * that[0],
                            r * rhat[1] + s * w / 2 * that[1]))
        spts = [sk.modelToSketchSpace(pt(x, y, z)) for x, y in corners]
        lines = sk.sketchCurves.sketchLines
        first = lines.addByTwoPoints(spts[0], spts[1])
        prev = first
        for j in range(2, 4):
            adsk.doEvents()
            prev = lines.addByTwoPoints(prev.endSketchPoint, spts[j])
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _axis_dimple(root, ctx, body, rim_r, depth, z_face, downward):
    """Spherical dimple on the main axis. downward=True cuts into -z
    from a top face; False cuts into +z from a bottom face."""
    pt, cbs = ctx.pt, ctx.cbs
    sph_r = (rim_r ** 2 + depth ** 2) / (2 * depth)
    if downward:
        z_apex = z_face - depth
        zc = z_apex + sph_r
    else:
        z_apex = z_face + depth
        zc = z_apex - sph_r
    skd = root.sketches.add(root.xZConstructionPlane)
    skd.name = "dimple_z%d" % int(round(z_face * 10))
    va = (0.0, z_apex - zc)
    vb = (rim_r, z_face - zc)
    ms = (va[0] + vb[0], va[1] + vb[1])
    mn = math.hypot(ms[0], ms[1])
    mid = (sph_r * ms[0] / mn, zc + sph_r * ms[1] / mn)
    dl = skd.sketchCurves.sketchLines
    ax_ln = dl.addByTwoPoints(skd.modelToSketchSpace(pt(0, 0, z_apex)),
                              skd.modelToSketchSpace(pt(0, 0, z_face)))
    face_ln = dl.addByTwoPoints(
        ax_ln.endSketchPoint, skd.modelToSketchSpace(pt(rim_r, 0, z_face)))
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
    if v0 - body.volume < 0.01:
        raise RuntimeError("dimple removed %.4f" % (v0 - body.volume))


def run(_context: str):
    app = adsk.core.Application.get()
    target = None
    for i in range(app.documents.count):
        doc = app.documents.item(i)
        des = adsk.fusion.Design.cast(
            doc.products.itemByProductType("DesignProductType"))
        if des and des.rootComponent.bRepBodies.itemByName("pb_rotor"):
            target = doc
            break
    if target is None:
        raise RuntimeError("Pulsar doc not found")
    target.activate()
    adsk.doEvents()

    ctx = BuildCtx(app)
    root = ctx.root
    pt = ctx.pt
    cbs = ctx.cbs
    rotor = root.bRepBodies.itemByName("pb_rotor")
    stator = root.bRepBodies.itemByName("pb_stator")

    ctx.up.add("pb_engrave_d", cbs("0.5 mm"), "mm", "engrave depth")

    plt = ctx.plane_at_z("13.3 mm", "engrave_plane")

    # 12 skirt flutes on the crests
    skf = root.sketches.add(plt)
    skf.name = "skirt_flutes"
    _radial_bars(skf, pt, 12, FLUTE_R0, FLUTE_R1, FLUTE_W, 0.0, SKIRT_TOP)
    _fix_sketch(skf)
    if skf.profiles.count != 12:
        raise RuntimeError("flute profiles %d != 12" % skf.profiles.count)
    f1 = ctx.blind_cut(ctx.all_profiles(skf), "pb_engrave_d", [rotor],
                       "engrave_skirt", min_vol_cm3=0.02)
    f1.name = "skirt_flute_engrave"

    # framing ring groove
    skr = root.sketches.add(plt)
    skr.name = "skirt_ring"
    ctx.bound_circle(skr, (0, 0, SKIRT_TOP), RING_IN, "67.6 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skr, (0, 0, SKIRT_TOP), RING_OUT, "68.6 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ring = None
    for p in skr.profiles:
        a = p.areaProperties().area
        if 0.8 < a < 1.6:
            ring = p
            break
    if ring is None:
        raise RuntimeError("no skirt ring profile")
    f2 = ctx.blind_cut(ring, "pb_engrave_d", [rotor], "engrave_skirt",
                       min_vol_cm3=0.02)
    f2.name = "skirt_ring_engrave"

    # 4 arm ticks (arms at 45 + 90k, 8 mm wide)
    ska = root.sketches.add(plt)
    ska.name = "arm_ticks"
    _radial_bars(ska, pt, 4, TICK_R0, TICK_R1, TICK_W, 45.0, ARM_TOP)
    _fix_sketch(ska)
    if ska.profiles.count != 4:
        raise RuntimeError("arm tick profiles %d != 4" % ska.profiles.count)
    f3 = ctx.blind_cut(ctx.all_profiles(ska), "pb_engrave_d", [rotor],
                       "engrave_skirt", min_vol_cm3=0.005)
    f3.name = "arm_tick_engrave"
    print("FH rotor ornament done, rotor %.3f" % rotor.volume)

    # spec's pinch dimples on the stator
    _axis_dimple(root, ctx, stator, 0.5, 0.06, H, True)     # head top
    _axis_dimple(root, ctx, stator, 1.0, 0.08, 0.0, False)  # base under
    print("FH BUILD OK: ornament done, rotor %.3f stator %.3f"
          % (rotor.volume, stator.volume))
