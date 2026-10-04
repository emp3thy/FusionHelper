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

# fh-bundle: kit begin v2 00ca86d51507
"""The build kit: one canonical copy of the helpers every Fusion build
script used to copy-paste (measured drift: back_splices.py carried a
stale face-count blind_cut while the volume fixes lived only in
build16.py).

Author scripts do `from fusionhelper.buildkit import *`; the bundler
(fusionhelper.bundle) replaces that line with this file's source so a
single self-contained artifact reaches Fusion. Offline (tests, pyright)
this module imports like any other; inside Fusion the same text runs
inlined.

Validation policy (api-notes S14/S15): volume-threshold is the DEFAULT
for cuts and cut patterns; face-count is opt-in for small isolated holes
only. Pattern seed cuts must cut exactly ONE body (multi-body seeds fail
replication with R-Pattern85/PATTERN_FEATURES_NO_PASTE and no causal
error text).
"""
import adsk.core
import adsk.fusion

KIT_VERSION = "2"

__all__ = ["KIT_VERSION", "BuildCtx"]


class BuildCtx:
    """Per-run Fusion handles + helper methods. Create once at the top
    of run(): ctx = BuildCtx(adsk.core.Application.get())"""

    def __init__(self, app):
        self.app = app
        self.des = adsk.fusion.Design.cast(app.activeProduct)
        self.root = self.des.rootComponent
        self.up = self.des.userParameters
        self.extrudes = self.root.features.extrudeFeatures
        self.patterns = self.root.features.rectangularPatternFeatures
        self.planes = self.root.constructionPlanes
        self.ops = adsk.fusion.FeatureOperations
        self.dims_or = adsk.fusion.DimensionOrientations
        self.dirs = adsk.fusion.ExtentDirections
        self.pt = adsk.core.Point3D.create
        self.cbs = adsk.core.ValueInput.createByString
        self.x_axis = self.root.xConstructionAxis
        self.y_axis = self.root.yConstructionAxis
        self.U = (1.0, 0.0, 0.0)
        self.V = (0.0, 1.0, 0.0)
        self._resolved = {}
        self._circle_jitter = 0

    def val(self, name):
        return self.up.itemByName(name).value  # cm

    def plane_at_z(self, off_expr, name):
        pin = self.planes.createInput()
        pin.setByOffset(self.root.xYConstructionPlane, self.cbs(off_expr))
        pl = self.planes.add(pin)
        pl.name = name
        return pl

    def all_profiles(self, sk):
        coll = adsk.core.ObjectCollection.create()
        for pr in sk.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
            coll.add(pr)
        return coll

    def bound_rect2(self, sk, w, hu, hv, u_size=None, v_size=None,
                    u_pos=None, v_pos=None):
        """Constrained rectangle. w = world centre; position expressions
        are (centre_expr, half_size_expr) pairs — base is the CENTRE
        coordinate expression (measured: corner-based baselines snapped
        the board to the wrong quadrant)."""
        pt, U, V = self.pt, self.U, self.V
        dims_or = self.dims_or
        c = sk.modelToSketchSpace(pt(w[0], w[1], w[2]))
        pu = sk.modelToSketchSpace(pt(w[0] + U[0], w[1] + U[1], w[2] + U[2]))
        pv = sk.modelToSketchSpace(pt(w[0] + V[0], w[1] + V[1], w[2] + V[2]))
        if abs(pu.x - c.x) >= abs(pu.y - c.y):
            shx, shy = hu, hv
            ax = (u_size, u_pos, 1 if pu.x > c.x else -1)
            ay = (v_size, v_pos, 1 if pv.y > c.y else -1)
        else:
            shx, shy = hv, hu
            ax = (v_size, v_pos, 1 if pv.x > c.x else -1)
            ay = (u_size, u_pos, 1 if pu.y > c.y else -1)
        lines = sk.sketchCurves.sketchLines.addTwoPointRectangle(
            pt(c.x - shx, c.y - shy, 0), pt(c.x + shx, c.y + shy, 0))
        gc = sk.geometricConstraints
        h_line = None
        v_line = None
        for k in range(lines.count):
            ln = lines.item(k)
            s, e = ln.startSketchPoint.geometry, ln.endSketchPoint.geometry
            if abs(e.x - s.x) >= abs(e.y - s.y):
                gc.addHorizontal(ln)
                if h_line is None:
                    h_line = ln
            else:
                gc.addVertical(ln)
                if v_line is None:
                    v_line = ln
        if h_line is None or v_line is None:
            raise RuntimeError("rect missing axis-aligned line")
        corner = lines.item(0).startSketchPoint
        anchor = pt(c.x + shx + 0.5, c.y - shy - 0.5, 0)
        d = sk.sketchDimensions.addDistanceDimension(
            h_line.startSketchPoint, h_line.endSketchPoint,
            dims_or.HorizontalDimensionOrientation, anchor)
        d.parameter.expression = ax[0] if ax[0] else "%.4f mm" % (shx * 20)
        d = sk.sketchDimensions.addDistanceDimension(
            v_line.startSketchPoint, v_line.endSketchPoint,
            dims_or.VerticalDimensionOrientation, anchor)
        d.parameter.expression = ay[0] if ay[0] else "%.4f mm" % (shy * 20)
        for orient, half_sz, (_, pos, sign), cval in (
                (dims_or.HorizontalDimensionOrientation, shx, ax, c.x),
                (dims_or.VerticalDimensionOrientation, shy, ay, c.y)):
            d = sk.sketchDimensions.addDistanceDimension(
                sk.originPoint, corner, orient, anchor)
            if pos is None:
                d.parameter.expression = "%.4f mm" % (abs(cval - half_sz) * 10)
            else:
                # abs() is load-bearing: a distance dimension is unsigned,
                # so a corner expression that evaluates NEGATIVE (any rect
                # centred on the sketch origin, e.g. '0 mm - (9.65 mm)')
                # is stored negative but SNAPPED POSITIVE by the solver,
                # sliding the whole rectangle sideways by its full width.
                # Measured 2026-08-02; abs() confirmed valid in a Fusion
                # expression and keeps the dimension parametric.
                d.parameter.expression = "abs( %s %s (%s) )" % (
                    pos[0], "-" if sign > 0 else "+", pos[1])

    def bound_circle(self, sk, w, r_cm, dia_expr, x_pos=None, v_pos=None):
        """Jittered creation: coincident-coordinate circles trigger silent
        alignment inference then over-constrain (measured). Dims snap it."""
        pt, U = self.pt, self.U
        dims_or = self.dims_or
        c = sk.modelToSketchSpace(pt(w[0], w[1], w[2]))
        pu = sk.modelToSketchSpace(pt(w[0] + U[0], w[1] + U[1], w[2] + U[2]))
        self._circle_jitter += 1
        j = self._circle_jitter
        circle = sk.sketchCurves.sketchCircles.addByCenterRadius(
            pt(c.x + 0.011 + 0.003 * j, c.y + 0.017 + 0.005 * j, 0), r_cm)
        anchor = pt(c.x + r_cm + 0.4, c.y - 0.4, 0)
        if abs(pu.x - c.x) >= abs(pu.y - c.y):
            h_pos, v_pos_ = x_pos, v_pos
        else:
            h_pos, v_pos_ = v_pos, x_pos
        d = sk.sketchDimensions.addDistanceDimension(
            sk.originPoint, circle.centerSketchPoint,
            dims_or.HorizontalDimensionOrientation, anchor)
        d.parameter.expression = (h_pos if h_pos
                                  else "%.4f mm" % (abs(c.x) * 10))
        d = sk.sketchDimensions.addDistanceDimension(
            sk.originPoint, circle.centerSketchPoint,
            dims_or.VerticalDimensionOrientation, anchor)
        d.parameter.expression = (v_pos_ if v_pos_
                                  else "%.4f mm" % (abs(c.y) * 10))
        d = sk.sketchDimensions.addDiameterDimension(circle, anchor)
        d.parameter.expression = dia_expr
        return circle

    # ---- cuts and joins (volume-threshold validation by default) --------

    def _one_side(self, inp, dist_expr, direction):
        ext = adsk.fusion.DistanceExtentDefinition.create(self.cbs(dist_expr))
        inp.setOneSideExtent(ext, direction)

    def _try_dirs(self, kind):
        if kind in self._resolved:
            return (self._resolved[kind], None)
        return (self.dirs.PositiveExtentDirection,
                self.dirs.NegativeExtentDirection)

    def faces_of(self, bodies):
        return sum(b.faces.count for b in bodies)

    def through_cut(self, profs, depth_expr, participants, *,
                    min_vol_cm3=0.02):
        """Symmetric through-cut. Volume-validated (S14/S15: face counts
        can stay flat or DROP on seam-spanning cuts)."""
        return self.sym_cut(profs, depth_expr, participants,
                            min_vol_cm3=min_vol_cm3)

    def sym_cut(self, profs, depth_expr, participants, *, min_vol_cm3=0.02):
        v0 = sum(b.volume for b in participants)
        inp = self.extrudes.createInput(profs, self.ops.CutFeatureOperation)
        inp.setSymmetricExtent(self.cbs(depth_expr), True)
        inp.participantBodies = participants
        f = self.extrudes.add(inp)
        if v0 - sum(b.volume for b in participants) <= min_vol_cm3:
            f.deleteMe()
            raise RuntimeError("symmetric cut removed no volume")
        return f

    def blind_cut(self, profs, dist_expr, participants, kind="cut", *,
                  min_vol_cm3=0.02):
        v0 = sum(b.volume for b in participants)
        for d in self._try_dirs(kind):
            adsk.doEvents()
            if d is None:
                break
            inp = self.extrudes.createInput(
                profs, self.ops.CutFeatureOperation)
            self._one_side(inp, dist_expr, d)
            inp.participantBodies = participants
            f = self.extrudes.add(inp)
            if v0 - sum(b.volume for b in participants) > min_vol_cm3:
                self._resolved[kind] = d
                return f
            f.deleteMe()
        raise RuntimeError("blind cut cut nothing (%s)" % kind)

    def checked_join(self, profs, dist_expr, target, predicate, kind):
        for d in self._try_dirs(kind):
            adsk.doEvents()
            if d is None:
                break
            inp = self.extrudes.createInput(
                profs, self.ops.JoinFeatureOperation)
            self._one_side(inp, dist_expr, d)
            inp.participantBodies = [target]
            f = self.extrudes.add(inp)
            if predicate(target):
                self._resolved[kind] = d
                return f
            f.deleteMe()
        raise RuntimeError("join never satisfied predicate (%s)" % kind)

    def checked_newbody(self, profs, dist_expr, predicate, kind):
        for d in self._try_dirs(kind):
            adsk.doEvents()
            if d is None:
                break
            inp = self.extrudes.createInput(
                profs, self.ops.NewBodyFeatureOperation)
            self._one_side(inp, dist_expr, d)
            f = self.extrudes.add(inp)
            body = f.bodies.item(0)
            if predicate(body):
                self._resolved[kind] = d
                return f, body
            f.deleteMe()
        raise RuntimeError("new body never satisfied predicate (%s)" % kind)

    # ---- patterns -------------------------------------------------------

    def _pattern(self, coll, ax, n, d, validate, adjust):
        """Direction/compute retry ladder. NOTE (S15, measured): a seed
        CUT that removes material from more than one body never
        replicates (R-Pattern85 / PATTERN_FEATURES_NO_PASTE, no causal
        error text) — reshape the seed to cut exactly one body."""
        healthy = (
            adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
            adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)
        reasons = []
        perp = self.y_axis if ax == self.x_axis else self.x_axis
        popts = adsk.fusion.PatternComputeOptions
        modes = ((popts.AdjustPatternCompute, popts.IdenticalPatternCompute)
                 if adjust else (None,))
        for dd in (d, "-(%s)" % d):
            adsk.doEvents()
            for mode in modes:
                adsk.doEvents()
                inp = self.patterns.createInput(
                    coll, ax, self.cbs(n), self.cbs(dd),
                    adsk.fusion.PatternDistanceType
                    .SpacingPatternDistanceType)
                inp.setDirectionTwo(perp, self.cbs("1"), self.cbs("0 mm"))
                if mode is not None:
                    inp.patternComputeOption = mode  # pyright: ignore[reportAttributeAccessIssue]
                try:
                    f = self.patterns.add(inp)
                except Exception as e:
                    reasons.append("%s/%s add-raise %s"
                                   % (dd, mode, str(e)[:50]))
                    continue
                if f.healthState in healthy and validate(f):
                    return f
                reasons.append("%s/%s hs=%s" % (dd, mode, f.healthState))
                f.deleteMe()
        raise RuntimeError("pattern never validated: " + " | ".join(reasons))

    def pattern_bodies(self, bodies, ax, n, d, predicate):
        """Body pattern (no compute-option: body patterns reject it).
        predicate(feature) -> bool accepts/rejects the whole pattern —
        e.g. a bounds check that every new body landed inside the part."""
        coll = adsk.core.ObjectCollection.create()
        for b in bodies:  # fusionhelper: allow R11 — collection add, not a document mutation
            coll.add(b)
        f = self._pattern(coll, ax, n, d, predicate, adjust=False)
        out = []
        for i in range(f.bodies.count):
            out.append(f.bodies.item(i))
        return out

    def pattern_cut(self, feats, ax, n, d, watch, *,
                    min_vol_cm3=None, min_new_faces=None):
        """Pattern of cut features. Volume threshold is the default
        choice (S14/S15); face-count is opt-in for small isolated holes.
        Exactly one of min_vol_cm3 / min_new_faces must be given."""
        if (min_vol_cm3 is None) == (min_new_faces is None):
            raise ValueError(
                "pass exactly one of min_vol_cm3 / min_new_faces")
        coll = adsk.core.ObjectCollection.create()
        for f in feats:  # fusionhelper: allow R11 — collection add, not a document mutation
            coll.add(f)
        if min_vol_cm3 is not None:
            v0 = sum(b.volume for b in watch)

            def validate(_f):
                return v0 - sum(b.volume for b in watch) >= min_vol_cm3
        else:
            before = self.faces_of(watch)

            def validate(_f):
                return self.faces_of(watch) - before >= min_new_faces  # pyright: ignore[reportOperatorIssue]
        return self._pattern(coll, ax, n, d, validate, adjust=True)
