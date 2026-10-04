"""HEX - honeycomb wine rack for a 335 x 335 mm cube opening (modern).

One confident idea: a single hexagonal ring, printed flat, repeated.

    3 - 2 - 3 honeycomb of pointy-top rings, 8 bottles, two plates
    (back + front) of 8 rings each, tied by double-dovetail keys that
    run the full rack depth, standing on a zig-zag base rail.

Why hex over a 3 x 3 square grid (which holds 9):
  - every pointy-top cell is a 120 deg V-cradle: two-line contact for
    any diameter from 74 to 96 mm, no separate saddle, nothing rolls;
  - every cell carries its bottle in the hoop of a flat-printed ring
    (load in XY, the proven architecture), and the middle row bears on
    the diagonal flats of the row below in pure compression - the keys
    only stop the lattice spreading;
  - one part type for all 16 cells, one key for all 19 joints, one
    rail for the two plinths; capacity cost is one bottle (8 vs 9).

Module list (all bodies in this document are print-oriented, show face
on the bed):
  hex_ring_1..4      one plate's worth of rings (4 plates = 16 rings)
  hex_key_1..10      one plate of keys (two plates = 19 + 1 spare)
  hex_rail_1..2      the two base rails (print on the bed diagonal)
  hex_coupon_block / hex_coupon_key   dovetail tolerance coupon

Joint: double-dovetail (bow-tie) key, 20 deg flanks, 4 mm deep each
side, 0.25 mm clearance per side (brief: sliding dovetail 0.20-0.30).
Grooves are BLIND: floor 3 mm behind the show face, so no key end is
ever visible and no key can leave the lattice once both plates are on.
Key and ring are both symmetric: there is no backwards.

Every dimension is an expression of the parameter table below; the
sketches pin every vertex to the sketch origin with bound distance
dimensions (unsigned - the seed chooses the side), so a parameter
edit moves everything.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": [
        "space_w", "fit_gap", "edge_gap", "wall_t", "ring_d", "floor_t",
        "rack_d", "dt_neck", "dt_d", "dt_ang", "dt_gap", "grv_over",
        "base_t", "ch_reveal", "ch_flare", "cp_w", "cp_h", "cp_key_len",
        "lay_gap", "lay_key_x", "lay_rail_y", "lay_cp_y",
    ],
    "liveness_budget_s": 120,
    "max_bodies": 40,
}
INTERFERENCE_ALLOWED = []

SQ3 = math.sqrt(3.0)

# ---- parameter table: (name, expression, unit, what it drives) ----------
# Root values first, derived expressions after; one value stated once.
PARAMS = (
    ("space_w", "335 mm", "mm", "opening width and height"),
    ("fit_gap", "1.5 mm", "mm", "clearance per side to the opening"),
    ("edge_gap", "1 mm", "mm", "honeycomb-to-envelope reveal per side"),
    ("wall_t", "7 mm", "mm", "ring wall (two rings meet: 14 mm web)"),
    ("ring_d", "30 mm", "mm", "ring depth = print height"),
    ("floor_t", "3 mm", "mm", "blind-groove floor behind the show face"),
    ("rack_d", "180 mm", "mm", "overall rack depth, back face to front face"),
    ("dt_neck", "10 mm", "mm", "dovetail neck width at the interface"),
    ("dt_d", "4 mm", "mm", "dovetail depth into each wall"),
    ("dt_ang", "20 deg", "deg", "dovetail flank angle from the depth axis"),
    ("dt_gap", "0.25 mm", "mm", "groove clearance per side (coupon tunes this)"),
    ("grv_over", "0.6 mm", "mm", "groove profile overshoot outside the flat"),
    ("base_t", "6 mm", "mm", "rail thickness under a ring vertex"),
    ("ch_reveal", "1 mm", "mm", "show-face chamfer: the seam reveal"),
    ("ch_flare", "2.5 mm", "mm", "cell entry flare on the show face"),
    ("cp_w", "30 mm", "mm", "coupon block width"),
    ("cp_h", "20 mm", "mm", "coupon block height"),
    ("cp_key_len", "40 mm", "mm", "coupon key length"),
    ("lay_gap", "6 mm", "mm", "plate layout gap between parts"),
    ("lay_key_x", "220 mm", "mm", "layout: keys start at this x"),
    ("lay_rail_y", "250 mm", "mm", "layout: rail bottom edge this far below origin"),
    ("lay_cp_y", "250 mm", "mm", "layout: coupon this far above origin"),
    # derived
    ("rack_w", "space_w - 2 * fit_gap", "mm", "rack envelope (332)"),
    ("pitch", "(rack_w - 2 * edge_gap) / 3", "mm", "cell pitch = ring outer flat-to-flat"),
    ("slot_clear", "pitch - 2 * wall_t", "mm", "clear slot, flat-to-flat (96)"),
    ("hex_r", "pitch / sqrt(3)", "mm", "ring outer circumradius"),
    ("hex_ri", "slot_clear / sqrt(3)", "mm", "ring inner circumradius"),
    ("hex_v", "2 * hex_r", "mm", "ring vertex-to-vertex height"),
    ("notch_h", "hex_r / 2", "mm", "rise of a lower flat above the bottom vertex"),
    ("rack_h", "2 * notch_h * 3 + hex_v + base_t", "mm", "rack overall height (check < rack_w)"),
    ("key_len", "rack_d - 2 * floor_t", "mm", "key length, floor to floor"),
    ("dt_base", "dt_neck + 2 * dt_d * tan(dt_ang)", "mm", "dovetail base width"),
    ("grv_d", "dt_d + dt_gap", "mm", "groove depth from the flat"),
    ("grv_neck", "dt_neck + 2 * dt_gap / cos(dt_ang)", "mm", "groove opening at the flat"),
    ("grv_base", "dt_base + 2 * dt_gap * (tan(dt_ang) + 1 / cos(dt_ang))", "mm",
     "groove base width"),
    ("grv_cut", "ring_d - floor_t", "mm", "groove cut depth from the mouth"),
    ("rail_w", "3 * pitch", "mm", "base rail length (330, print diagonal)"),
    ("rail_h", "base_t + notch_h", "mm", "base rail height at a notch"),
)


class SkMap:
    """Runtime map between world axes and this sketch's local axes (R6).
    Points are pinned to the sketch origin with bound distance dims;
    a None coordinate means 'on the origin's axis line' (constraint)."""

    def __init__(self, ctx, sk):
        self.ctx = ctx
        self.sk = sk
        pt = ctx.pt
        o = sk.modelToSketchSpace(pt(0.0, 0.0, 0.0))
        self.o = o
        self.axis = {}
        for name, w in (("x", (1.0, 0.0, 0.0)), ("y", (0.0, 1.0, 0.0)),
                        ("z", (0.0, 0.0, 1.0))):
            q = sk.modelToSketchSpace(pt(w[0], w[1], w[2]))
            dx, dy = q.x - o.x, q.y - o.y
            if abs(dx) > 0.5:
                self.axis[name] = "h"
            elif abs(dy) > 0.5:
                self.axis[name] = "v"

    def local(self, wx_mm, wy_mm, wz_mm):
        p = self.sk.modelToSketchSpace(
            self.ctx.pt(wx_mm / 10.0, wy_mm / 10.0, wz_mm / 10.0))
        return self.ctx.pt(p.x, p.y, 0.0)

    def polyline(self, world_pts_mm):
        """Closed chain of lines; returns the list of start sketch points."""
        sp = [self.local(x, y, z) for x, y, z in world_pts_mm]
        lines = self.sk.sketchCurves.sketchLines
        first = lines.addByTwoPoints(sp[0], sp[1])
        prev = first
        made = [first]
        for i in range(2, len(sp)):
            adsk.doEvents()
            prev = lines.addByTwoPoints(prev.endSketchPoint, sp[i])
            made.append(prev)
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
        return [ln.startSketchPoint for ln in made]

    def pin(self, point, **world_exprs):
        """Pin a sketch point: one entry per in-plane world axis, either an
        expression (distance from the origin, unsigned) or None (on axis)."""
        sk, ctx = self.sk, self.ctx
        gc = sk.geometricConstraints
        g = point.geometry
        anchor = ctx.pt(g.x + 0.35, g.y + 0.25, 0.0)
        for name, expr in world_exprs.items():
            orient = self.axis[name]
            if expr is None:
                if orient == "h":
                    gc.addVerticalPoints(sk.originPoint, point)
                else:
                    gc.addHorizontalPoints(sk.originPoint, point)
                continue
            if orient == "h":
                o = ctx.dims_or.HorizontalDimensionOrientation
            else:
                o = ctx.dims_or.VerticalDimensionOrientation
            d = sk.sketchDimensions.addDistanceDimension(
                sk.originPoint, point, o, anchor)
            d.parameter.expression = expr


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    cbs = ctx.cbs
    cpats = root.features.circularPatternFeatures
    chamfers = root.features.chamferFeatures
    popts = adsk.fusion.PatternComputeOptions
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    if root.bRepBodies.itemByName("hex_ring_1") is not None:
        raise RuntimeError("hex_ring_1 already exists: run in a fresh document")

    for nm, expr, unit, desc in PARAMS:
        adsk.doEvents()
        if up.itemByName(nm) is not None:
            raise RuntimeError("parameter %s already exists" % nm)
        up.add(nm, cbs(expr), unit, desc)

    # numeric mirrors (mm) for seeds and predicates only
    v = {nm: ctx.val(nm) * 10.0 for nm, _e, unit, _d in PARAMS if unit == "mm"}
    v["dt_ang"] = ctx.val("dt_ang")  # radians
    pitch, hex_r, hex_ri = v["pitch"], v["hex_r"], v["hex_ri"]
    print("FH params: pitch %.2f clear %.2f rack_h %.2f key_len %.2f"
          % (pitch, v["slot_clear"], v["rack_h"], v["key_len"]))
    if v["rack_h"] > v["rack_w"]:
        raise RuntimeError("rack_h %.1f exceeds envelope %.1f"
                           % (v["rack_h"], v["rack_w"]))
    if v["slot_clear"] < 92.0:
        raise RuntimeError("slot_clear %.1f < 92 mm" % v["slot_clear"])

    def finish_sketch(sk, label):
        adsk.doEvents()
        print("FH sketch %s fully constrained: %s" % (label, sk.isFullyConstrained))

    def hex_loop(m, half_flat, circ, half_circ, hf, rr):
        """Pointy-top hexagon centred on the origin: p0 top vertex, then
        clockwise. hf / rr are the mm seeds; the expressions drive."""
        pts = m.polyline([
            (0.0, rr, 0.0), (hf, rr / 2.0, 0.0), (hf, -rr / 2.0, 0.0),
            (0.0, -rr, 0.0), (-hf, -rr / 2.0, 0.0), (-hf, rr / 2.0, 0.0)])
        m.pin(pts[0], x=None, y=circ)
        m.pin(pts[3], x=None, y=circ)
        for k in (1, 2, 4, 5):
            adsk.doEvents()
            m.pin(pts[k], x=half_flat, y=half_circ)

    # ---- ring --------------------------------------------------------
    sk_ring = root.sketches.add(root.xYConstructionPlane)
    sk_ring.name = "hex_ring_profile"
    m = SkMap(ctx, sk_ring)
    hex_loop(m, "pitch / 2", "hex_r", "hex_r / 2", pitch / 2.0, hex_r)
    hex_loop(m, "slot_clear / 2", "hex_ri", "hex_ri / 2",
             v["slot_clear"] / 2.0, hex_ri)
    finish_sketch(sk_ring, "ring")

    ring_area = (SQ3 / 2.0) * (pitch ** 2 - v["slot_clear"] ** 2) / 100.0  # cm2
    ring_prof = adsk.core.ObjectCollection.create()
    for pr in sk_ring.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
        a = pr.areaProperties().area
        if abs(a - ring_area) < 0.05 * ring_area:
            ring_prof.add(pr)
    if ring_prof.count != 1:
        raise RuntimeError("ring profile pick found %d" % ring_prof.count)

    ring_vol = ring_area * v["ring_d"] / 10.0

    def ring_ok(b):
        bb = b.boundingBox
        return (abs(b.volume - ring_vol) < 0.02 * ring_vol
                and abs(bb.minPoint.z) < 1e-4 and bb.maxPoint.z > 0)

    f_ring, ring = ctx.checked_newbody(ring_prof, "ring_d", ring_ok, "ring")
    f_ring.name = "hex_ring_extrude"
    ring.name = "hex_ring_1"
    print("FH ring %.3f cm3" % ring.volume)

    top_plane = ctx.plane_at_z("ring_d", "hex_mouth_plane")

    def groove_profile(m, flat_x, cy, fx_mm, cy_mm):
        """Dovetail groove at a vertical flat (x = flat_x), centred on
        y = cy, opening outward (+x). Neck sits grv_over outside the flat
        so the cut always opens the surface."""
        neck_x = "%s + grv_over" % flat_x
        base_x = "%s - grv_d" % flat_x
        wo = "grv_neck / 2 - grv_over * tan(dt_ang)"
        wi = "grv_base / 2"
        wo_mm = v["grv_neck"] / 2.0 - v["grv_over"] * math.tan(v["dt_ang"])
        wi_mm = v["grv_base"] / 2.0
        xo, xi = fx_mm + v["grv_over"], fx_mm - v["grv_d"]
        pts = m.polyline([(xo, cy_mm + wo_mm, 0.0), (xi, cy_mm + wi_mm, 0.0),
                          (xi, cy_mm - wi_mm, 0.0), (xo, cy_mm - wo_mm, 0.0)])
        if cy is None:
            ys = (wo, wi, wi, wo)
        else:
            ys = ("%s + %s" % (cy, wo), "%s + %s" % (cy, wi),
                  "abs(%s - (%s))" % (cy, wi), "abs(%s - (%s))" % (cy, wo))
        xs = (neck_x, base_x, base_x, neck_x)
        for k in range(4):
            adsk.doEvents()
            m.pin(pts[k], x=xs[k], y=ys[k])

    groove_vol = ((v["grv_neck"] + v["grv_base"]) / 2.0 * v["grv_d"]
                  * v["grv_cut"]) / 1000.0  # cm3, approximate

    sk_grv = root.sketches.add(top_plane)
    sk_grv.name = "hex_ring_groove"
    groove_profile(SkMap(ctx, sk_grv), "pitch / 2", None, pitch / 2.0, 0.0)
    finish_sketch(sk_grv, "ring groove")
    f_grv = ctx.blind_cut(ctx.all_profiles(sk_grv), "grv_cut", [ring],
                          "groove", min_vol_cm3=0.4 * groove_vol)
    f_grv.name = "hex_ring_groove_cut"

    v0 = ring.volume
    coll = adsk.core.ObjectCollection.create()
    coll.add(f_grv)
    pin = cpats.createInput(coll, root.zConstructionAxis)
    pin.quantity = cbs("6")
    pin.totalAngle = cbs("360 deg")
    pin.isSymmetric = False
    pin.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
    pf = cpats.add(pin)
    if pf.healthState not in healthy or v0 - ring.volume < 5 * 0.4 * groove_vol:
        raise RuntimeError("groove pattern dv=%.4f" % (v0 - ring.volume))
    pf.name = "hex_ring_groove_pattern"
    print("FH ring with 6 grooves %.3f cm3" % ring.volume)

    def show_face_edges(body, split_r_cm=None):
        """Edges lying in the z = 0 plane (the show face, on the bed),
        selected by geometry. With split_r_cm, returns (inner, outer)
        by the edge midpoint's distance from the z axis."""
        inner = adsk.core.ObjectCollection.create()
        outer = adsk.core.ObjectCollection.create()
        for e in body.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            s, t = e.startVertex.geometry, e.endVertex.geometry
            if abs(s.z) > 1e-4 or abs(t.z) > 1e-4:
                continue
            r = math.hypot((s.x + t.x) / 2.0, (s.y + t.y) / 2.0)
            if split_r_cm is not None and r < split_r_cm:
                inner.add(e)
            else:
                outer.add(e)
        return inner, outer

    def chamfer(edges, dist_expr, body, name):
        vb = body.volume
        ci = chamfers.createInput2()
        ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            edges, cbs(dist_expr), True)
        f = chamfers.add(ci)
        if f.healthState not in healthy or body.volume >= vb:
            raise RuntimeError("%s chamfer removed nothing" % name)
        f.name = name
        return f

    inner_e, outer_e = show_face_edges(ring, (hex_r + hex_ri) / 20.0)
    if inner_e.count != 6 or outer_e.count != 6:
        raise RuntimeError("ring show-face edges %d/%d" % (inner_e.count,
                                                           outer_e.count))
    chamfer(outer_e, "ch_reveal", ring, "hex_ring_reveal")
    chamfer(inner_e, "ch_flare", ring, "hex_ring_flare")

    def n_new(expected):
        def ok(f):
            return f.healthState in healthy and f.bodies.count == expected
        return ok

    ring_x = ctx.pattern_bodies([ring], ctx.x_axis, "2", "pitch + lay_gap",
                                n_new(1))
    ring_y = ctx.pattern_bodies([ring] + ring_x, ctx.y_axis, "2",
                                "hex_v + lay_gap", n_new(2))
    for i, b in enumerate(ring_x + ring_y):
        adsk.doEvents()
        b.name = "hex_ring_%d" % (i + 2)

    # ---- key: bow-tie, lying flat, length along +x ----------------------
    kin = ctx.planes.createInput()
    kin.setByOffset(root.yZConstructionPlane, cbs("lay_key_x"))
    key_plane = ctx.planes.add(kin)
    key_plane.name = "hex_key_plane"

    def key_profile(m, cy, cy_mm, kx):
        b2, n2, d = v["dt_base"] / 2.0, v["dt_neck"] / 2.0, v["dt_d"]
        pts = m.polyline([
            (kx, cy_mm + b2, 0.0), (kx, cy_mm + n2, d), (kx, cy_mm + b2, 2 * d),
            (kx, cy_mm - b2, 2 * d), (kx, cy_mm - n2, d), (kx, cy_mm - b2, 0.0)])
        if cy is None:
            ys = ("dt_base / 2", "dt_neck / 2", "dt_base / 2",
                  "dt_base / 2", "dt_neck / 2", "dt_base / 2")
        else:
            ys = ("%s + dt_base / 2" % cy, "%s + dt_neck / 2" % cy,
                  "%s + dt_base / 2" % cy, "abs(%s - dt_base / 2)" % cy,
                  "abs(%s - dt_neck / 2)" % cy, "abs(%s - dt_base / 2)" % cy)
        zs = (None, "dt_d", "2 * dt_d", "2 * dt_d", "dt_d", None)
        for k in range(6):
            adsk.doEvents()
            m.pin(pts[k], y=ys[k], z=zs[k])

    key_area = (v["dt_base"] + v["dt_neck"]) * v["dt_d"] / 100.0  # cm2

    def key_ok(length_mm):
        vol = key_area * length_mm / 10.0

        def ok(b):
            bb = b.boundingBox
            return (abs(b.volume - vol) < 0.02 * vol
                    and abs(bb.minPoint.z) < 1e-4)
        return ok

    sk_key = root.sketches.add(key_plane)
    sk_key.name = "hex_key_profile"
    key_profile(SkMap(ctx, sk_key), None, 0.0, v["lay_key_x"])
    finish_sketch(sk_key, "key")
    f_key, key = ctx.checked_newbody(ctx.all_profiles(sk_key), "key_len",
                                     key_ok(v["key_len"]), "key")
    f_key.name = "hex_key_extrude"
    key.name = "hex_key_1"
    print("FH key %.3f cm3" % key.volume)
    keys = ctx.pattern_bodies([key], ctx.y_axis, "10", "dt_base + lay_gap",
                              n_new(9))
    for i, b in enumerate(keys):
        adsk.doEvents()
        b.name = "hex_key_%d" % (i + 2)

    # ---- base rail: flat bottom, zig-zag top under the bottom row -----
    sk_rail = root.sketches.add(root.xYConstructionPlane)
    sk_rail.name = "hex_rail_profile"
    m = SkMap(ctx, sk_rail)
    ry = -v["lay_rail_y"]
    bt, nh, rw = v["base_t"], v["notch_h"], v["rail_w"]
    rail_pts = m.polyline([
        (-rw / 2.0, ry, 0.0), (rw / 2.0, ry, 0.0),
        (rw / 2.0, ry + bt + nh, 0.0), (pitch, ry + bt, 0.0),
        (pitch / 2.0, ry + bt + nh, 0.0), (0.0, ry + bt, 0.0),
        (-pitch / 2.0, ry + bt + nh, 0.0), (-pitch, ry + bt, 0.0),
        (-rw / 2.0, ry + bt + nh, 0.0)])
    y_bot, y_vtx, y_notch = ("lay_rail_y", "lay_rail_y - base_t",
                             "lay_rail_y - base_t - notch_h")
    rail_dims = (("rail_w / 2", y_bot), ("rail_w / 2", y_bot),
                 ("rail_w / 2", y_notch), ("pitch", y_vtx),
                 ("pitch / 2", y_notch), (None, y_vtx),
                 ("pitch / 2", y_notch), ("pitch", y_vtx),
                 ("rail_w / 2", y_notch))
    for k in range(9):
        adsk.doEvents()
        m.pin(rail_pts[k], x=rail_dims[k][0], y=rail_dims[k][1])
    finish_sketch(sk_rail, "rail")
    rail_area = (rw * bt + 6 * 0.5 * (pitch / 2.0) * nh) / 100.0  # cm2
    rail_vol = rail_area * v["ring_d"] / 10.0

    def rail_ok(b):
        bb = b.boundingBox
        return (abs(b.volume - rail_vol) < 0.02 * rail_vol
                and abs(bb.minPoint.z) < 1e-4)

    f_rail, rail = ctx.checked_newbody(ctx.all_profiles(sk_rail), "ring_d",
                                       rail_ok, "rail")
    f_rail.name = "hex_rail_extrude"
    rail.name = "hex_rail_1"
    print("FH rail %.3f cm3" % rail.volume)

    def rail_groove(m, side):
        """Groove under the lower-left (side=-1) / lower-right (side=+1)
        flat of the bottom ring at x = -pitch, expressed in the rail's
        sketch. Depth axis n points into the rail, t runs along the flat."""
        nx, ny = side * math.cos(math.radians(30)), -math.sin(math.radians(30))
        tx, ty = side * math.sin(math.radians(30)), math.cos(math.radians(30))
        cx_mm = -pitch + side * pitch / 4.0
        cy_mm = ry + bt + nh / 2.0
        wo_mm = v["grv_neck"] / 2.0 - v["grv_over"] * math.tan(v["dt_ang"])
        wi_mm = v["grv_base"] / 2.0
        ov, gd = v["grv_over"], v["grv_d"]
        seeds = [(cx_mm - ov * nx + wo_mm * tx, cy_mm - ov * ny + wo_mm * ty, 0.0),
                 (cx_mm + gd * nx + wi_mm * tx, cy_mm + gd * ny + wi_mm * ty, 0.0),
                 (cx_mm + gd * nx - wi_mm * tx, cy_mm + gd * ny - wi_mm * ty, 0.0),
                 (cx_mm - ov * nx - wo_mm * tx, cy_mm - ov * ny - wo_mm * ty, 0.0)]
        pts = m.polyline(seeds)
        s = "+" if side > 0 else "-"
        cx = "(-pitch %s pitch / 4)" % s
        cy = "(-lay_rail_y + base_t + notch_h / 2)"
        n = ("(%s cos(30 deg))" % ("" if side > 0 else "-"), "(-sin(30 deg))")
        t = ("(%s sin(30 deg))" % ("" if side > 0 else "-"), "(cos(30 deg))")
        wo = "(grv_neck / 2 - grv_over * tan(dt_ang))"
        wi = "(grv_base / 2)"
        rows = (("-grv_over", wo), ("grv_d", wi),
                ("grv_d", "-" + wi), ("-grv_over", "-" + wo))
        for k in range(4):
            adsk.doEvents()
            a, b = rows[k]
            ex = "abs(%s + (%s) * %s + (%s) * %s)" % (cx, a, n[0], b, t[0])
            ey = "abs(%s + (%s) * %s + (%s) * %s)" % (cy, a, n[1], b, t[1])
            m.pin(pts[k], x=ex, y=ey)

    sk_rg = root.sketches.add(top_plane)
    sk_rg.name = "hex_rail_groove"
    mrg = SkMap(ctx, sk_rg)
    rail_groove(mrg, -1)
    rail_groove(mrg, 1)
    finish_sketch(sk_rg, "rail grooves")
    f_rg = ctx.blind_cut(ctx.all_profiles(sk_rg), "grv_cut", [rail],
                         "rail_groove", min_vol_cm3=0.8 * groove_vol)
    f_rg.name = "hex_rail_groove_cut"
    pf_r = ctx.pattern_cut([f_rg], ctx.x_axis, "3", "pitch", [rail],
                           min_vol_cm3=4 * 0.4 * groove_vol)
    pf_r.name = "hex_rail_groove_pattern"
    print("FH rail with 6 grooves %.3f cm3" % rail.volume)

    _unused, rail_e = show_face_edges(rail)
    if rail_e.count != 9:
        raise RuntimeError("rail show-face edges %d" % rail_e.count)
    chamfer(rail_e, "ch_reveal", rail, "hex_rail_reveal")
    rails = ctx.pattern_bodies([rail], ctx.y_axis, "2", "rail_h + lay_gap",
                               n_new(1))
    for b in rails:
        adsk.doEvents()
        b.name = "hex_rail_2"

    # ---- tolerance coupon: one groove block + one short key -----------
    sk_cp = root.sketches.add(root.xYConstructionPlane)
    sk_cp.name = "hex_coupon_profile"
    cy_cp = v["lay_cp_y"]
    ctx.bound_rect2(sk_cp, (0.0, cy_cp / 10.0, 0.0),
                    v["cp_w"] / 20.0, v["cp_h"] / 20.0,
                    u_size="cp_w", v_size="cp_h",
                    u_pos=("0 mm", "cp_w / 2"), v_pos=("lay_cp_y", "cp_h / 2"))
    finish_sketch(sk_cp, "coupon")
    cp_vol = v["cp_w"] * v["cp_h"] * v["ring_d"] / 1000.0

    def cp_ok(b):
        return abs(b.volume - cp_vol) < 0.02 * cp_vol and abs(b.boundingBox.minPoint.z) < 1e-4

    f_cp, cp = ctx.checked_newbody(ctx.all_profiles(sk_cp), "ring_d", cp_ok,
                                   "coupon")
    f_cp.name = "hex_coupon_extrude"
    cp.name = "hex_coupon_block"
    sk_cg = root.sketches.add(top_plane)
    sk_cg.name = "hex_coupon_groove"
    groove_profile(SkMap(ctx, sk_cg), "cp_w / 2", "lay_cp_y",
                   v["cp_w"] / 2.0, cy_cp)
    finish_sketch(sk_cg, "coupon groove")
    f_cg = ctx.blind_cut(ctx.all_profiles(sk_cg), "grv_cut", [cp],
                         "coupon_groove", min_vol_cm3=0.4 * groove_vol)
    f_cg.name = "hex_coupon_groove_cut"

    ckin = ctx.planes.createInput()
    ckin.setByOffset(root.yZConstructionPlane, cbs("cp_w / 2 + lay_gap"))
    ck_plane = ctx.planes.add(ckin)
    ck_plane.name = "hex_coupon_key_plane"
    sk_ck = root.sketches.add(ck_plane)
    sk_ck.name = "hex_coupon_key_profile"
    key_profile(SkMap(ctx, sk_ck), "lay_cp_y", cy_cp,
                v["cp_w"] / 2.0 + v["lay_gap"])
    finish_sketch(sk_ck, "coupon key")
    f_ck, ck = ctx.checked_newbody(ctx.all_profiles(sk_ck), "cp_key_len",
                                   key_ok(v["cp_key_len"]), "coupon_key")
    f_ck.name = "hex_coupon_key_extrude"
    ck.name = "hex_coupon_key"

    n_total = root.bRepBodies.count
    if n_total != 18:
        raise RuntimeError("expected 18 bodies, found %d" % n_total)
    print("FH BUILD OK: %d bodies, pitch %.1f, clear %.1f, rack %.1f x %.1f x %.1f"
          % (n_total, pitch, v["slot_clear"], v["rack_w"], v["rack_h"],
             v["rack_d"]))
