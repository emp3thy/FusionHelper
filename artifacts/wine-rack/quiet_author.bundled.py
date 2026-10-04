"""QUIET NINE - an unobtrusive 3 x 3 bottle insert for a 335 x 335 mm cube.

The rack is meant to vanish. It is a short (164 mm deep) cradle that sits
at the BACK of the cube, so from the front you see nine bottle shoulders
and necks and, 150 mm behind them in shadow, a thin matte lattice. There
is no frame, no fastener and no pattern.

Architecture (every piece printed flat, hoop in XY, no supports):

    9 x quiet_rear   rear half-cell: cradle ring + base stop + 4 hollow
                     square ribs whose bores ARE the peg sockets
    9 x quiet_front  front half-cell: flared ring + 4 solid ribs ending
                     in chamfered square pegs
   24 x quiet_key    bone key (two discs + neck) tying ring to ring
    1 x coupon       fit coupon: bone sockets and peg sockets at three
                     clearances, plus a loose peg

Load path: the bottle rests on the floor of the rear cradle ring and on
the floor of the front ring, both 12 mm deep hoops lying in the print XY
plane. Rings stack ring-on-ring row to row down to the cube floor; the
ribs carry nothing but spacing. The keys hold each ring plane as one
3 x 3 slab so the assembly cannot shear or tip inside the cube.

Numbers that bind (brief): pitch = (335 - 2 x 1.25) / 3 = 110.83 mm,
clear bore 94 mm (>= 92) with a 5 mm 45-degree flare, ring wall 8.4 mm
(<= 12). Front support ring centred 155 mm from the bottle base: ahead
of the full-bottle centre of gravity (130-145) and still under the
cylindrical body of Bordeaux, Burgundy and Champagne shapes. The rear
cradle bore sits 4 mm LOWER than the front bore, so a bottle whose
shoulder taper has started by the front ring still sits level or a hair
neck-up, never neck-down.

Joints (printer research): keys slide in along the print Z so their
flanks are smooth XY perimeters, 0.20 mm per side, blind at the visible
face. Pegs are 6.7 mm squares in 7.2 mm square bores (0.25 mm per side,
loose enough that 36 pegs engage at once) with 1 mm lead chamfers; the
bores are the hollow rib interiors, so there is no boss and no overhang.

Layout: the five unique modules sit side by side on the XY plane in
their print orientation, each with its rear/front face on z = 0.
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
FH_OPTS = {"liveness_budget_s": 90, "max_bodies": 20}
INTERFERENCE_ALLOWED = []

# ---- parameter table: (name, expression, unit, comment) ---------------
# Roots hold literals; everything else is an expression of a root.
PARAMS = [
    # opening and grid
    ("space_w", "335 mm", "mm", "cube opening, width and height"),
    ("fit_gap", "1.25 mm", "mm", "clearance per side to the opening"),
    ("n_cells", "3", "", "cells per row and per column"),
    ("rack_w", "space_w - 2 * fit_gap", "mm", "rack envelope"),
    ("pitch", "rack_w / n_cells", "mm", "cell pitch = cell outer size"),
    # bottle interface
    ("slot_clear", "94 mm", "mm", "clear bore of both rings"),
    ("flare", "5 mm", "mm", "45 deg entry chamfer on the front bore"),
    ("ring_wall", "(pitch - slot_clear) / 2", "mm", "ring wall, reference"),
    ("rear_drop", "4 mm", "mm", "rear bore sits this much lower"),
    ("stop_bore", "70 mm", "mm", "base stop bore, < any bottle base"),
    ("stop_t", "3 mm", "mm", "base stop plate thickness"),
    # depth
    ("ring_d", "12 mm", "mm", "ring depth along the bottle axis"),
    ("half_d", "82 mm", "mm", "half-cell depth, ring + ribs"),
    ("cell_d", "2 * half_d", "mm", "cell depth = rack depth"),
    # ribs and pegs
    ("sock_w", "7.2 mm", "mm", "square peg socket = rear rib bore"),
    ("rib_t", "2.4 mm", "mm", "rear rib wall, 4 x 0.6 mm"),
    ("rib_w", "sock_w + 2 * rib_t", "mm", "rear rib outer square"),
    ("frib_w", "10 mm", "mm", "front rib, solid square"),
    ("peg_gap", "0.25 mm", "mm", "peg clearance per side"),
    ("peg_w", "sock_w - 2 * peg_gap", "mm", "peg square"),
    ("peg_l", "10 mm", "mm", "peg length"),
    ("peg_ch", "1 mm", "mm", "peg tip chamfer"),
    ("sock_ch", "0.8 mm", "mm", "socket mouth chamfer"),
    # bone keys
    ("key_d", "8 mm", "mm", "key disc diameter"),
    ("key_neck", "5 mm", "mm", "key neck width"),
    ("key_in", "5.5 mm", "mm", "disc centre depth behind the face"),
    ("key_off", "30 mm", "mm", "socket offset from the side centre"),
    ("key_blind", "2 mm", "mm", "socket floor left at the visible face"),
    ("dt_gap", "0.2 mm", "mm", "key clearance per side, sliding fit"),
    ("key_slack", "0.3 mm", "mm", "key shorter than its socket"),
    ("key_len", "ring_d - key_blind - key_slack", "mm", "key height"),
    # finish
    ("edge_ch", "1.5 mm", "mm", "chamfer on outer vertical corners"),
    # coupon and layout
    ("gap_step", "0.1 mm", "mm", "coupon clearance step"),
    ("coup_w", "18 mm", "mm", "coupon strip width"),
    ("coup_t", "12 mm", "mm", "coupon strip thickness"),
    ("coup_pitch", "18 mm", "mm", "coupon socket spacing"),
    ("coup_l", "coup_pitch * 7", "mm", "coupon strip length"),
    ("cpeg_t", "3 mm", "mm", "coupon peg base plate"),
    ("lay_gap", "20 mm", "mm", "gap between modules in the layout"),
    ("cell_cy", "pitch / 2", "mm", "y of both cell centres"),
    ("cell_a_x", "pitch / 2", "mm", "x of the rear half-cell centre"),
    ("cell_b_x", "pitch * 1.5 + lay_gap", "mm", "x of the front half-cell"),
    ("key_x", "pitch * 2 + lay_gap * 2 + key_in + key_d / 2", "mm",
     "x of the key centre"),
    ("coup_x", "key_x + key_in + key_d / 2 + lay_gap + coup_l / 2", "mm",
     "x of the coupon strip centre"),
    ("cpeg_y", "cell_cy + coup_w / 2 + lay_gap + frib_w / 2", "mm",
     "y of the coupon peg centre"),
]


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    for name, expr, unit, comment in PARAMS:
        adsk.doEvents()
        if up.itemByName(name) is None:
            up.add(name, cbs(expr), unit, comment)

    v = ctx.val   # cm
    pitch, hp = v("pitch"), v("pitch") / 2
    ring_d, half_d, stop_t = v("ring_d"), v("half_d"), v("stop_t")
    bore_r, stop_r = v("slot_clear") / 2, v("stop_bore") / 2
    rib_w, frib_w, sock_w = v("rib_w"), v("frib_w"), v("sock_w")
    peg_w, peg_l = v("peg_w"), v("peg_l")
    key_r, key_in, key_off = v("key_d") / 2, v("key_in"), v("key_off")
    key_neck, dt_gap = v("key_neck"), v("dt_gap")
    cy, ax, bx = v("cell_cy"), v("cell_a_x"), v("cell_b_x")
    kx, cx = v("key_x"), v("coup_x")
    coup_w, coup_t, coup_l = v("coup_w"), v("coup_t"), v("coup_l")
    cpeg_y, cpeg_t = v("cpeg_y"), v("cpeg_t")
    print("FH pitch %.2f mm, ring wall %.2f mm, cell depth %.1f mm"
          % (pitch * 10, v("ring_wall") * 10, v("cell_d") * 10))
    if v("ring_wall") * 10 < 6.0:
        raise RuntimeError("ring wall under 6 mm: widen pitch or shrink bore")
    if (v("ring_wall") - v("rear_drop")) * 10 < 4.0:
        raise RuntimeError("rear ring bottom wall under 4 mm")
    if v("flare") > v("ring_wall") - 0.2:
        raise RuntimeError("flare eats the whole front land")

    # ---- small helpers ------------------------------------------------
    def near(a, b, tol=0.02):
        return abs(a - b) <= tol * abs(b) + 1e-4

    def pick_profile(sk, expected_cm2, what):
        chosen = None
        for pr in sk.profiles:
            if near(pr.areaProperties().area, expected_cm2):
                chosen = pr
        if chosen is None:
            raise RuntimeError("%s: no profile of area %.3f cm2"
                               % (what, expected_cm2))
        coll = adsk.core.ObjectCollection.create()
        coll.add(chosen)
        return coll

    def on_bed(expected_cm3):
        def ok(body):
            bb = body.boundingBox
            return (abs(bb.minPoint.z) < 1e-3
                    and near(body.volume, expected_cm3))
        return ok

    def grew_by(target, expected_cm3):
        v0 = target.volume

        def ok(body):
            return near(body.volume - v0, expected_cm3)
        return ok

    def corners(cx_, cy_, w):
        d = hp - w / 2
        return [(cx_ - d, cy_ - d), (cx_ + d, cy_ - d),
                (cx_ - d, cy_ + d), (cx_ + d, cy_ + d)]

    def square_set(sk, z, centres, size_expr, size_cm, x_exprs, y_exprs):
        for (x, y), xe, ye in zip(centres, x_exprs, y_exprs):
            adsk.doEvents()
            ctx.bound_rect2(sk, (x, y, z), size_cm / 2, size_cm / 2,
                            u_size=size_expr, v_size=size_expr,
                            u_pos=(xe, "(%s) / 2" % size_expr),
                            v_pos=(ye, "(%s) / 2" % size_expr))

    def corner_exprs(cx_expr, w_expr):
        d = "(pitch / 2 - %s / 2)" % w_expr
        xs = ["%s - %s" % (cx_expr, d), "%s + %s" % (cx_expr, d),
              "%s - %s" % (cx_expr, d), "%s + %s" % (cx_expr, d)]
        ys = ["cell_cy - %s" % d, "cell_cy - %s" % d,
              "cell_cy + %s" % d, "cell_cy + %s" % d]
        return xs, ys

    def edges_where(body, pred):
        coll = adsk.core.ObjectCollection.create()
        for e in body.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            if pred(e):
                coll.add(e)
        return coll

    def is_line(e):
        return e.geometry.curveType == adsk.core.Curve3DTypes.Line3DCurveType

    def is_circle(e):
        return (e.geometry.curveType
                == adsk.core.Curve3DTypes.Circle3DCurveType)

    def ends(e):
        return e.startVertex.geometry, e.endVertex.geometry

    def chamfer(body, edges, dist_expr, name, min_count):
        if edges.count < min_count:
            raise RuntimeError("%s: %d edges, expected >= %d"
                               % (name, edges.count, min_count))
        v0 = body.volume
        ci = root.features.chamferFeatures.createInput2()
        ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            edges, cbs(dist_expr), True)
        f = root.features.chamferFeatures.add(ci)
        if f.healthState not in healthy or body.volume >= v0:
            raise RuntimeError("%s: chamfer unhealthy or removed nothing"
                               % name)
        f.name = name
        return f

    def ring_sketch(name, plane, cx_, cx_expr, circ_cy, circ_cy_expr,
                    r_cm, dia_expr, z):
        sk = root.sketches.add(plane)
        sk.name = name
        ctx.bound_rect2(sk, (cx_, cy, z), hp, hp,
                        u_size="pitch", v_size="pitch",
                        u_pos=(cx_expr, "pitch / 2"),
                        v_pos=("cell_cy", "pitch / 2"))
        ctx.bound_circle(sk, (cx_, circ_cy, z), r_cm, dia_expr,
                         x_pos=cx_expr, v_pos=circ_cy_expr)
        return sk

    def bone_sockets(body, cx_, cx_expr, name):
        """Four translation-symmetric key sockets, open at the ring top,
        blind key_blind above the bed face. Right/left faces carry the
        socket at +key_off in y, top/bottom at +key_off in x, so every
        cell is identical and neighbours' sockets face each other."""
        sk = root.sketches.add(pl_ring)
        sk.name = name
        r = key_r + dt_gap
        dia = "key_d + 2 * dt_gap"
        neck = "key_neck + 2 * dt_gap"
        reach = "key_in + 1 mm"
        hr = (key_in + 0.1) / 2
        spots = [
            # (circle x, circle y, x expr, y expr, rect x, rect y, rect
            #  x expr, rect y expr, along x?)
            (cx_ + hp - key_in, cy + key_off,
             "%s + pitch / 2 - key_in" % cx_expr, "cell_cy + key_off",
             cx_ + hp - hr + 0.05, cy + key_off,
             "%s + pitch / 2 - (key_in + 1 mm) / 2 + 0.5 mm" % cx_expr,
             "cell_cy + key_off", True),
            (cx_ - hp + key_in, cy + key_off,
             "%s - pitch / 2 + key_in" % cx_expr, "cell_cy + key_off",
             cx_ - hp + hr - 0.05, cy + key_off,
             "%s - pitch / 2 + (key_in + 1 mm) / 2 - 0.5 mm" % cx_expr,
             "cell_cy + key_off", True),
            (cx_ + key_off, cy + hp - key_in,
             "%s + key_off" % cx_expr, "cell_cy + pitch / 2 - key_in",
             cx_ + key_off, cy + hp - hr + 0.05,
             "%s + key_off" % cx_expr,
             "cell_cy + pitch / 2 - (key_in + 1 mm) / 2 + 0.5 mm", False),
            (cx_ + key_off, cy - hp + key_in,
             "%s + key_off" % cx_expr, "cell_cy - pitch / 2 + key_in",
             cx_ + key_off, cy - hp + hr - 0.05,
             "%s + key_off" % cx_expr,
             "cell_cy - pitch / 2 + (key_in + 1 mm) / 2 - 0.5 mm", False),
        ]
        for (x, y, xe, ye, rx, ry, rxe, rye, along_x) in spots:
            adsk.doEvents()
            ctx.bound_circle(sk, (x, y, ring_d), r, dia, x_pos=xe, v_pos=ye)
            if along_x:
                ctx.bound_rect2(sk, (rx, ry, ring_d), hr, (key_neck / 2
                                                            + dt_gap),
                                u_size=reach, v_size=neck,
                                u_pos=(rxe, "(%s) / 2" % reach),
                                v_pos=(rye, "(%s) / 2" % neck))
            else:
                ctx.bound_rect2(sk, (rx, ry, ring_d), (key_neck / 2
                                                        + dt_gap), hr,
                                u_size=neck, v_size=reach,
                                u_pos=(rxe, "(%s) / 2" % neck),
                                v_pos=(rye, "(%s) / 2" % reach))
        # expected removal, cm3: 4 x (disc + neck - overlap) x depth
        hw = key_neck / 2 + dt_gap
        overlap = 2 * (hw / 2 * math.sqrt(r * r - hw * hw)
                       + r * r / 2 * math.asin(hw / r))
        area = math.pi * r * r + key_in * 2 * hw - overlap
        depth = ring_d - v("key_blind")
        f = ctx.blind_cut(ctx.all_profiles(sk), "ring_d - key_blind",
                          [body], name, min_vol_cm3=0.5 * 4 * area * depth)
        f.name = name + "_cut"
        return f

    def corner_chamfer(body, cx_, name):
        def pred(e):
            if not is_line(e):
                return False
            s, t = ends(e)
            if abs(s.x - t.x) > 1e-3 or abs(s.y - t.y) > 1e-3:
                return False
            return (abs(abs(s.x - cx_) - hp) < 1e-3
                    and abs(abs(s.y - cy) - hp) < 1e-3)
        return chamfer(body, edges_where(body, pred), "edge_ch", name, 4)

    # ================= quiet_rear: cradle ring + stop + hollow ribs ====
    pl_ring = ctx.plane_at_z("ring_d", "ring_top_plane")
    ring_area = pitch * pitch - math.pi * bore_r * bore_r
    stop_area = pitch * pitch - math.pi * stop_r * stop_r

    sk = ring_sketch("rear_stop", root.xYConstructionPlane, ax, "cell_a_x",
                     cy - v("rear_drop"), "cell_cy - rear_drop", stop_r,
                     "stop_bore", 0.0)
    f, rear = ctx.checked_newbody(
        pick_profile(sk, stop_area, "rear_stop"), "stop_t",
        on_bed(stop_area * stop_t), "rear_stop")
    f.name = "rear_stop_extrude"
    rear.name = "quiet_rear"

    pl = ctx.plane_at_z("stop_t", "rear_cradle_plane")
    sk = ring_sketch("rear_cradle", pl, ax, "cell_a_x",
                     cy - v("rear_drop"), "cell_cy - rear_drop", bore_r,
                     "slot_clear", stop_t)
    f = ctx.checked_join(pick_profile(sk, ring_area, "rear_cradle"),
                         "ring_d - stop_t", rear,
                         grew_by(rear, ring_area * (ring_d - stop_t)),
                         "rear_cradle")
    f.name = "rear_cradle_join"

    sk = root.sketches.add(pl_ring)
    sk.name = "rear_ribs"
    xs, ys = corner_exprs("cell_a_x", "rib_w")
    square_set(sk, ring_d, corners(ax, cy, rib_w), "rib_w", rib_w, xs, ys)
    f = ctx.checked_join(ctx.all_profiles(sk), "half_d - ring_d", rear,
                         grew_by(rear, 4 * rib_w * rib_w * (half_d - ring_d)),
                         "rear_ribs")
    f.name = "rear_ribs_join"

    pl_top = ctx.plane_at_z("half_d", "rib_top_plane")
    sk = root.sketches.add(pl_top)
    sk.name = "rear_sockets"
    xs, ys = corner_exprs("cell_a_x", "rib_w")
    square_set(sk, half_d, corners(ax, cy, rib_w), "sock_w", sock_w, xs, ys)
    f = ctx.blind_cut(ctx.all_profiles(sk), "half_d - ring_d", [rear],
                      "rear_sockets",
                      min_vol_cm3=0.9 * 4 * sock_w * sock_w * (half_d - ring_d))
    f.name = "rear_sockets_cut"

    def sock_mouth(e):
        if not is_line(e):
            return False
        s, t = ends(e)
        if abs(s.z - half_d) > 1e-3 or abs(t.z - half_d) > 1e-3:
            return False
        mx, my = (s.x + t.x) / 2, (s.y + t.y) / 2
        for (qx, qy) in corners(ax, cy, rib_w):
            if max(abs(mx - qx), abs(my - qy)) <= sock_w / 2 + 0.01:
                return True
        return False
    chamfer(rear, edges_where(rear, sock_mouth), "sock_ch",
            "rear_socket_chamfer", 16)
    bone_sockets(rear, ax, "cell_a_x", "rear_keys")
    corner_chamfer(rear, ax, "rear_corner_chamfer")
    print("FH quiet_rear %.2f cm3" % rear.volume)

    # ================= quiet_front: flared ring + solid ribs + pegs ====
    sk = ring_sketch("front_ring", root.xYConstructionPlane, bx, "cell_b_x",
                     cy, "cell_cy", bore_r, "slot_clear", 0.0)
    f, front = ctx.checked_newbody(
        pick_profile(sk, ring_area, "front_ring"), "ring_d",
        on_bed(ring_area * ring_d), "front_ring")
    f.name = "front_ring_extrude"
    front.name = "quiet_front"

    def bore_bed_edge(e):
        if not is_circle(e):
            return False
        c = adsk.core.Circle3D.cast(e.geometry)
        return abs(c.center.z) < 1e-3 and near(c.radius, bore_r)
    chamfer(front, edges_where(front, bore_bed_edge), "flare",
            "front_flare", 1)

    sk = root.sketches.add(pl_ring)
    sk.name = "front_ribs"
    xs, ys = corner_exprs("cell_b_x", "frib_w")
    square_set(sk, ring_d, corners(bx, cy, frib_w), "frib_w", frib_w, xs, ys)
    f = ctx.checked_join(ctx.all_profiles(sk), "half_d - ring_d", front,
                         grew_by(front, 4 * frib_w * frib_w * (half_d - ring_d)),
                         "front_ribs")
    f.name = "front_ribs_join"

    sk = root.sketches.add(pl_top)
    sk.name = "front_pegs"
    xs, ys = corner_exprs("cell_b_x", "frib_w")
    square_set(sk, half_d, corners(bx, cy, frib_w), "peg_w", peg_w, xs, ys)
    f = ctx.checked_join(ctx.all_profiles(sk), "peg_l", front,
                         grew_by(front, 4 * peg_w * peg_w * peg_l),
                         "front_pegs")
    f.name = "front_pegs_join"

    def peg_tip(e):
        if not is_line(e):
            return False
        s, t = ends(e)
        return (abs(s.z - half_d - peg_l) < 1e-3
                and abs(t.z - half_d - peg_l) < 1e-3)
    chamfer(front, edges_where(front, peg_tip), "peg_ch",
            "front_peg_chamfer", 16)
    bone_sockets(front, bx, "cell_b_x", "front_keys")
    corner_chamfer(front, bx, "front_corner_chamfer")
    print("FH quiet_front %.2f cm3" % front.volume)

    # ================= quiet_key: bone key ===============================
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.name = "key"
    ctx.bound_circle(sk, (kx - key_in, cy, 0.0), key_r, "key_d",
                     x_pos="key_x - key_in", v_pos="cell_cy")
    ctx.bound_circle(sk, (kx + key_in, cy, 0.0), key_r, "key_d",
                     x_pos="key_x + key_in", v_pos="cell_cy")
    ctx.bound_rect2(sk, (kx, cy, 0.0), key_in, key_neck / 2,
                    u_size="2 * key_in", v_size="key_neck",
                    u_pos=("key_x", "key_in"), v_pos=("cell_cy", "key_neck / 2"))
    hw = key_neck / 2
    overlap = 2 * (hw / 2 * math.sqrt(key_r * key_r - hw * hw)
                   + key_r * key_r / 2 * math.asin(hw / key_r))
    key_area = 2 * math.pi * key_r * key_r + 2 * key_in * key_neck - 2 * overlap
    f, key = ctx.checked_newbody(ctx.all_profiles(sk), "key_len",
                                 on_bed(key_area * v("key_len")), "key")
    if f.bodies.count != 1:
        raise RuntimeError("key extrude made %d bodies" % f.bodies.count)
    f.name = "key_extrude"
    key.name = "quiet_key"
    print("FH quiet_key %.3f cm3" % key.volume)

    # ================= coupon: strip with 3 + 3 sockets, loose peg ======
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.name = "coupon_strip"
    ctx.bound_rect2(sk, (cx, cy, 0.0), coup_l / 2, coup_w / 2,
                    u_size="coup_l", v_size="coup_w",
                    u_pos=("coup_x", "coup_l / 2"),
                    v_pos=("cell_cy", "coup_w / 2"))
    f, coupon = ctx.checked_newbody(ctx.all_profiles(sk), "coup_t",
                                    on_bed(coup_l * coup_w * coup_t),
                                    "coupon_strip")
    f.name = "coupon_strip_extrude"
    coupon.name = "quiet_coupon"

    pl_ct = ctx.plane_at_z("coup_t", "coupon_top_plane")
    sk = root.sketches.add(pl_ct)
    sk.name = "coupon_peg_sockets"
    cp = v("coup_pitch")
    for k, step in ((0, "-"), (1, "+ 0 *"), (2, "+")):
        adsk.doEvents()
        gap = "(peg_gap %s gap_step)" % step
        size = "peg_w + 2 * %s" % gap
        size_cm = peg_w + 2 * (v("peg_gap") + (k - 1) * v("gap_step"))
        xe = "coup_x - coup_l / 2 + coup_pitch * %d" % (k + 1)
        ctx.bound_rect2(sk, (cx - coup_l / 2 + cp * (k + 1), cy, coup_t),
                        size_cm / 2, size_cm / 2,
                        u_size=size, v_size=size,
                        u_pos=(xe, "(%s) / 2" % size),
                        v_pos=("cell_cy", "(%s) / 2" % size))
    f = ctx.blind_cut(ctx.all_profiles(sk), "peg_l + 1 mm", [coupon],
                      "coupon_peg_sockets",
                      min_vol_cm3=0.9 * 3 * sock_w * sock_w * (peg_l + 0.1))
    f.name = "coupon_peg_sockets_cut"

    sk = root.sketches.add(pl_ct)
    sk.name = "coupon_key_sockets"
    for k, step in ((0, "-"), (1, "+ 0 *"), (2, "+")):
        adsk.doEvents()
        gap = "(dt_gap %s gap_step)" % step
        g_cm = dt_gap + (k - 1) * v("gap_step")
        xe = "coup_x - coup_l / 2 + coup_pitch * %d" % (k + 4)
        x = cx - coup_l / 2 + cp * (k + 4)
        ctx.bound_circle(sk, (x, cy + coup_w / 2 - key_in, coup_t),
                         key_r + g_cm, "key_d + 2 * %s" % gap,
                         x_pos=xe, v_pos="cell_cy + coup_w / 2 - key_in")
        neck = "key_neck + 2 * %s" % gap
        ctx.bound_rect2(sk, (x, cy + coup_w / 2 - hr_of(key_in), coup_t),
                        key_neck / 2 + g_cm, (key_in + 0.1) / 2,
                        u_size=neck, v_size="key_in + 1 mm",
                        u_pos=(xe, "(%s) / 2" % neck),
                        v_pos=("cell_cy + coup_w / 2 - (key_in + 1 mm) / 2 "
                               "+ 0.5 mm", "(key_in + 1 mm) / 2"))
    f = ctx.blind_cut(ctx.all_profiles(sk), "coup_t - key_blind", [coupon],
                      "coupon_key_sockets", min_vol_cm3=0.5 * 3 * key_area
                      / 2 * (coup_t - v("key_blind")))
    f.name = "coupon_key_sockets_cut"
    print("FH quiet_coupon %.2f cm3" % coupon.volume)

    sk = root.sketches.add(root.xYConstructionPlane)
    sk.name = "coupon_peg_base"
    ctx.bound_rect2(sk, (cx, cpeg_y, 0.0), frib_w / 2, frib_w / 2,
                    u_size="frib_w", v_size="frib_w",
                    u_pos=("coup_x", "frib_w / 2"),
                    v_pos=("cpeg_y", "frib_w / 2"))
    f, cpeg = ctx.checked_newbody(ctx.all_profiles(sk), "cpeg_t",
                                  on_bed(frib_w * frib_w * cpeg_t),
                                  "coupon_peg_base")
    f.name = "coupon_peg_base_extrude"
    cpeg.name = "quiet_coupon_peg"
    pl = ctx.plane_at_z("cpeg_t", "coupon_peg_plane")
    sk = root.sketches.add(pl)
    sk.name = "coupon_peg"
    ctx.bound_rect2(sk, (cx, cpeg_y, cpeg_t), peg_w / 2, peg_w / 2,
                    u_size="peg_w", v_size="peg_w",
                    u_pos=("coup_x", "peg_w / 2"),
                    v_pos=("cpeg_y", "peg_w / 2"))
    f = ctx.checked_join(ctx.all_profiles(sk), "peg_l", cpeg,
                         grew_by(cpeg, peg_w * peg_w * peg_l), "coupon_peg")
    f.name = "coupon_peg_join"

    def cpeg_tip(e):
        if not is_line(e):
            return False
        s, t = ends(e)
        return (abs(s.z - cpeg_t - peg_l) < 1e-3
                and abs(t.z - cpeg_t - peg_l) < 1e-3)
    chamfer(cpeg, edges_where(cpeg, cpeg_tip), "peg_ch",
            "coupon_peg_chamfer", 4)

    # ---- bed check and summary ------------------------------------------
    for b in (rear, front, key, coupon, cpeg):
        bb = b.boundingBox
        dx = (bb.maxPoint.x - bb.minPoint.x) * 10
        dy = (bb.maxPoint.y - bb.minPoint.y) * 10
        dz = (bb.maxPoint.z - bb.minPoint.z) * 10
        if dx > 325 or dy > 320 or dz > 325:
            raise RuntimeError("%s exceeds the H2D bed" % b.name)
        print("FH %s %.1f x %.1f x %.1f mm  %.2f cm3"
              % (b.name, dx, dy, dz, b.volume))
    print("FH BUILD OK: %d bodies" % root.bRepBodies.count)


def hr_of(key_in_cm):
    """Neck-rect centre offset from the face: half of (key_in + 1 mm),
    minus the 0.5 mm overshoot that pokes the rect past the face."""
    return (key_in_cm + 0.1) / 2 - 0.05


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
