"""BLOOM rev 2 - a decorative 3 x 3 wine rack for a 335 x 335 mm cube.

Rev 2 change: THREE flat rings per cell on four pass-through RODS, in
place of rev 1's two rings on integral posts. Rev 1's front ring sat
under the neck of a 320 mm bottle, so only the rear ring touched the
body; the new middle ring puts both load contacts on the body either
side of the centre of gravity (rear 0-16, middle 156-172 from the
bottle base) and bottles lie level. Rods are separate 10 mm square bars
printed lying flat: no towers on the plate.

Every cell: rear ring (blind pockets on its front face), middle ring
(square through holes), front ring (blind pockets on its back face,
locating pins on its front face), four rods through all three, dovetail
grooves on every ring face so keys tie neighbouring cells at all three
planes (36 keys). The wood-PLA BEZEL TILE pins onto the front ring and
carries the flared entry, the two-colour leaf relief and an optional
COB-LED rebate; it never carries load.

Modules modelled (bodies laid out on the XY plane in PRINT orientation):

  ring_f      110.8 x 110.8 x 16 (+5 mm pins), face up    print 9
  ring_m      110.8 x 110.8 x 16, flat                     print 9
  ring_r      110.8 x 110.8 x 16, pockets up               print 9
  rod         10 x 10 x 264, lying flat, tick at mid_z     print 36
  tile        110.5 x 110.5 x 8, face up                   print 9
  tile_leaf_* eight half-leaves + tile_collar, colour 2   with each tile
  key         bowtie 6 x 7.8 x 15.5, standing              print 36 (+4)
  coupon      56 x 24 x 20: groove, pin hole, pocket, through hole
  rod_stub    10 x 10 x 20 rod end with the same chamfers
  key_tight / key_loose   keys at dt_clr -0.1 / +0.1

Overhang discipline: entry flare asserted <= 45 deg, relief extruded
straight up, pins up, pockets and holes blind or through from a bed
face, pocket-mouth and rod-end chamfers at 45 deg. The one bridge is
the 10.2 mm pocket roof inside the front ring. No supports anywhere.
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
INTERFERENCE_ALLOWED = []

# (name, default, unit, comment)
PARAMS = (
    ("space_w", "335 mm", "mm", "cube opening, square"),
    ("fit_gap", "1.25 mm", "mm", "clearance per side to the opening"),
    ("rack_d", "280 mm", "mm", "total rack depth incl. tile"),
    ("bezel_t", "8 mm", "mm", "tile thickness"),
    ("slot_clear", "92 mm", "mm", "clear bore through rings and tile"),
    ("flare_r", "4 mm", "mm", "entry flare, radial growth at the face"),
    ("flare_h", "6 mm", "mm", "entry flare, axial depth (>= flare_r)"),
    ("ring_d", "16 mm", "mm", "ring thickness (all three rings)"),
    ("mid_z", "140 mm", "mm", "rear ring inner face to middle ring rear face"),
    ("rod_w", "10 mm", "mm", "rod section (square)"),
    ("rod_gap", "0.1 mm", "mm", "rod to pocket / hole clearance per side"),
    ("rod_in", "3 mm", "mm", "rod inset from the ring outer faces"),
    ("rod_ch", "1 mm", "mm", "rod end chamfer, 45 deg"),
    ("pocket_d", "12 mm", "mm", "blind pocket depth in the end rings"),
    ("pocket_ch", "0.5 mm", "mm", "pocket mouth chamfer, 45 deg"),
    ("tick_w", "0.8 mm", "mm", "rod tick groove width"),
    ("tick_d", "0.4 mm", "mm", "rod tick groove depth"),
    ("dt_mouth", "7 mm", "mm", "dovetail groove mouth width at the face"),
    ("dt_base", "8.3 mm", "mm", "dovetail groove base width"),
    ("dt_depth", "3 mm", "mm", "dovetail groove depth"),
    ("dt_ovr", "1 mm", "mm", "cut overshoot outside a face"),
    ("dt_clr", "0.25 mm", "mm", "key clearance per side (sliding fit)"),
    ("key_short", "0.5 mm", "mm", "key is ring_d minus this"),
    ("pin_d", "6 mm", "mm", "tile locating pin diameter"),
    ("pin_h", "5 mm", "mm", "pin height above the ring front face"),
    ("pin_inset", "13 mm", "mm", "pin centre from each outer face"),
    ("fit_push", "0.1 mm", "mm", "pin push-fit clearance per side"),
    ("hole_comp", "0.4 mm", "mm", "round-hole print undersize allowance"),
    ("tile_gap", "0.3 mm", "mm", "seam between adjacent tiles"),
    ("relief_h", "1.2 mm", "mm", "leaf / collar relief height"),
    ("relief_in", "0.6 mm", "mm", "leaf straight side inset from the seam"),
    ("leaf_s0", "3 mm", "mm", "leaf start along the edge from the corner"),
    ("leaf_len", "38 mm", "mm", "leaf length along the edge"),
    ("leaf_w", "7 mm", "mm", "leaf max half-width (inward from the seam)"),
    ("collar_w", "2 mm", "mm", "collar ring radial width"),
    ("collar_gap", "0.5 mm", "mm", "collar inner radius beyond the flare lip"),
    ("led_w", "11 mm", "mm", "LED channel width (10 mm COB strip)"),
    ("led_d", "3.2 mm", "mm", "LED channel depth into the tile back"),
    ("coupon_w", "56 mm", "mm", "tolerance coupon block width"),
    ("coupon_h", "24 mm", "mm", "tolerance coupon block height"),
    ("coupon_z", "20 mm", "mm", "tolerance coupon block thickness"),
    ("stub_len", "20 mm", "mm", "rod stub length for the coupon"),
    ("layout_gap", "40 mm", "mm", "gap between modules in the document"),
    ("lay_ky", "45 mm", "mm", "key row offset in the document"),
    ("lay_kx", "20 mm", "mm", "key spacing in the document"),
    # derived
    ("cell_w", "( space_w - 2 * fit_gap ) / 3", "mm", "cell pitch"),
    ("cell_d", "rack_d - bezel_t", "mm", "cell depth, rear face to front face"),
    ("pocket_floor", "ring_d - pocket_d", "mm", "material under a pocket"),
    ("rod_len", "cell_d - 2 * pocket_floor", "mm", "rod length"),
    ("hole_w", "rod_w + 2 * rod_gap", "mm", "pocket and through-hole side"),
    ("post_c", "cell_w / 2 - rod_w / 2 - rod_in", "mm", "rod centre offset"),
    ("tick_z", "ring_d + mid_z - pocket_floor", "mm", "tick from the rod rear end"),
    ("tile_w", "cell_w - tile_gap", "mm", "tile side"),
    ("hole_d", "pin_d + 2 * fit_push + hole_comp", "mm", "tile pin hole"),
    ("key_len", "ring_d - key_short", "mm", "key length"),
    ("tile_cx", "cell_w + layout_gap", "mm", "tile centre x in document"),
    ("ring_r_cy", "cell_w + layout_gap", "mm", "rear ring centre y"),
    ("ring_m_cy", "2 * ( cell_w + layout_gap )", "mm", "middle ring centre y"),
    ("rod_cy", "-( cell_w / 2 + layout_gap )", "mm", "rod centre y (flat)"),
    ("lay_x3", "2 * cell_w + 2 * layout_gap", "mm", "coupon centre x"),
)

# liveness scoped to this script's own parameters (names, not a flag)
FH_OPTS = {"only_params": [p[0] for p in PARAMS], "liveness_budget_s": 90}


def _ax_map(sk, pt, w, U, V):
    """Which sketch axis carries world direction U and V (R6: derived at
    runtime from modelToSketchSpace, never assumed)."""
    c = sk.modelToSketchSpace(pt(w[0], w[1], w[2]))
    pu = sk.modelToSketchSpace(pt(w[0] + U[0], w[1] + U[1], w[2] + U[2]))
    pv = sk.modelToSketchSpace(pt(w[0] + V[0], w[1] + V[1], w[2] + V[2]))
    u_is_x = abs(pu.x - c.x) >= abs(pu.y - c.y)
    v_is_x = abs(pv.x - c.x) >= abs(pv.y - c.y)
    if u_is_x == v_is_x:
        raise RuntimeError("sketch plane does not span U and V")
    return u_is_x


def bound_poly(ctx, sk, U, V, pts):
    """Closed chained polygon, every vertex pinned by one U-distance and
    one V-distance dimension (unsigned, abs-wrapped, from the sketch
    origin or from another vertex of the same polygon).

    pts: list of (world_seed_cm, u_expr, v_expr, u_ref, v_ref) where
    u_ref / v_ref are None (origin) or the index of the reference
    vertex. 2 dims per vertex = 2 DOF per vertex: fully constrained
    without any geometric constraint, so nothing can over-constrain."""
    pt = ctx.pt
    dims_or = ctx.dims_or
    u_is_x = _ax_map(sk, pt, pts[0][0], U, V)
    sp = [sk.modelToSketchSpace(pt(p[0][0], p[0][1], p[0][2])) for p in pts]
    ln = sk.sketchCurves.sketchLines
    first = ln.addByTwoPoints(sp[0], sp[1])
    verts = [first.startSketchPoint, first.endSketchPoint]
    prev = first
    for i in range(2, len(sp)):
        adsk.doEvents()
        prev = ln.addByTwoPoints(prev.endSketchPoint, sp[i])
        verts.append(prev.endSketchPoint)
    ln.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    u_or = (dims_or.HorizontalDimensionOrientation if u_is_x
            else dims_or.VerticalDimensionOrientation)
    v_or = (dims_or.VerticalDimensionOrientation if u_is_x
            else dims_or.HorizontalDimensionOrientation)
    for i, (_, u_expr, v_expr, u_ref, v_ref) in enumerate(pts):
        adsk.doEvents()
        anchor = pt(sp[i].x + 0.25, sp[i].y + 0.25, 0)
        u_from = sk.originPoint if u_ref is None else verts[u_ref]
        d = sk.sketchDimensions.addDistanceDimension(
            u_from, verts[i], u_or, anchor)
        d.parameter.expression = "abs( %s )" % u_expr
        v_from = sk.originPoint if v_ref is None else verts[v_ref]
        d = sk.sketchDimensions.addDistanceDimension(
            v_from, verts[i], v_or, anchor)
        d.parameter.expression = "abs( %s )" % v_expr
    return verts


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs
    XY = root.xYConstructionPlane
    XZ = root.xZConstructionPlane
    YZ = root.yZConstructionPlane
    UX, UY, UZ = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)

    for name, expr, unit, comment in PARAMS:
        adsk.doEvents()
        if up.itemByName(name) is None:
            up.add(name, cbs(expr), unit, comment)

    v = ctx.val  # cm

    # ---- printability / geometry assertions ----------------------------
    flare = math.degrees(math.atan2(v("flare_r"), v("flare_h")))
    if flare > 45.0:
        raise RuntimeError("entry flare %.1f deg > 45: raise flare_h"
                           % flare)
    if v("dt_base") <= v("dt_mouth"):
        raise RuntimeError("dt_base must exceed dt_mouth (dovetail)")
    wall = v("cell_w") / 2 - v("slot_clear") / 2
    if wall - v("dt_depth") < 0.4:
        raise RuntimeError("mid-side wall %.1f mm leaves < 4 mm behind "
                           "the groove" % (wall * 10))
    hole_in = v("post_c") - v("hole_w") / 2        # pocket inner corner
    if math.hypot(hole_in, hole_in) <= v("slot_clear") / 2 + 0.3:
        raise RuntimeError("rod pockets reach the bore: raise rod_in")
    if v("post_c") + v("hole_w") / 2 >= v("cell_w") / 2 - 0.15:
        raise RuntimeError("rod pockets break the outer face: raise rod_in")
    if v("pocket_floor") < 0.3:
        raise RuntimeError("pocket floor %.1f mm < 3 mm" % (v("pocket_floor") * 10))
    if v("ring_d") + v("mid_z") + v("ring_d") >= v("cell_d") - v("ring_d"):
        raise RuntimeError("middle ring collides with the front ring")
    pin_c = v("cell_w") / 2 - v("pin_inset")
    tile_hole_in = math.hypot(pin_c, pin_c) - v("hole_d") / 2
    if tile_hole_in < v("slot_clear") / 2 + v("flare_r") + 0.2:
        raise RuntimeError("tile pin hole breaks into the flare")
    print("FH bloom2 flare %.1f deg wall %.1f mm pitch %.2f mm rod %.0f mm "
          "mid ring at %.0f-%.0f from the rear face"
          % (flare, wall * 10, v("cell_w") * 10, v("rod_len") * 10,
             (v("ring_d") + v("mid_z")) * 10,
             (2 * v("ring_d") + v("mid_z")) * 10))

    def find_body(name):
        return root.bRepBodies.itemByName(name)

    def plane_z(expr, name):
        pl = root.constructionPlanes.itemByName(name)
        if pl is None:
            pl = ctx.plane_at_z(expr, name)
        return pl

    def sketch_on(plane, name):
        sk = root.sketches.add(plane)
        sk.name = name
        return sk

    # layout centres are themselves parameters so dims stay live
    cx_names = {0.0: "0 mm"}
    cy_names = {0.0: "0 mm"}

    def groove_profile(sk, cx, cy, half_expr, half, sign, along_x):
        """Dovetail groove profile on the XY plane for the face at
        centre +- half along the groove axis (x if along_x else y):
        base inside the wall, mouth overshot outside the face."""
        hb = v("dt_base") / 2
        depth = v("dt_depth")
        ovr = v("dt_ovr")
        hm_expr = ("( dt_mouth - dt_ovr * ( dt_base - dt_mouth ) "
                   "/ dt_depth ) / 2")
        hm = (v("dt_mouth") - ovr * (v("dt_base") - v("dt_mouth"))
              / depth) / 2
        sgn = "+" if sign > 0 else "-"
        ce = cx_names[cx] if along_x else cy_names[cy]
        c = cx if along_x else cy
        oe = cy_names[cy] if along_x else cx_names[cx]
        o = cy if along_x else cx
        ab = c + sign * (half - depth)
        am = c + sign * (half + ovr)
        ab_e = "%s %s ( %s - dt_depth )" % (ce, sgn, half_expr)
        am_e = "%s %s ( %s + dt_ovr )" % (ce, sgn, half_expr)
        quad = [
            (ab, o + hb, ab_e, "%s + dt_base / 2" % oe),
            (ab, o - hb, ab_e, "%s - dt_base / 2" % oe),
            (am, o - hm, am_e, "%s - %s" % (oe, hm_expr)),
            (am, o + hm, am_e, "%s + %s" % (oe, hm_expr)),
        ]
        pts = []
        for a, b, ae, be in quad:
            if along_x:
                pts.append(((a, b, 0.0), ae, be, None, None))
            else:
                pts.append(((b, a, 0.0), be, ae, None, None))
        bound_poly(ctx, sk, UX, UY, pts)

    def four_grooves(body, cx, cy, name, depth_expr, depth):
        skg = sketch_on(XY, name)
        half = v("cell_w") / 2
        for sign, along_x in ((1, True), (-1, True), (1, False), (-1, False)):
            adsk.doEvents()
            groove_profile(skg, cx, cy, "cell_w / 2", half, sign, along_x)
        if skg.profiles.count != 4:
            raise RuntimeError("%s profiles %d" % (name, skg.profiles.count))
        gv = (v("dt_mouth") + v("dt_base")) / 2 * v("dt_depth") * depth * 4
        fg = ctx.blind_cut(ctx.all_profiles(skg), depth_expr, [body], name,
                           min_vol_cm3=0.7 * gv)
        fg.name = name + "_cut"

    def square_ring(name, cx, cy, cx_e, cy_e):
        sk = sketch_on(XY, name + "_outline")
        ctx.bound_rect2(sk, (cx, cy, 0), v("cell_w") / 2, v("cell_w") / 2,
                        u_size="cell_w", v_size="cell_w",
                        u_pos=(cx_e, "cell_w / 2"), v_pos=(cy_e, "cell_w / 2"))
        exp_vol = v("cell_w") ** 2 * v("ring_d")

        def ok(b):
            return abs(b.volume - exp_vol) < 0.02 * exp_vol

        f, body = ctx.checked_newbody(ctx.all_profiles(sk), "ring_d", ok,
                                      name + "_block")
        f.name = name + "_block"
        body.name = name
        skb = sketch_on(XY, name + "_bore")
        ctx.bound_circle(skb, (cx, cy, 0), v("slot_clear") / 2, "slot_clear",
                         x_pos=cx_e, v_pos=cy_e)
        bore_vol = math.pi * (v("slot_clear") / 2) ** 2 * v("ring_d")
        fb = ctx.blind_cut(ctx.all_profiles(skb), "ring_d", [body],
                           name + "_bore", min_vol_cm3=0.8 * bore_vol)
        fb.name = name + "_bore_cut"
        four_grooves(body, cx, cy, name + "_grooves", "ring_d", v("ring_d"))
        return body

    def corner_squares(sk, cx, cy, cx_e, cy_e, z, off_e, off, half_e, half):
        """Four squares at (cx +- off, cy +- off) on a plane at z."""
        for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            adsk.doEvents()
            ux = "%s %s %s" % (cx_e, "+" if sx > 0 else "-", off_e)
            uy = "%s %s %s" % (cy_e, "+" if sy > 0 else "-", off_e)
            ctx.bound_rect2(sk, (cx + sx * off, cy + sy * off, z), half, half,
                            u_size="2 * ( %s )" % half_e,
                            v_size="2 * ( %s )" % half_e,
                            u_pos=(ux, half_e), v_pos=(uy, half_e))

    def chamfer_edges(body, pick, name, dist_expr, dv_min, expect):
        """Equal-distance chamfer on every edge the predicate picks
        (geometric predicate, R4). Validates the edge count and volume."""
        coll = adsk.core.ObjectCollection.create()
        n = 0
        for e in body.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            if pick(e):
                coll.add(e)
                n += 1
        if n != expect:
            raise RuntimeError("%s picked %d edges, expected %d"
                               % (name, n, expect))
        v0 = body.volume
        ci = root.features.chamferFeatures.createInput2()
        ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            coll, cbs(dist_expr), False)
        cf = root.features.chamferFeatures.add(ci)
        cf.name = name
        if v0 - body.volume < dv_min:
            raise RuntimeError("%s removed %.4f cm3" % (name, v0 - body.volume))

    def edges_at_z_len(z_at, edge_len):
        def pick(e):
            s = e.startVertex.geometry
            t = e.endVertex.geometry
            return (abs(s.z - z_at) < 0.002 and abs(t.z - z_at) < 0.002
                    and abs(e.length - edge_len) < 0.01)
        return pick

    def rod_pockets(body, cx, cy, cx_e, cy_e, z_face, z_face_e, name,
                    depth_expr, depth, chamfer):
        """Four square pockets (blind, depth) or holes (depth = ring_d)
        from the face at z_face; optional 45 deg mouth chamfer."""
        skp = sketch_on(plane_z(z_face_e, name + "_plane") if z_face_e
                        else XY, name)
        corner_squares(skp, cx, cy, cx_e, cy_e, z_face, "post_c",
                       v("post_c"), "hole_w / 2", v("hole_w") / 2)
        if skp.profiles.count != 4:
            raise RuntimeError("%s profiles %d" % (name, skp.profiles.count))
        pv = 4 * v("hole_w") ** 2 * depth
        fp = ctx.blind_cut(ctx.all_profiles(skp), depth_expr, [body], name,
                           min_vol_cm3=0.9 * pv)
        fp.name = name + "_cut"
        if chamfer:
            # 16 mouth edges: straight, at the face, hole_w long
            dv = 16 * 0.5 * v("pocket_ch") ** 2 * v("hole_w") * 0.8
            chamfer_edges(body, edges_at_z_len(z_face, v("hole_w")),
                          name + "_chamfer", "pocket_ch", dv, 16)

    # ================================================================
    # FRONT RING - at the origin, face (pins) up, pockets on the bed side
    # ================================================================
    ring_f = find_body("ring_f")
    if ring_f is None:
        ring_f = square_ring("ring_f", 0.0, 0.0, "0 mm", "0 mm")
        rod_pockets(ring_f, 0.0, 0.0, "0 mm", "0 mm", 0.0, None,
                    "ring_f_pockets", "pocket_d", v("pocket_d"), True)
        front = plane_z("ring_d", "ring_f_face_plane")
        skp = sketch_on(front, "ring_f_pins")
        a = v("cell_w") / 2 - v("pin_inset")
        for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            adsk.doEvents()
            ctx.bound_circle(skp, (sx * a, sy * a, v("ring_d")),
                             v("pin_d") / 2, "pin_d",
                             x_pos="cell_w / 2 - pin_inset",
                             v_pos="cell_w / 2 - pin_inset")
        pin_vol = 4 * math.pi * (v("pin_d") / 2) ** 2 * v("pin_h")
        vb = ring_f.volume

        def pins_ok(b):
            return b.volume - vb > 0.8 * pin_vol

        fp = ctx.checked_join(ctx.all_profiles(skp), "pin_h", ring_f,
                              pins_ok, "ring_f_pins")
        fp.name = "ring_f_pins_join"
        bb = ring_f.boundingBox
        if bb.maxPoint.z < v("ring_d") + v("pin_h") - 0.01:
            raise RuntimeError("pins did not land on the front face")
        print("FH ring_f %.1f cm3, %.1f x %.1f x %.1f mm"
              % (ring_f.volume, (bb.maxPoint.x - bb.minPoint.x) * 10,
                 (bb.maxPoint.y - bb.minPoint.y) * 10,
                 (bb.maxPoint.z - bb.minPoint.z) * 10))
    else:
        print("FH skip ring_f (exists)")

    # ================================================================
    # REAR RING - at (0, ring_r_cy), pockets open on its top (front) face
    # ================================================================
    rcy = v("ring_r_cy")
    cy_names[rcy] = "ring_r_cy"
    ring_r = find_body("ring_r")
    if ring_r is None:
        ring_r = square_ring("ring_r", 0.0, rcy, "0 mm", "ring_r_cy")
        rod_pockets(ring_r, 0.0, rcy, "0 mm", "ring_r_cy", v("ring_d"),
                    "ring_d", "ring_r_pockets", "pocket_d", v("pocket_d"),
                    True)
        bb = ring_r.boundingBox
        if abs(bb.maxPoint.z - v("ring_d")) > 0.001:
            raise RuntimeError("rear ring top at %.3f" % bb.maxPoint.z)
        print("FH ring_r %.1f cm3" % ring_r.volume)
    else:
        print("FH skip ring_r (exists)")

    # ================================================================
    # MIDDLE RING - at (0, ring_m_cy), four square through holes
    # ================================================================
    mcy = v("ring_m_cy")
    cy_names[mcy] = "ring_m_cy"
    ring_m = find_body("ring_m")
    if ring_m is None:
        ring_m = square_ring("ring_m", 0.0, mcy, "0 mm", "ring_m_cy")
        rod_pockets(ring_m, 0.0, mcy, "0 mm", "ring_m_cy", 0.0, None,
                    "ring_m_holes", "ring_d", v("ring_d"), False)
        print("FH ring_m %.1f cm3" % ring_m.volume)
    else:
        print("FH skip ring_m (exists)")

    # ================================================================
    # ROD - lying flat along X at (tile_cx, rod_cy), chamfered ends,
    # tick groove around it at tick_z from its rear (-X) end
    # ================================================================
    rod_cy = v("rod_cy")
    cy_names[rod_cy] = "rod_cy"
    tcx = v("tile_cx")
    cx_names[tcx] = "tile_cx"

    def rod_body(name, cx, cx_e, len_e, length, tick):
        if find_body(name) is not None:
            print("FH skip %s (exists)" % name)
            return
        skr = sketch_on(XY, name + "_outline")
        ctx.bound_rect2(skr, (cx, rod_cy, 0), length / 2, v("rod_w") / 2,
                        u_size=len_e, v_size="rod_w",
                        u_pos=(cx_e, "%s / 2" % len_e),
                        v_pos=("rod_cy", "rod_w / 2"))
        exp_vol = v("rod_w") ** 2 * length

        def ok(b):
            return abs(b.volume - exp_vol) < 0.02 * exp_vol

        f, body = ctx.checked_newbody(ctx.all_profiles(skr), "rod_w", ok,
                                      name + "_block")
        f.name = name + "_block"
        body.name = name
        x0 = cx - length / 2
        x1 = cx + length / 2

        def end_edges(e):
            s = e.startVertex.geometry
            t = e.endVertex.geometry
            at_end = ((abs(s.x - x0) < 0.002 and abs(t.x - x0) < 0.002)
                      or (abs(s.x - x1) < 0.002 and abs(t.x - x1) < 0.002))
            return at_end and abs(e.length - v("rod_w")) < 0.01

        chamfer_edges(body, end_edges, name + "_chamfer", "rod_ch",
                      8 * 0.5 * v("rod_ch") ** 2 * v("rod_w") * 0.8, 8)
        if tick:
            # tick station measured from the -X (rear) end
            xt = x0 + v("tick_z")
            xt_e = "%s - %s / 2 + tick_z" % (cx_e, len_e)
            hw = v("rod_w") / 2
            tw = v("tick_w") / 2
            td = v("tick_d")
            ovr = v("dt_ovr")
            # side faces: two strips, through-all in Z
            sks = sketch_on(XY, name + "_tick_sides")
            for sy in (1, -1):
                adsk.doEvents()
                ctx.bound_rect2(
                    sks, (xt, rod_cy + sy * (hw - td / 2 + ovr / 2), 0),
                    tw, (td + ovr) / 2,
                    u_size="tick_w", v_size="tick_d + dt_ovr",
                    u_pos=(xt_e, "tick_w / 2"),
                    v_pos=("rod_cy %s ( rod_w / 2 - tick_d / 2 + dt_ovr / 2 )"
                           % ("+" if sy > 0 else "-"),
                           "( tick_d + dt_ovr ) / 2"))
            if sks.profiles.count != 2:
                raise RuntimeError("tick side profiles %d" % sks.profiles.count)
            side_vol = 2 * v("tick_w") * td * v("rod_w")
            fs = ctx.sym_cut(ctx.all_profiles(sks), "rod_w + 2 * dt_ovr",
                             [body], min_vol_cm3=0.7 * side_vol)
            fs.name = name + "_tick_sides_cut"
            # top face: blind from the top plane; bottom face: from XY
            face_vol = v("tick_w") * td * v("rod_w")
            for pl, pname in ((plane_z("rod_w", "rod_top_plane"), "_tick_top"),
                              (XY, "_tick_bottom")):
                adsk.doEvents()
                skt = sketch_on(pl, name + pname)
                zc = v("rod_w") if pname == "_tick_top" else 0.0
                ctx.bound_rect2(skt, (xt, rod_cy, zc), tw, hw + ovr,
                                u_size="tick_w", v_size="rod_w + 2 * dt_ovr",
                                u_pos=(xt_e, "tick_w / 2"),
                                v_pos=("rod_cy", "( rod_w + 2 * dt_ovr ) / 2"))
                ftk = ctx.blind_cut(ctx.all_profiles(skt), "tick_d", [body],
                                    name + pname, min_vol_cm3=0.7 * face_vol)
                ftk.name = name + pname + "_cut"
        bb = body.boundingBox
        print("FH %s %.2f cm3, %.1f x %.1f x %.1f mm"
              % (name, body.volume, (bb.maxPoint.x - bb.minPoint.x) * 10,
                 (bb.maxPoint.y - bb.minPoint.y) * 10,
                 (bb.maxPoint.z - bb.minPoint.z) * 10))

    rod_body("rod", tcx, "tile_cx", "rod_len", v("rod_len"), True)

    # ================================================================
    # TILE - the decorative bezel, face up, centred at (tile_cx, 0)
    # ================================================================
    tile = find_body("tile")
    if tile is None:
        sk = sketch_on(XY, "tile_outline")
        ctx.bound_rect2(sk, (tcx, 0, 0), v("tile_w") / 2, v("tile_w") / 2,
                        u_size="tile_w", v_size="tile_w",
                        u_pos=("tile_cx", "tile_w / 2"),
                        v_pos=("0 mm", "tile_w / 2"))
        exp_vol = v("tile_w") ** 2 * v("bezel_t")

        def ok_tile(b):
            return abs(b.volume - exp_vol) < 0.02 * exp_vol

        f, tile = ctx.checked_newbody(ctx.all_profiles(sk), "bezel_t",
                                      ok_tile, "tile_block")
        f.name = "tile_block"
        tile.name = "tile"

        skb = sketch_on(XY, "tile_bore")
        ctx.bound_circle(skb, (tcx, 0, 0), v("slot_clear") / 2, "slot_clear",
                         x_pos="tile_cx", v_pos="0 mm")
        bore_vol = math.pi * (v("slot_clear") / 2) ** 2 * v("bezel_t")
        fb = ctx.blind_cut(ctx.all_profiles(skb), "bezel_t", [tile],
                           "tile_bore", min_vol_cm3=0.8 * bore_vol)
        fb.name = "tile_bore_cut"

        # entry flare: revolve-cut a triangle about the tile axis.
        # Axis = intersection of (YZ offset to tile_cx) and XZ (y = 0).
        axpl = root.constructionPlanes.itemByName("tile_axis_plane")
        if axpl is None:
            pin_ = root.constructionPlanes.createInput()
            pin_.setByOffset(YZ, cbs("tile_cx"))
            axpl = root.constructionPlanes.add(pin_)
            axpl.name = "tile_axis_plane"
        ain = root.constructionAxes.createInput()
        ain.setByTwoPlanes(axpl, XZ)
        tile_axis = root.constructionAxes.add(ain)
        tile_axis.name = "tile_axis"
        r0 = v("slot_clear") / 2
        zt = v("bezel_t")
        fh = v("flare_h")
        fr = v("flare_r")
        ovr = v("dt_ovr")
        r_top = r0 + fr * (fh + ovr) / fh
        skf = sketch_on(XZ, "tile_flare")
        pts = [
            ((tcx + r0, 0, zt - fh), "tile_cx + slot_clear / 2",
             "bezel_t - flare_h", None, None),
            ((tcx + r_top, 0, zt + ovr),
             "tile_cx + slot_clear / 2 + flare_r * ( flare_h + dt_ovr ) "
             "/ flare_h", "bezel_t + dt_ovr", None, None),
            ((tcx + r0, 0, zt + ovr), "tile_cx + slot_clear / 2",
             "bezel_t + dt_ovr", None, None),
        ]
        bound_poly(ctx, skf, UX, UZ, pts)
        if skf.profiles.count != 1:
            raise RuntimeError("flare profiles %d" % skf.profiles.count)
        R = r0 + fr
        flare_vol = (math.pi * fh / 3 * (R * R + R * r0 + r0 * r0)
                     - math.pi * fh * r0 * r0)
        v0 = tile.volume
        rin = root.features.revolveFeatures.createInput(
            skf.profiles.item(0), tile_axis, ctx.ops.CutFeatureOperation)
        rin.setAngleExtent(False, cbs("360 deg"))
        rin.participantBodies = [tile]
        rf = root.features.revolveFeatures.add(rin)
        rf.name = "tile_flare_cut"
        dv = v0 - tile.volume
        if abs(dv - flare_vol) > 0.25 * flare_vol:
            raise RuntimeError("flare removed %.3f cm3, expected %.3f"
                               % (dv, flare_vol))

        # blind pin holes from the bed side
        skh = sketch_on(XY, "tile_holes")
        a = v("tile_w") / 2 - v("pin_inset")
        for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            adsk.doEvents()
            ctx.bound_circle(skh, (tcx + sx * a, sy * a, 0),
                             v("hole_d") / 2, "hole_d",
                             x_pos="tile_cx %s ( tile_w / 2 - pin_inset )"
                             % ("+" if sx > 0 else "-"),
                             v_pos="tile_w / 2 - pin_inset")
        hole_vol = 4 * math.pi * (v("hole_d") / 2) ** 2 * (v("pin_h")
                                                           + v("key_short"))
        fh_ = ctx.blind_cut(ctx.all_profiles(skh), "pin_h + key_short",
                            [tile], "tile_holes", min_vol_cm3=0.7 * hole_vol)
        fh_.name = "tile_holes_cut"

        # LED rebates on the back: +-Y strips run the full width (the
        # strip crosses tile seams along a row), +-X strips stop short
        # so the four profiles stay disjoint and no interior is enclosed.
        skl = sketch_on(XY, "tile_led")
        hw = v("tile_w") / 2
        lw = v("led_w")
        half_strip = lw / 4 + ovr / 2          # (led_w/2 + ovr)/2
        strip_c = hw - lw / 4 + ovr / 2        # centre of the strip
        for sy in (1, -1):
            adsk.doEvents()
            ctx.bound_rect2(skl, (tcx, sy * strip_c, 0), hw + ovr,
                            half_strip,
                            u_size="tile_w + 2 * dt_ovr",
                            v_size="led_w / 2 + dt_ovr",
                            u_pos=("tile_cx", "( tile_w + 2 * dt_ovr ) / 2"),
                            v_pos=("%s( tile_w / 2 - led_w / 4 + dt_ovr / 2 )"
                                   % ("" if sy > 0 else "-"),
                                   "( led_w / 2 + dt_ovr ) / 2"))
        short_half = (v("tile_w") - lw - 2 * ovr) / 2
        for sx in (1, -1):
            adsk.doEvents()
            ctx.bound_rect2(skl, (tcx + sx * strip_c, 0, 0), half_strip,
                            short_half,
                            u_size="led_w / 2 + dt_ovr",
                            v_size="tile_w - led_w - 2 * dt_ovr",
                            u_pos=("tile_cx %s ( tile_w / 2 - led_w / 4 "
                                   "+ dt_ovr / 2 )" % ("+" if sx > 0 else "-"),
                                   "( led_w / 2 + dt_ovr ) / 2"),
                            v_pos=("0 mm",
                                   "( tile_w - led_w - 2 * dt_ovr ) / 2"))
        if skl.profiles.count != 4:
            raise RuntimeError("led profiles %d" % skl.profiles.count)
        led_vol = (2 * v("tile_w") * lw / 2 * v("led_d")
                   + 2 * (v("tile_w") - lw - 2 * ovr) * lw / 2 * v("led_d"))
        fl = ctx.blind_cut(ctx.all_profiles(skl), "led_d", [tile],
                           "tile_led", min_vol_cm3=0.7 * led_vol)
        fl.name = "tile_led_cut"
        bb = tile.boundingBox
        print("FH tile %.1f cm3, %.1f x %.1f x %.1f mm"
              % (tile.volume, (bb.maxPoint.x - bb.minPoint.x) * 10,
                 (bb.maxPoint.y - bb.minPoint.y) * 10,
                 (bb.maxPoint.z - bb.minPoint.z) * 10))
    else:
        print("FH skip tile (exists)")

    # ---- relief: eight half-leaves + collar, colour 2, on the face -----
    def newbody_up(profs, dist_expr, z_floor, predicate, kind):
        """New bodies extruded from a plane; accept only the direction
        where every body rises from z_floor (so relief sits ON the face,
        never inside the tile)."""
        for d in (ctx.dirs.PositiveExtentDirection,
                  ctx.dirs.NegativeExtentDirection):
            adsk.doEvents()
            inp = ctx.extrudes.createInput(profs,
                                           ctx.ops.NewBodyFeatureOperation)
            ext = adsk.fusion.DistanceExtentDefinition.create(cbs(dist_expr))
            inp.setOneSideExtent(ext, d)
            f = ctx.extrudes.add(inp)
            bodies = [f.bodies.item(i) for i in range(f.bodies.count)]
            if (bodies and all(b.boundingBox.minPoint.z > z_floor - 0.005
                               for b in bodies) and predicate(bodies)):
                return f, bodies
            f.deleteMe()
        raise RuntimeError("%s never satisfied predicate" % kind)

    if find_body("tile_leaf_1") is None:
        face = plane_z("bezel_t", "tile_face_plane")
        skr = sketch_on(face, "tile_leaves")
        zt = v("bezel_t")
        hw = v("tile_w") / 2
        ins = v("relief_in")
        s0 = v("leaf_s0")
        L = v("leaf_len")
        W = v("leaf_w")
        N = 8
        # one half-leaf per (corner, edge): the straight side lies
        # relief_in inside the seam; the curved side is a parabola.
        leaf_specs = []
        for cxs, cys in ((-1, 1), (1, 1), (1, -1), (-1, -1)):
            for along_x in (True, False):
                leaf_specs.append((cxs, cys, along_x))
        for cxs, cys, along_x in leaf_specs:
            adsk.doEvents()
            pts = []
            for i in range(N + 1):
                t = i / float(N)
                s = s0 + L * t
                h = W * 4 * t * (1 - t)
                s_expr = "leaf_s0 + leaf_len * %.4f" % t
                h_expr = "leaf_w * %.4f" % (4 * t * (1 - t))
                if along_x:
                    x = tcx + cxs * (hw - s)
                    y = cys * (hw - ins - h)
                    xe = "tile_cx %s ( tile_w / 2 - ( %s ) )" % (
                        "+" if cxs > 0 else "-", s_expr)
                    ye = "tile_w / 2 - relief_in - ( %s )" % h_expr
                else:
                    x = tcx + cxs * (hw - ins - h)
                    y = cys * (hw - s)
                    xe = "tile_cx %s ( tile_w / 2 - relief_in - ( %s ) )" % (
                        "+" if cxs > 0 else "-", h_expr)
                    ye = "tile_w / 2 - ( %s )" % s_expr
                pts.append(((x, y, zt), xe, ye, None, None))
            bound_poly(ctx, skr, UX, UY, pts)
        # collar ring around the flare lip
        rc0 = v("slot_clear") / 2 + v("flare_r") + v("collar_gap")
        rc1 = rc0 + v("collar_w")
        if rc1 >= hw - 0.05:
            raise RuntimeError("collar outer radius reaches the tile edge")
        ctx.bound_circle(skr, (tcx, 0, zt), rc0,
                         "slot_clear + 2 * flare_r + 2 * collar_gap",
                         x_pos="tile_cx", v_pos="0 mm")
        ctx.bound_circle(skr, (tcx, 0, zt), rc1,
                         "slot_clear + 2 * flare_r + 2 * collar_gap "
                         "+ 2 * collar_w", x_pos="tile_cx", v_pos="0 mm")
        leaf_area = W * L * 2.0 / 3.0            # cm2, parabola
        collar_area = math.pi * (rc1 * rc1 - rc0 * rc0)
        profs = adsk.core.ObjectCollection.create()
        n_leaf = 0
        n_collar = 0
        for prof in skr.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
            a = prof.areaProperties().area
            if abs(a - leaf_area) < 0.2 * leaf_area:
                profs.add(prof)
                n_leaf += 1
            elif abs(a - collar_area) < 0.1 * collar_area:
                profs.add(prof)
                n_collar += 1
        if n_leaf != len(leaf_specs) or n_collar != 1:
            raise RuntimeError("relief profiles: %d leaves, %d collar"
                               % (n_leaf, n_collar))
        min_leaf = 0.5 * leaf_area * v("relief_h")

        def relief_ok(bodies):
            return (len(bodies) == len(leaf_specs) + 1
                    and all(b.volume > min_leaf for b in bodies))

        fr_, bodies = newbody_up(profs, "relief_h", zt, relief_ok,
                                 "tile_relief")
        fr_.name = "tile_relief_extrude"
        k = 0
        for b in sorted(bodies, key=lambda bd: bd.volume):
            adsk.doEvents()
            if b.volume > 2 * leaf_area * v("relief_h"):
                b.name = "tile_collar"
            else:
                k += 1
                b.name = "tile_leaf_%d" % k
        print("FH relief: %d leaves + collar, %.2f cm3 total"
              % (k, sum(b.volume for b in bodies)))
    else:
        print("FH skip relief (exists)")

    # ================================================================
    # KEYS, COUPON and ROD STUB, around (lay_x3, 0)
    # ================================================================
    x3 = v("lay_x3")
    ky = v("lay_ky")
    kx = v("lay_kx")
    cx_names[x3] = "lay_x3"

    def key_body(name, cx, cx_expr, clr_expr, clr):
        if find_body(name) is not None:
            print("FH skip %s (exists)" % name)
            return
        skk = sketch_on(XY, name + "_profile")
        d = v("dt_depth")
        hb = v("dt_base") / 2 - clr
        hm = v("dt_mouth") / 2 - clr
        hb_e = "dt_base / 2 - ( %s )" % clr_expr
        hm_e = "dt_mouth / 2 - ( %s )" % clr_expr
        pts = [
            ((cx - d, ky + hb, 0), "%s - dt_depth" % cx_expr,
             "lay_ky + %s" % hb_e, None, None),
            ((cx - d, ky - hb, 0), "%s - dt_depth" % cx_expr,
             "lay_ky - ( %s )" % hb_e, None, None),
            ((cx, ky - hm, 0), cx_expr, "lay_ky - ( %s )" % hm_e,
             None, None),
            ((cx + d, ky - hb, 0), "%s + dt_depth" % cx_expr,
             "lay_ky - ( %s )" % hb_e, None, None),
            ((cx + d, ky + hb, 0), "%s + dt_depth" % cx_expr,
             "lay_ky + %s" % hb_e, None, None),
            ((cx, ky + hm, 0), cx_expr, "lay_ky + %s" % hm_e, None, None),
        ]
        bound_poly(ctx, skk, UX, UY, pts)
        if skk.profiles.count != 1:
            raise RuntimeError("%s profiles %d" % (name, skk.profiles.count))
        exp = 2 * (hb + hm) * d * v("key_len")

        def ok(b):
            return abs(b.volume - exp) < 0.05 * exp

        f, b = ctx.checked_newbody(ctx.all_profiles(skk), "key_len", ok,
                                   name)
        f.name = name + "_extrude"
        b.name = name
        print("FH %s %.3f cm3" % (name, b.volume))

    clr = v("dt_clr")
    key_body("key", x3, "lay_x3", "dt_clr", clr)
    key_body("key_tight", x3 - kx, "lay_x3 - lay_kx", "dt_clr - 0.1 mm",
             clr - 0.01)
    key_body("key_loose", x3 + kx, "lay_x3 + lay_kx", "dt_clr + 0.1 mm",
             clr + 0.01)

    coupon = find_body("coupon")
    if coupon is None:
        skc = sketch_on(XY, "coupon_outline")
        ctx.bound_rect2(skc, (x3, 0, 0), v("coupon_w") / 2, v("coupon_h") / 2,
                        u_size="coupon_w", v_size="coupon_h",
                        u_pos=("lay_x3", "coupon_w / 2"),
                        v_pos=("0 mm", "coupon_h / 2"))
        exp_vol = v("coupon_w") * v("coupon_h") * v("coupon_z")

        def ok_c(b):
            return abs(b.volume - exp_vol) < 0.02 * exp_vol

        f, coupon = ctx.checked_newbody(ctx.all_profiles(skc), "coupon_z",
                                        ok_c, "coupon_block")
        f.name = "coupon_block"
        coupon.name = "coupon"
        # the production groove on the coupon's +X face
        skg = sketch_on(XY, "coupon_groove")
        groove_profile(skg, x3, 0.0, "coupon_w / 2", v("coupon_w") / 2, 1,
                       True)
        if skg.profiles.count != 1:
            raise RuntimeError("coupon groove profiles %d"
                               % skg.profiles.count)
        gv = (v("dt_mouth") + v("dt_base")) / 2 * v("dt_depth") * v("coupon_z")
        fg = ctx.blind_cut(ctx.all_profiles(skg), "coupon_z", [coupon],
                           "coupon_groove", min_vol_cm3=0.6 * gv)
        fg.name = "coupon_groove_cut"
        # pin hole (blind), rod pocket (blind, chamfered) and rod through
        # hole, all from the bed side, spaced along x
        skh = sketch_on(XY, "coupon_hole")
        ctx.bound_circle(skh, (x3 - 1.8, 0, 0), v("hole_d") / 2, "hole_d",
                         x_pos="lay_x3 - 18 mm", v_pos="0 mm")
        hv = math.pi * (v("hole_d") / 2) ** 2 * (v("pin_h") + v("key_short"))
        fh2 = ctx.blind_cut(ctx.all_profiles(skh), "pin_h + key_short",
                            [coupon], "coupon_hole", min_vol_cm3=0.7 * hv)
        fh2.name = "coupon_hole_cut"
        skq = sketch_on(XY, "coupon_pocket")
        ctx.bound_rect2(skq, (x3 - 0.3, 0, 0), v("hole_w") / 2, v("hole_w") / 2,
                        u_size="hole_w", v_size="hole_w",
                        u_pos=("lay_x3 - 3 mm", "hole_w / 2"),
                        v_pos=("0 mm", "hole_w / 2"))
        qv = v("hole_w") ** 2 * v("pocket_d")
        fq = ctx.blind_cut(ctx.all_profiles(skq), "pocket_d", [coupon],
                           "coupon_pocket", min_vol_cm3=0.9 * qv)
        fq.name = "coupon_pocket_cut"
        chamfer_edges(coupon, edges_at_z_len(0.0, v("hole_w")),
                      "coupon_pocket_chamfer", "pocket_ch",
                      4 * 0.5 * v("pocket_ch") ** 2 * v("hole_w") * 0.8, 4)
        skt = sketch_on(XY, "coupon_through")
        ctx.bound_rect2(skt, (x3 + 1.3, 0, 0), v("hole_w") / 2, v("hole_w") / 2,
                        u_size="hole_w", v_size="hole_w",
                        u_pos=("lay_x3 + 13 mm", "hole_w / 2"),
                        v_pos=("0 mm", "hole_w / 2"))
        tv = v("hole_w") ** 2 * v("coupon_z")
        ft = ctx.blind_cut(ctx.all_profiles(skt), "coupon_z", [coupon],
                           "coupon_through", min_vol_cm3=0.9 * tv)
        ft.name = "coupon_through_cut"
        print("FH coupon %.2f cm3" % coupon.volume)
    else:
        print("FH skip coupon (exists)")

    rod_body("rod_stub", x3, "lay_x3", "stub_len", v("stub_len"), False)

    # ---- bed-fit report (H2D single nozzle 325 x 320 x 325) -----------
    for name, limit in (("ring_f", (32.5, 32.0, 32.5)),
                        ("ring_m", (32.5, 32.0, 32.5)),
                        ("ring_r", (32.5, 32.0, 32.5)),
                        ("rod", (32.5, 32.0, 32.5)),
                        ("tile", (30.0, 32.0, 32.5))):
        b = find_body(name)
        if b is None:
            raise RuntimeError("missing body %s" % name)
        bb = b.boundingBox
        size = (bb.maxPoint.x - bb.minPoint.x, bb.maxPoint.y - bb.minPoint.y,
                bb.maxPoint.z - bb.minPoint.z)
        if any(s > lim for s, lim in zip(size, limit)):
            raise RuntimeError("%s %.1f x %.1f x %.1f mm exceeds the bed"
                               % (name, size[0] * 10, size[1] * 10,
                                  size[2] * 10))
    print("FH BUILD OK: %d bodies" % root.bRepBodies.count)


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
