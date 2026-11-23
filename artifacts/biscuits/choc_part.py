

# =================== chocolate sandwich cookie ==========================
# Printed flat, face up. Same size and face layout as the jam biscuit.
# Bodies: choc_base, filling (white), choc_top (bevelled rim, embossed
# tick ring, ring line, flowers and a plain oval where the jam biscuit
# has its heart), ink_* (eyes and smile - painted WHITE on this dark
# cookie), feet, legs, print brace. No brand name or emblem.

CH_R = 29.5                    # cookie radius, mm
CH_FILL_INSET = 1.5
CH_HIP = (9.0, -22.1)
CH_TICKS = 60
CH_RING = (23.4, 24.4)
CH_FLOWER_R = 17.5             # radius of the flower ring
CH_OVAL = (11.0, 6.5)          # oval frame centreline semi-axes
CH_OVAL_Y = -4.0               # oval centre (the face sits above it)
CH_OVAL_W = 1.2
CH_TOP_ROUND = "0.2 mm"


def ch_ticks():
    polys = []
    for i in range(CH_TICKS):
        a = 2 * math.pi * i / CH_TICKS
        ca, sa = math.cos(a), math.sin(a)
        quad = []
        for r, t in ((25.6, -0.6), (27.6, -0.6), (27.6, 0.6), (25.6, 0.6)):
            quad.append((r * ca - t * sa, r * sa + t * ca))
        polys.append(quad)
    return polys


def ch_flowers():
    """Four-petal flowers on a ring; none behind the face (top) and none
    where the hips are."""
    dots = []
    for k in range(12):
        if 45 < (90 - 30 * k) % 360 < 135:
            continue
        a = math.radians(90 - 30 * k)
        cx, cy = CH_FLOWER_R * math.cos(a), CH_FLOWER_R * math.sin(a)
        if min(math.hypot(cx - sx * CH_HIP[0], cy - CH_HIP[1])
               for sx in (1, -1)) < 7.5:
            continue
        for q in range(4):
            b = a + math.radians(45 + 90 * q)
            dots.append((cx + 1.75 * math.cos(b), cy + 1.75 * math.sin(b), 1.15))
    return dots


def ch_oval(half_w):
    out = []
    for da in (half_w, -half_w):
        pts = []
        for i in range(48):
            t = 2 * math.pi * i / 48
            pts.append(((CH_OVAL[0] + da) * math.cos(t),
                        CH_OVAL_Y + (CH_OVAL[1] + da) * math.sin(t)))
        out.append(pts)
    return out


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up, cbs = ctx.up, ctx.cbs

    up.add("bis_t", cbs("6 mm"), "mm", "cookie layer thickness")
    up.add("fill_t", cbs("4 mm"), "mm", "filling thickness")
    bevel_params(ctx, taper_deg=20, relief="0.6 mm")
    common_params(ctx)
    print("FH params added")

    bis = ctx.val("bis_t")
    fill = ctx.val("fill_t")
    total = 2 * bis + fill
    inlay_cm = ctx.val("inlay_d")

    sk0 = fixed_sketch(ctx, root.xYConstructionPlane, "base_outline", 0,
                       circles=[(0, 0, CH_R)])
    base = new_bodies(ctx, ctx.all_profiles(sk0), "bis_t", "choc_base")[0]
    pl_fill = ctx.plane_at_z("bis_t", "filling_plane")
    sk1 = fixed_sketch(ctx, pl_fill, "filling_outline", bis,
                       circles=[(0, 0, CH_R - CH_FILL_INSET)])
    filling = new_bodies(ctx, ctx.all_profiles(sk1), "fill_t", "filling")[0]
    pl_top = ctx.plane_at_z("bis_t + fill_t", "top_plane")
    sk2 = fixed_sketch(ctx, pl_top, "top_outline", bis + fill,
                       circles=[(0, 0, CH_R)])
    top = new_bodies(ctx, ctx.all_profiles(sk2), "bis_t", "choc_top")[0]
    print("FH sandwich: %.3f %.3f %.3f" % (base.volume, filling.volume,
                                           top.volume))

    fillet_rims(ctx, base, "edge_fillet", "base_top_bevel", bis)
    fillet_rims(ctx, base, "under_fillet", "base_bed_bevel", 0)
    fillet_rims(ctx, top, "edge_fillet", "top_face_bevel", total)
    fillet_rims(ctx, top, "under_fillet", "top_under_bevel", bis + fill)
    print("FH rims bevelled: %.3f %.3f" % (base.volume, top.volume))

    # embossed pattern. The ring line goes first: emboss() needs a simple
    # shape to learn the taper sign from.
    pl_emb = ctx.plane_at_z("(2 * bis_t + fill_t)", "emboss_plane")
    z_rel = total + ctx.val("relief_h")
    before = top_edge_keys(top, z_rel)
    skr = fixed_sketch(ctx, pl_emb, "ring_line", total,
                       circles=[(0, 0, CH_RING[0]), (0, 0, CH_RING[1])])
    emboss(ctx, ring_profile(skr), top, "ring_line")
    soften_new_tops(ctx, top, z_rel, before, CH_TOP_ROUND, "ring_line_round")
    before = top_edge_keys(top, z_rel)
    sko = fixed_sketch(ctx, pl_emb, "face_oval", total,
                       splines=ch_oval(CH_OVAL_W / 2))
    emboss(ctx, ring_profile(sko), top, "face_oval")
    soften_new_tops(ctx, top, z_rel, before, CH_TOP_ROUND, "face_oval_round")
    skt = fixed_sketch(ctx, pl_emb, "rim_ticks", total, polys=ch_ticks())
    emboss(ctx, ctx.all_profiles(skt), top, "rim_ticks")
    skf = fixed_sketch(ctx, pl_emb, "flowers", total, circles=ch_flowers())
    emboss(ctx, ctx.all_profiles(skf), top, "flowers")
    print("FH emboss ok %.3f" % top.volume)

    # face in the jam biscuit's position, sunk below the surface
    pl_face = ctx.plane_at_z("(2 * bis_t + fill_t) - face_sink - inlay_d",
                            "face_plane")
    zf = total - ctx.val("face_sink") - inlay_cm
    sk_ink = fixed_sketch(
        ctx, pl_face, "face_ink", zf,
        polys=[smile(0, 13.5, 6.0, 1.3)],
        circles=[(7.5, 14.5, 1.2), (-7.5, 14.5, 1.2)])
    inlay(ctx, sk_ink, top, "inlay_d", "ink", sink_expr="face_sink")
    print("FH face ok")

    _legs, zc, z_end = jointed_legs(ctx, [top, filling, base], CH_HIP[0],
                                    CH_HIP[1], total / MM)
    print_brace(ctx, CH_HIP[0], CH_HIP[1], zc, z_end, -CH_R)
    feet(ctx, 12, -66)
    print("FH BUILD OK: %d bodies" % root.bRepBodies.count)
