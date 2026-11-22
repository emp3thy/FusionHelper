

# ========================= custard cream =================================
# Printed flat, face up. Bodies: biscuit_base, cream, biscuit_top (rounded
# corners, bevelled rim, embossed diamond frame and swirls), ink_*, feet,
# legs.

CC_W, CC_H = 45.0, 60.0
CC_STROKE = 1.4
CC_DIA = (15.0, 21.0)          # diamond frame centreline half-diagonals
CC_FRAME_W = 1.6


# Smooth (spline) stroke outlines. Measured (spike_soften): polyline
# swirls accept only a 0.12 mm top fillet; spline swirls accept 0.3.
CC_SMOOTH = True
CC_TOP_ROUND = "0.25 mm"       # rounding of the relief ridge tops


def cc_stroke(centre):
    if CC_SMOOTH:
        return stroke_round(centre, CC_STROKE)
    return stroke(centre, CC_STROKE)


def cc_frame():
    d = 1 / math.hypot(1 / CC_DIA[0], 1 / CC_DIA[1])
    out = []
    for k in ((d + CC_FRAME_W / 2) / d, (d - CC_FRAME_W / 2) / d):
        hx, hy = CC_DIA[0] * k, CC_DIA[1] * k
        out.append([(hx, 0), (0, hy), (-hx, 0), (0, -hy)])
    return out


def cc_quad(make):
    return [mirror(make(), sx, sy) for sx in (1, -1) for sy in (1, -1)]


def cc_big_spirals():
    return cc_quad(lambda: cc_stroke(spiral(15.3, 22.8, 1.5, 3.9, 1.1, 250, 26)))


def cc_top_spirals():
    # top edge only: the bottom pair would sit where the hips are
    return [mirror(q, 1, 1) for q in cc_quad(lambda: cc_stroke(spiral(6.0, 24.9, 1.5, 2.6, 0.75, 60, 16)))[0::2]]


def cc_side_spirals():
    return cc_quad(lambda: cc_stroke(spiral(17.5, 6.2, 1.5, 2.6, 0.75, 300, 16)))


def cc_tendrils():
    nrm = math.hypot(1 / CC_DIA[0], 1 / CC_DIA[1])
    nx, ny = 1 / CC_DIA[0] / nrm, 1 / CC_DIA[1] / nrm

    def one():
        pts = []
        for i in range(13):
            t = 0.24 + 0.44 * i / 12
            off = 3.7 + 0.7 * math.sin(2 * math.pi * i / 12)
            pts.append((CC_DIA[0] * t + nx * off,
                        CC_DIA[1] * (1 - t) + ny * off))
        return cc_stroke(pts)
    return cc_quad(one)


