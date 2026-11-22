

# ========================= custard cream =================================
# Printed flat, face up. Bodies: biscuit_base, cream, biscuit_top (with
# raised diamond), scroll_* (brown inlaid scrollwork), ink_*, feet, legs.

CC_W, CC_H = 45.0, 60.0
CC_STROKE = 1.2


def cc_brackets():
    polys = []
    for sx in (1, -1):
        for sy in (1, -1):
            cl = ([(18.5, 14.0), (18.5, 21.0)]
                  + arc_pts(16.0, 23.0, 2.5, 0, 90, 6)
                  + [(14.0, 25.5), (8.0, 25.5)])
            polys.append(mirror(stroke(cl, CC_STROKE), sx, sy))
    return polys


def cc_curls():
    polys = []
    for sx in (1, -1):
        for sy in (1, -1):
            # corner curl, open towards the diamond
            polys.append(mirror(
                stroke(arc_pts(12.0, 19.5, 2.6, 250, -20, 14), CC_STROKE),
                sx, sy))
            # one bowl of the side "3"
            polys.append(mirror(
                stroke(arc_pts(16.0, 3.3, 2.3, 160, -80, 12), CC_STROKE),
                sx, sy))
    return polys


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up, cbs = ctx.up, ctx.cbs

    up.add("bis_t", cbs("5.5 mm"), "mm", "biscuit layer thickness")
    up.add("fill_t", cbs("4 mm"), "mm", "cream layer thickness")
    up.add("fill_inset", cbs("0.8 mm"), "mm", "cream set back from edge")
    up.add("diamond_h", cbs("1 mm"), "mm", "raised diamond height")
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

    # raised central diamond
    pl_face = ctx.plane_at_z("(2 * bis_t + fill_t)", "top_face_plane")
    skd = fixed_sketch(ctx, pl_face, "diamond", total,
                       polys=[[(9.0, 0), (0, 13.0), (-9.0, 0), (0, -13.0)]])
    join_up(ctx, ctx.all_profiles(skd), "diamond_h", top, "diamond")

    # brown scrollwork inlays
    pl_scroll = ctx.plane_at_z("(2 * bis_t + fill_t) - inlay_d", "scroll_plane")
    zs = total - inlay_cm
    skb = fixed_sketch(ctx, pl_scroll, "scroll_brackets", zs,
                       polys=cc_brackets())
    inlay(ctx, skb, top, "inlay_d", "scroll_bracket")
    skc = fixed_sketch(ctx, pl_scroll, "scroll_curls", zs,
                       polys=cc_curls())
    inlay(ctx, skc, top, "inlay_d", "scroll_curl")
    print("FH scrollwork ok")

    # face on the diamond
    pl_ink = ctx.plane_at_z("(2 * bis_t + fill_t) + diamond_h - inlay_d", "face_plane")
    zi = total + ctx.val("diamond_h") - inlay_cm
    sk_ink = fixed_sketch(
        ctx, pl_ink, "face_ink", zi,
        polys=[smile(0, 1.5, 3.2, 1.0)],
        circles=[(3.0, 2.6, 0.9), (-3.0, 2.6, 0.9)])
    inlay(ctx, sk_ink, top, "inlay_d", "ink")
    print("FH face ok")

    leg_sockets(ctx, [base, cream, top], "%g mm" % (CC_H / 2), hh,
                "10 mm", 1.0, "(2 * bis_t + fill_t) / 2", total / 2)
    feet_and_legs(ctx, 12, -47, (33, 42), 0)
    print("FH BUILD OK: %d bodies" % root.bRepBodies.count)
