import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {"liveness_budget_s": 180}
INTERFERENCE_ALLOWED = []

MM = 0.1  # art constants are written in mm; the API is cm


# ---- pure-python art generators (all coordinates mm) -------------------

def arc_pts(cx, cy, r, a0_deg, a1_deg, n):
    out = []
    for i in range(n + 1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / n)
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def stroke(centre, w):
    """Closed polygon of constant width w around an open centreline."""
    n = len(centre)
    left, right = [], []
    for i in range(n):
        x0, y0 = centre[max(i - 1, 0)]
        x1, y1 = centre[min(i + 1, n - 1)]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln, dx / ln
        x, y = centre[i]
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    return left + right[::-1]


def smile(cx, cy, r, w, half_span_deg=55, n=12):
    return stroke(arc_pts(cx, cy, r, 270 - half_span_deg,
                          270 + half_span_deg, n), w)


def mirror(poly, sx, sy):
    return [(x * sx, y * sy) for x, y in poly]


def clip_rect(poly, x0, y0, x1, y1):
    """Sutherland-Hodgman clip of a convex polygon to a rectangle."""
    def clip(pts, inside, cross):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            ia, ib = inside(a), inside(b)
            if ia and ib:
                out.append(b)
            elif ia and not ib:
                out.append(cross(a, b))
            elif ib:
                out.append(cross(a, b))
                out.append(b)
        return out

    def xcross(xv):
        return lambda a, b: (xv, a[1] + (b[1] - a[1]) * (xv - a[0])
                             / (b[0] - a[0]))

    def ycross(yv):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yv - a[1])
                             / (b[1] - a[1]), yv)

    pts = list(poly)
    for inside, cross in (
            (lambda p: p[0] >= x0, xcross(x0)),
            (lambda p: p[0] <= x1, xcross(x1)),
            (lambda p: p[1] >= y0, ycross(y0)),
            (lambda p: p[1] <= y1, ycross(y1))):
        if len(pts) < 3:
            return []
        pts = clip(pts, inside, cross)
    clean = []
    for p in pts:
        if not clean or math.hypot(p[0] - clean[-1][0],
                                   p[1] - clean[-1][1]) > 1e-6:
            clean.append(p)
    if len(clean) > 1 and math.hypot(clean[0][0] - clean[-1][0],
                                     clean[0][1] - clean[-1][1]) < 1e-6:
        clean.pop()
    return clean


def poly_area(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i - 1]
        x1, y1 = poly[i]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2


# ---- Fusion helpers -----------------------------------------------------

def fixed_sketch(ctx, plane, name, z_cm, polys=(), circles=()):
    """Fixed-art sketch: closed polylines and circles at mm coordinates,
    mapped through the sketch's own transform (R6), then fixed."""
    sk = ctx.root.sketches.add(plane)
    sk.name = name
    sk.isComputeDeferred = True
    lines = sk.sketchCurves.sketchLines
    for poly in polys:
        adsk.doEvents()
        pts = [sk.modelToSketchSpace(ctx.pt(x * MM, y * MM, z_cm))
               for x, y in poly]
        first = lines.addByTwoPoints(pts[0], pts[1])
        prev = first
        for k in range(2, len(pts)):
            adsk.doEvents()
            prev = lines.addByTwoPoints(prev.endSketchPoint, pts[k])
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    for (x, y, r) in circles:
        adsk.doEvents()
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sk.modelToSketchSpace(ctx.pt(x * MM, y * MM, z_cm)), r * MM)
    for c in sk.sketchCurves:
        adsk.doEvents()
        if not c.isFixed:
            c.isFixed = True
    for sp in sk.sketchPoints:
        adsk.doEvents()
        if sp.isFullyConstrained or sp.isFixed:
            continue
        sp.isFixed = True
    sk.isComputeDeferred = False
    want = len(polys) + len(circles)
    if sk.profiles.count != want:
        raise RuntimeError("%s: %d profiles, expected %d"
                           % (name, sk.profiles.count, want))
    return sk


def prof_area(profs):
    total = 0.0
    for i in range(profs.count):
        total += profs.item(i).areaProperties().area
    return total


def depth_cm(ctx, expr):
    return ctx.des.unitsManager.evaluateExpression(expr, "cm")


def extrude(ctx, profs, op, dist_expr, name, participants=None, taper=None):
    inp = ctx.extrudes.createInput(profs, op)
    ext = adsk.fusion.DistanceExtentDefinition.create(ctx.cbs(dist_expr))
    if taper is None:
        inp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
    else:
        inp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection,
                             ctx.cbs(taper))
    if participants is not None:
        inp.participantBodies = participants
    f = ctx.extrudes.add(inp)
    f.name = name
    return f