# fh-bundle: kit end

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


# fusionhelper: verification stub v1
def _fh_verify_entry():
    import os, json, traceback
    home = os.environ.get('FUSIONHELPER_HOME') or os.path.join(
        os.environ.get('LOCALAPPDATA', ''), 'FusionHelper')

    def _bail(code, msg):
        return 'FH_VERDICT1 ' + json.dumps(
            {'v': 1, 'status': 'error', 'code': code, 'msg': msg, 'home': home},
            separators=(',', ':'))

    try:
        with open(os.path.join(home, 'fh_verify.py'), encoding='utf-8') as f:
            src = f.read()
    except Exception as e:
        return _bail('verify.block_missing', str(e))
    ns: dict = {'__name__': 'fh_verify'}   # annotated: else pyright infers dict[str, str]
    try:
        exec(compile(src, 'fh_verify.py', 'exec'), ns)
        g = globals()
        return ns['fh_verify'](
            clearances=g.get('CLEARANCES'),
            face_specs=g.get('FACE_SPECS'),
            datum_heights_cm=g.get('DATUM_HEIGHTS_CM'),
            digest=g.get('DIGEST'),
            interference_allowed=g.get('INTERFERENCE_ALLOWED'),
            expect_dead=g.get('EXPECT_DEAD'),
            refs=g.get('FH_REFS', {}),
            attempt=g.get('FH_ATTEMPT', 1),
            **g.get('FH_OPTS', {}))
    except Exception:
        return _bail('verify.internal', traceback.format_exc()[-600:])


def _fh_wrap(inner):
    def _wrapped(_context: str):
        inner(_context)                 # NOT wrapped: build exceptions must escape
        print(_fh_verify_entry())
    return _wrapped


run = _fh_wrap(run)
