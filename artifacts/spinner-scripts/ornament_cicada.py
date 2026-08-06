"""Cicada 75 ornament pass - engraved detail only, zero functional
change: (1) 24 radial flutes on the rim top face aligned with the
silhouette crests (24-fold = matches the rim lobes, balance-neutral),
(2) two concentric ring grooves framing them, (3) 24 reeded flutes on
the stator cap top edge (the spec's own cosmetic reeding, added now).
All cuts are on top faces (no new overhangs) and clear of the journal,
float groove, tooth rings and rim inner wall. Depth: ci_engrave_d.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["ci_spoke_t", "ci_fuse_ch", "ci_rim_ch",
                    "ci_engrave_d"],
}
INTERFERENCE_ALLOWED = []

H = 1.4
FLUTE_R0, FLUTE_R1, FLUTE_W = 3.20, 3.46, 0.16   # rim band 30.5-37.5
RING_A_IN, RING_A_OUT = 3.12, 3.17
RING_B_IN, RING_B_OUT = 3.49, 3.54
REED_R0, REED_R1, REED_W = 1.18, 1.50, 0.10      # cap r15.5, dimple r7


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
            if k % 4 == 0:
                adsk.doEvents()
            prev = lines.addByTwoPoints(prev.endSketchPoint, spts[j])
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def run(_context: str):
    app = adsk.core.Application.get()
    target = None
    for i in range(app.documents.count):
        doc = app.documents.item(i)
        des = adsk.fusion.Design.cast(
            doc.products.itemByProductType("DesignProductType"))
        if des and des.rootComponent.bRepBodies.itemByName("ci_rotor"):
            target = doc
            break
    if target is None:
        raise RuntimeError("Cicada doc not found")
    target.activate()
    adsk.doEvents()

    ctx = BuildCtx(app)
    root = ctx.root
    pt = ctx.pt
    cbs = ctx.cbs
    rotor = root.bRepBodies.itemByName("ci_rotor")
    stator = root.bRepBodies.itemByName("ci_stator")

    ctx.up.add("ci_engrave_d", cbs("0.5 mm"), "mm", "engrave depth")

    plt = ctx.plane_at_z("14 mm", "engrave_plane")

    # 24 rim flutes, phased on the silhouette crests (cos(24t) peaks at 0)
    skf = root.sketches.add(plt)
    skf.name = "rim_flutes"
    _radial_bars(skf, pt, 24, FLUTE_R0, FLUTE_R1, FLUTE_W, 0.0, H)
    _fix_sketch(skf)
    if skf.profiles.count != 24:
        raise RuntimeError("flute profiles %d != 24" % skf.profiles.count)
    f1 = ctx.blind_cut(ctx.all_profiles(skf), "ci_engrave_d", [rotor],
                       "engrave_rim", min_vol_cm3=0.03)
    f1.name = "rim_flute_engrave"

    # two framing ring grooves
    skr = root.sketches.add(plt)
    skr.name = "rim_rings"
    ctx.bound_circle(skr, (0, 0, H), RING_A_IN, "62.4 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skr, (0, 0, H), RING_A_OUT, "63.4 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skr, (0, 0, H), RING_B_IN, "69.8 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(skr, (0, 0, H), RING_B_OUT, "70.8 mm",
                     x_pos="0 mm", v_pos="0 mm")
    rings = adsk.core.ObjectCollection.create()
    for p in skr.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
        a = p.areaProperties().area
        if 0.8 < a < 1.4:
            rings.add(p)
    if rings.count != 2:
        raise RuntimeError("ring groove profiles %d != 2" % rings.count)
    f2 = ctx.blind_cut(rings, "ci_engrave_d", [rotor],
                       "engrave_rim", min_vol_cm3=0.04)
    f2.name = "rim_ring_engrave"
    print("FH rim ornament done, rotor %.3f" % rotor.volume)

    # 24 cap reeds (cosmetic, spec's own)
    skc = root.sketches.add(plt)
    skc.name = "cap_reeds"
    _radial_bars(skc, pt, 24, REED_R0, REED_R1, REED_W, 7.5, H)
    _fix_sketch(skc)
    if skc.profiles.count != 24:
        raise RuntimeError("reed profiles %d != 24" % skc.profiles.count)
    f3 = ctx.blind_cut(ctx.all_profiles(skc), "ci_engrave_d", [stator],
                       "engrave_cap", min_vol_cm3=0.005)
    f3.name = "cap_reed_engrave"

    print("FH BUILD OK: ornament done, rotor %.3f stator %.3f"
          % (rotor.volume, stator.volume))