def new_bodies(ctx, profs, dist_expr, name):
    f = extrude(ctx, profs, ctx.ops.NewBodyFeatureOperation, dist_expr,
                name + "_extrude")
    bodies = [f.bodies.item(i) for i in range(f.bodies.count)]
    if not bodies:
        raise RuntimeError("%s made no body" % name)
    if len(bodies) == 1:
        bodies[0].name = name
    else:
        for i, b in enumerate(bodies):
            b.name = "%s_%d" % (name, i + 1)
    return bodies


def cut_up(ctx, profs, dist_expr, targets, name):
    """Cut upward (+normal) from the sketch plane; volume-validated."""
    want = prof_area(profs) * depth_cm(ctx, dist_expr)
    v0 = sum(b.volume for b in targets)
    extrude(ctx, profs, ctx.ops.CutFeatureOperation, dist_expr,
            name + "_cut", participants=targets)
    dv = v0 - sum(b.volume for b in targets)
    if dv < 0.5 * want:
        raise RuntimeError("%s cut removed %.5f of %.5f cm3"
                           % (name, dv, want))


def join_up(ctx, profs, dist_expr, target, name):
    want = prof_area(profs) * depth_cm(ctx, dist_expr)
    v0 = target.volume
    extrude(ctx, profs, ctx.ops.JoinFeatureOperation, dist_expr,
            name + "_join", participants=[target])
    dv = target.volume - v0
    if dv < 0.4 * want:
        raise RuntimeError("%s join added %.5f of %.5f cm3"
                           % (name, dv, want))


def inlay(ctx, sk, target, depth_expr, name):
    """Flush colour inlay: pocket the target, then fill the pocket with
    new bodies from the same profiles."""
    profs = ctx.all_profiles(sk)
    cut_up(ctx, profs, depth_expr, [target], name)
    return new_bodies(ctx, ctx.all_profiles(sk), depth_expr, name)


def plane_at_y(ctx, expr, name, y_cm):
    """XZ-parallel datum at world y = y_cm. The offset sign is measured,
    never assumed (R6)."""
    for e in (expr, "-(%s)" % expr):
        adsk.doEvents()
        pin = ctx.planes.createInput()
        pin.setByOffset(ctx.root.xZConstructionPlane, ctx.cbs(e))
        pl = ctx.planes.add(pin)
        if abs(pl.geometry.origin.y - y_cm) < 1e-4:
            pl.name = name
            return pl
        pl.deleteMe()
    raise RuntimeError("no offset sign puts %s at y=%.3f" % (name, y_cm))


def leg_sockets(ctx, bodies, edge_expr, edge_cm, x_expr, x_cm,
                z_expr, z_cm):
    """Two round rope/leg sockets bored into the bottom (-Y) edge."""
    pl = plane_at_y(ctx, edge_expr, "leg_socket_plane", -edge_cm)
    sk = ctx.root.sketches.add(pl)
    sk.name = "leg_sockets"
    for sx in (1, -1):
        adsk.doEvents()
        ctx.bound_circle(sk, (sx * x_cm, -edge_cm, z_cm), 0.325,
                         "leg_hole_d", x_pos=x_expr, v_pos=z_expr)
    if sk.profiles.count != 2:
        raise RuntimeError("leg socket profiles %d" % sk.profiles.count)
    f = ctx.sym_cut(ctx.all_profiles(sk), "2 * leg_hole_depth", bodies,
                    min_vol_cm3=0.1)
    f.name = "leg_socket_cut"


