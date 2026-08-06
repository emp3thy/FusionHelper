"""Supernova 72 ornament pass - engraved detail only, zero functional
change: (1) orbit ring groove on the rim top face (full circle =
axisymmetric, clear of scallop troughs), (2) six radial tick engraves on
the stator cap top at the roller azimuths (6-fold = balance-neutral,
outside the finger dimple). Depth is a live parameter sn_engrave_d.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["sn_floor_t", "sn_ceiling_t", "sn_g_float",
                    "sn_roll_d", "sn_cap_ch", "sn_fuse_ch",
                    "sn_engrave_d"],
}
INTERFERENCE_ALLOWED = []

GROOVE_RIN, GROOVE_ROUT = 3.33, 3.41   # rim top ring (silhouette min 3.46)
TICK_R0, TICK_R1, TICK_W = 0.95, 1.20, 0.15
H = 1.4


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
    target = None
    for i in range(app.documents.count):
        doc = app.documents.item(i)
        des = adsk.fusion.Design.cast(
            doc.products.itemByProductType("DesignProductType"))
        if des and des.rootComponent.bRepBodies.itemByName("sn_rotor"):
            target = doc
            break
    if target is None:
        raise RuntimeError("Supernova doc not found")
    target.activate()
    adsk.doEvents()

    ctx = BuildCtx(app)
    root = ctx.root
    pt = ctx.pt
    cbs = ctx.cbs
    rotor = root.bRepBodies.itemByName("sn_rotor")
    stator = root.bRepBodies.itemByName("sn_stator")

    ctx.up.add("sn_engrave_d", cbs("0.5 mm"), "mm", "engrave depth")

    # orbit ring groove on the rim top face
    plt = ctx.plane_at_z("14 mm", "engrave_plane")
    skr = root.sketches.add(plt)
    skr.name = "orbit_ring"
    ctx.bound_circle(skr, (0, 0, H), GROOVE_RIN, "66.6 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skr, (0, 0, H), GROOVE_ROUT, "68.2 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ring_prof = None
    for p in skr.profiles:
        a = p.areaProperties().area
        if 1.2 < a < 2.2:
            ring_prof = p
            break
    if ring_prof is None:
        raise RuntimeError("no ring groove profile")
    f1 = ctx.blind_cut(ring_prof, "sn_engrave_d", [rotor],
                       "engrave_ring", min_vol_cm3=0.05)
    f1.name = "orbit_ring_engrave"
    print("FH orbit ring engraved")

    # six cap ticks at the roller azimuths (90 + 60k)
    skt = root.sketches.add(plt)
    skt.name = "cap_ticks"
    for k in range(6):
        az = math.radians(90 + 60 * k)
        rhat = (math.cos(az), math.sin(az))
        that = (-math.sin(az), math.cos(az))
        corners = []
        for r, s in ((TICK_R0, -1), (TICK_R1, -1),
                     (TICK_R1, 1), (TICK_R0, 1)):
            corners.append((r * rhat[0] + s * TICK_W / 2 * that[0],
                            r * rhat[1] + s * TICK_W / 2 * that[1]))
        spts = [skt.modelToSketchSpace(pt(x, y, H)) for x, y in corners]
        lines = skt.sketchCurves.sketchLines
        first = lines.addByTwoPoints(spts[0], spts[1])
        prev = first
        for j in range(2, 4):
            adsk.doEvents()
            prev = lines.addByTwoPoints(prev.endSketchPoint, spts[j])
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    _fix_sketch(skt)
    if skt.profiles.count != 6:
        raise RuntimeError("tick profiles %d != 6" % skt.profiles.count)
    f2 = ctx.blind_cut(ctx.all_profiles(skt), "sn_engrave_d", [stator],
                       "engrave_tick", min_vol_cm3=0.005)
    f2.name = "cap_tick_engrave"
    print("FH BUILD OK: ornament done, rotor %.3f stator %.3f"
          % (rotor.volume, stator.volume))