def cc_dots():
    dots = [(0, 25.4, 1.3), (0, -25.4, 1.3), (19.2, 0, 1.3), (-19.2, 0, 1.3)]
    for sx in (1, -1):
        for sy in (1, -1):
            dots.append((sx * 19.4, sy * 14.6, 1.2))
            dots.append((sx * 10.6, sy * 18.2, 1.2))
    return dots


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up, cbs = ctx.up, ctx.cbs

    up.add("bis_t", cbs("5.5 mm"), "mm", "biscuit layer thickness")
    up.add("fill_t", cbs("4 mm"), "mm", "cream layer thickness")
    up.add("fill_inset", cbs("0.8 mm"), "mm", "cream set back from edge")
    up.add("corner_r", cbs("4 mm"), "mm", "biscuit corner radius")
    # spike_emboss: the four corner swirls together fail a 30 deg
    # tapered join (ASM_INCONS_REL); every set passes at 20 deg.
    bevel_params(ctx, taper_deg=20)
    common_params(ctx)
    print("FH params added")

    bis = ctx.val("bis_t")
    fill = ctx.val("fill_t")
    total = 2 * bis + fill
    inlay_cm = ctx.val("inlay_d")
    inset = ctx.val("fill_inset")
    hw, hh = CC_W / 2 * MM, CC_H / 2 * MM

    def slab(plane, z_cm, name, dist_expr, shrink_cm=0.0):
        sk = root.sketches.add(plane)
        sk.name = name + "_outline"
        if shrink_cm:
            w_e = "(%g mm - 2 * fill_inset)" % CC_W
            h_e = "(%g mm - 2 * fill_inset)" % CC_H
        else:
            w_e = "%g mm" % CC_W
            h_e = "%g mm" % CC_H
        ctx.bound_rect2(sk, (0, 0, z_cm), hw - shrink_cm, hh - shrink_cm,
                        u_size=w_e, v_size=h_e,
                        u_pos=("0 mm", w_e + " / 2"),
                        v_pos=("0 mm", h_e + " / 2"))
        return new_bodies(ctx, ctx.all_profiles(sk), dist_expr, name)[0]

    base = slab(root.xYConstructionPlane, 0, "biscuit_base", "bis_t")
    pl_fill = ctx.plane_at_z("bis_t", "cream_plane")
    cream = slab(pl_fill, bis, "cream", "fill_t", shrink_cm=inset)
    pl_top = ctx.plane_at_z("bis_t + fill_t", "top_plane")
    top = slab(pl_top, bis + fill, "biscuit_top", "bis_t")
    print("FH sandwich: %.3f %.3f %.3f" % (base.volume, cream.volume,
                                           top.volume))

    # rounded corners, then bevelled rims on the two biscuit layers
    fillet_corners(ctx, base, "corner_r", "base_corner_fillet")
    fillet_corners(ctx, cream, "corner_r - fill_inset",
                   "cream_corner_fillet")
    fillet_corners(ctx, top, "corner_r", "top_corner_fillet")
    fillet_rims(ctx, base, "edge_fillet", "base_top_bevel", bis)
    fillet_rims(ctx, base, "under_fillet", "base_bed_bevel", 0)
    fillet_rims(ctx, top, "edge_fillet", "top_face_bevel", total)
    fillet_rims(ctx, top, "under_fillet", "top_under_bevel", bis + fill)
    print("FH fillets ok %.3f %.3f" % (base.volume, top.volume))

    # embossed pattern: diamond frame, swirls, tendrils and dots
    pl_emb = ctx.plane_at_z("(2 * bis_t + fill_t)", "emboss_plane")
    z_rel = total + ctx.val("relief_h")
    before = top_edge_keys(top, z_rel)
    skf = fixed_sketch(ctx, pl_emb, "diamond_frame", total,
                       polys=cc_frame())
    emboss(ctx, ring_profile(skf), top, "diamond_frame")
    soften_new_tops(ctx, top, z_rel, before, CC_TOP_ROUND,
                    "diamond_frame_round")
    for nm, strokes, circles in (
            ("swirl_corner", cc_big_spirals(), ()),
            ("swirl_top", cc_top_spirals(), ()),
            ("swirl_side", cc_side_spirals(), ()),
            ("tendrils", cc_tendrils(), cc_dots())):
        adsk.doEvents()
        before = top_edge_keys(top, z_rel)
        ske = fixed_sketch(ctx, pl_emb, nm, total, splines=strokes,
                           circles=circles)
        emboss(ctx, ctx.all_profiles(ske), top, nm)
        soften_new_tops(ctx, top, z_rel, before, CC_TOP_ROUND,
                        nm + "_round")
    print("FH emboss ok %.3f" % top.volume)

    # face inside the diamond
    pl_ink = ctx.plane_at_z("(2 * bis_t + fill_t) - face_sink - inlay_d",
                           "face_plane")
    zi = total - ctx.val("face_sink") - inlay_cm
    sk_ink = fixed_sketch(
        ctx, pl_ink, "face_ink", zi,
        polys=[smile(0, 2.5, 4.2, 1.2)],
        circles=[(4.0, 3.5, 1.1), (-4.0, 3.5, 1.1)])
    inlay(ctx, sk_ink, top, "inlay_d", "ink", sink_expr="face_sink")
    print("FH face ok")

    jointed_legs(ctx, [top, cream], 7.0, -24.5, total / MM)
    print_brace(ctx, 7.0, -24.5, total / MM, -CC_H / 2)
    feet(ctx, 12, -66)
    print("FH BUILD OK: %d bodies" % root.bRepBodies.count)