def feet_and_legs(ctx, foot_x, foot_y, leg_xs, leg_y):
    """Two biscuit feet with piped-cream tops and rope sockets, plus two
    printable octagonal legs. Positions in mm; foot_y / leg_y signed."""
    root = ctx.root
    # discs
    skd = root.sketches.add(root.xYConstructionPlane)
    skd.name = "foot_discs"
    for sx in (1, -1):
        adsk.doEvents()
        ctx.bound_circle(skd, (sx * foot_x * MM, foot_y * MM, 0), 0.9,
                         "18 mm", x_pos="%g mm" % foot_x,
                         v_pos="%g mm" % abs(foot_y))
    discs = new_bodies(ctx, ctx.all_profiles(skd), "foot_disc_h",
                       "foot_disc")
    if len(discs) != 2:
        raise RuntimeError("foot discs %d" % len(discs))
    # piped cream: 8-point star, tapered inward
    plc = ctx.plane_at_z("foot_disc_h", "foot_cream_plane")
    zc = ctx.val("foot_disc_h")
    stars = []
    for sx in (1, -1):
        star = []
        for i in range(16):
            r = 8.2 if i % 2 == 0 else 6.2
            a = math.radians(i * 22.5)
            star.append((sx * foot_x + r * math.cos(a),
                         foot_y + r * math.sin(a)))
        stars.append(star)
    skc = fixed_sketch(ctx, plc, "foot_cream_stars", zc, polys=stars)
    prism = prof_area(ctx.all_profiles(skc)) * ctx.val("foot_cream_h")
    creams = None
    for taper in ("-12 deg", "12 deg"):
        adsk.doEvents()
        f = extrude(ctx, ctx.all_profiles(skc),
                    ctx.ops.NewBodyFeatureOperation, "foot_cream_h",
                    "foot_cream_extrude", taper=taper)
        got = [f.bodies.item(i) for i in range(f.bodies.count)]
        if sum(b.volume for b in got) < 0.95 * prism:
            creams = got
            break
        f.deleteMe()
    if creams is None or len(creams) != 2:
        raise RuntimeError("foot cream taper never narrowed")
    for i, b in enumerate(creams):
        b.name = "foot_cream_%d" % (i + 1)
    # rope socket down through the cream into the disc
    pls = ctx.plane_at_z("foot_disc_h + foot_cream_h", "foot_top_plane")
    zs = zc + ctx.val("foot_cream_h")
    sks = root.sketches.add(pls)
    sks.name = "foot_sockets"
    for sx in (1, -1):
        adsk.doEvents()
        ctx.bound_circle(sks, (sx * foot_x * MM, foot_y * MM, zs), 0.325,
                         "leg_hole_d", x_pos="%g mm" % foot_x,
                         v_pos="%g mm" % abs(foot_y))
    f = ctx.sym_cut(ctx.all_profiles(sks),
                    "2 * (foot_cream_h + foot_disc_h / 2)",
                    discs + creams, min_vol_cm3=0.1)
    f.name = "foot_socket_cut"
    # printable legs: square bar chamfered to an octagon, lying flat
    skl = root.sketches.add(root.xYConstructionPlane)
    skl.name = "printed_legs"
    for lx in leg_xs:
        adsk.doEvents()
        ctx.bound_rect2(skl, (lx * MM, leg_y * MM, 0), 0.28, 2.75,
                        u_size="leg_w", v_size="leg_len",
                        u_pos=("%g mm" % lx, "leg_w / 2"),
                        v_pos=("%g mm" % leg_y, "leg_len / 2"))
    legs = new_bodies(ctx, ctx.all_profiles(skl), "leg_w", "leg")
    if len(legs) != 2:
        raise RuntimeError("legs %d" % len(legs))
    leg_len_cm = ctx.val("leg_len")
    chf = root.features.chamferFeatures
    for n, leg in enumerate(legs):
        adsk.doEvents()
        coll = adsk.core.ObjectCollection.create()
        for e in leg.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            if abs(e.length - leg_len_cm) < 0.01:
                coll.add(e)
        if coll.count != 4:
            raise RuntimeError("leg long edges %d != 4" % coll.count)
        v0 = leg.volume
        ci = chf.createInput2()
        ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            coll, ctx.cbs("leg_w * 0.29"), True)
        cf = chf.add(ci)
        cf.name = "leg_octagon_chamfer_%d" % (n + 1)
        if v0 - leg.volume < 0.05 * v0:
            raise RuntimeError("leg chamfer removed too little")
    print("FH feet+legs ok")


def common_params(ctx):
    up, cbs = ctx.up, ctx.cbs
    up.add("inlay_d", cbs("0.6 mm"), "mm", "colour inlay depth")
    up.add("leg_hole_d", cbs("6.5 mm"), "mm", "rope / leg socket dia")
    up.add("leg_hole_depth", cbs("12 mm"), "mm", "socket depth from edge")
    up.add("leg_clear", cbs("0.9 mm"), "mm", "printed leg fit clearance")
    up.add("leg_w", cbs("leg_hole_d - leg_clear"), "mm", "printed leg AF")
    up.add("leg_len", cbs("55 mm"), "mm", "printed leg length")
    up.add("foot_disc_h", cbs("6 mm"), "mm", "foot biscuit height")
    up.add("foot_cream_h", cbs("7 mm"), "mm", "foot cream height")
