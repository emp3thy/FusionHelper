

# ======================= jammie (round jam sandwich) =====================
# Printed flat, face up. Bodies: biscuit_base, jam (layer + heart plug),
# biscuit_top, ink_* (eyes, smile), cheek_*, feet, legs.

JM_R_OUT = 30.0     # lobe crest radius, mm
JM_R_VAL = 28.0     # valley radius
JM_LOBES = 24
JM_FILL_INSET = 0.8


def jm_outline(inset):
    pts = []
    n = JM_LOBES * 8
    for i in range(n):
        a = 2 * math.pi * i / n
        r = (JM_R_VAL + (JM_R_OUT - JM_R_VAL)
             * abs(math.sin(JM_LOBES * a / 2))) - inset
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def jm_heart(scale, cy):
    pts = []
    for i in range(48):
        t = 2 * math.pi * i / 48
        x = 16 * math.sin(t) ** 3
        y = (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t)
             - math.cos(4 * t))
        pts.append((x * scale, y * scale + cy))
    return pts


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up, cbs = ctx.up, ctx.cbs

    up.add("bis_t", cbs("6 mm"), "mm", "biscuit layer thickness")
    up.add("fill_t", cbs("4 mm"), "mm", "jam layer thickness")
    up.add("heart_recess", cbs("1.5 mm"), "mm", "jam below top face")
    common_params(ctx)
    print("FH params added")

    bis = ctx.val("bis_t")
    fill = ctx.val("fill_t")
    total = 2 * bis + fill
    inlay_cm = ctx.val("inlay_d")

    # base biscuit
    sk0 = fixed_sketch(ctx, root.xYConstructionPlane, "base_outline", 0,
                       polys=[jm_outline(0)])
    base = new_bodies(ctx, ctx.all_profiles(sk0), "bis_t",
                      "biscuit_base")[0]
    # jam layer
    pl_fill = ctx.plane_at_z("bis_t", "jam_plane")
    sk1 = fixed_sketch(ctx, pl_fill, "jam_outline", bis,
                       polys=[jm_outline(JM_FILL_INSET)])
    jam = new_bodies(ctx, ctx.all_profiles(sk1), "fill_t", "jam")[0]
    # top biscuit
    pl_top = ctx.plane_at_z("bis_t + fill_t", "top_plane")
    sk2 = fixed_sketch(ctx, pl_top, "top_outline", bis + fill,
                       polys=[jm_outline(0)])
    top = new_bodies(ctx, ctx.all_profiles(sk2), "bis_t",
                     "biscuit_top")[0]
    print("FH sandwich: %.3f %.3f %.3f" % (base.volume, jam.volume,
                                           top.volume))

    # heart window through the top, jam plug rising into it
    skh = fixed_sketch(ctx, pl_top, "heart", bis + fill,
                       polys=[jm_heart(0.68, -5.0)])
    cut_up(ctx, ctx.all_profiles(skh), "bis_t", [top], "heart_window")
    join_up(ctx, ctx.all_profiles(skh), "bis_t - heart_recess", jam,
            "heart_plug")

    # face inlays
    pl_face = ctx.plane_at_z("(2 * bis_t + fill_t) - inlay_d", "face_plane")
    zf = total - inlay_cm
    sk_ink = fixed_sketch(
        ctx, pl_face, "face_ink", zf,
        polys=[smile(0, 13.5, 6.0, 1.3)],
        circles=[(7.5, 14.5, 1.2), (-7.5, 14.5, 1.2)])
    inlay(ctx, sk_ink, top, "inlay_d", "ink")
    sk_chk = fixed_sketch(ctx, pl_face, "face_cheeks", zf,
                          circles=[(14.5, 9.0, 2.5), (-14.5, 9.0, 2.5)])
    inlay(ctx, sk_chk, top, "inlay_d", "cheek")
    print("FH face ok")

    leg_sockets(ctx, [base, jam, top], "%g mm" % JM_R_OUT, JM_R_OUT * MM,
                "9 mm", 0.9, "(2 * bis_t + fill_t) / 2", total / 2)
    feet_and_legs(ctx, 12, -48, (40, 49), 0)
    print("FH BUILD OK: %d bodies" % root.bRepBodies.count)
