

# ======================= jammie (round jam sandwich) =====================
# Printed flat, face up. Bodies: biscuit_base, jam (layer + heart plug),
# biscuit_top (bevelled rim, embossed rim ring and splat), ink_* (eyes,
# smile), cheek_*, feet, legs.

JM_R_OUT = 29.5     # crimp crest radius, mm
JM_R_VAL = 28.5     # valley radius (spike: amp 0.5 takes a 2.0 fillet, amp 0.7 only 1.3)
JM_LOBES = 24
JM_FILL_INSET = 0.8
JM_HEART = (0.62, -5.0)        # scale, centre y
JM_ARM_ANGLES = (15, -25, -90, -155, 165)   # gaps at +-57 deg: hips
JM_HIP = (9.0, -22.1)          # hip socket x, y
JM_ARM_W = 3.2
JM_RING = (24.2, 26.6)         # embossed rim ring radii
JM_TOP_ROUND = "0.25 mm"       # rounding of the relief ridge tops


def jm_outline(inset):
    pts = []
    n = JM_LOBES * 8
    for i in range(n):
        a = 2 * math.pi * i / n
        r = ((JM_R_VAL + JM_R_OUT) / 2 + (JM_R_OUT - JM_R_VAL) / 2
             * math.cos(JM_LOBES * a)) - inset
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


def jm_splat():
    """Embossed arms radiating from the heart, with dots between them.
    The sector above the heart is left clear for the face."""
    heart = jm_heart(*JM_HEART)
    cy = JM_HEART[1]
    arms, dots = [], []

    def ray(deg, r):
        a = math.radians(deg)
        return (r * math.cos(a), cy + r * math.sin(a))

    for deg in JM_ARM_ANGLES:
        r = 0.0
        while in_poly(*ray(deg, r), heart):
            r += 0.1
        r_in = r + 2.0 + JM_ARM_W / 2
        r_out = r_in
        while math.hypot(*ray(deg, r_out + 0.1)) < 21.0:
            r_out += 0.1
        if r_out - r_in < 1.0:
            dots.append(ray(deg, r_in) + (JM_ARM_W / 2,))
        else:
            ax, ay = ray(deg, r_in)
            bx, by = ray(deg, r_out)
            arms.append(capsule(ax, ay, bx, by, JM_ARM_W))
    for k in range(len(JM_ARM_ANGLES) - 1):
        d0, d1 = JM_ARM_ANGLES[k], JM_ARM_ANGLES[k + 1]
        if abs(d0 - d1) > 60:
            continue
        mid = (d0 + d1) / 2
        r = 0.0
        while math.hypot(*ray(mid, r + 0.1)) < 20.6:
            r += 0.1
        dots.append(ray(mid, r) + (1.7,))
    return arms, dots


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up, cbs = ctx.up, ctx.cbs

    up.add("bis_t", cbs("6 mm"), "mm", "biscuit layer thickness")
    up.add("fill_t", cbs("4 mm"), "mm", "jam layer thickness")
    up.add("heart_recess", cbs("1.5 mm"), "mm", "jam below top face")
    bevel_params(ctx)
    common_params(ctx)
    print("FH params added")

    bis = ctx.val("bis_t")
    fill = ctx.val("fill_t")
    total = 2 * bis + fill
    inlay_cm = ctx.val("inlay_d")

    sk0 = fixed_sketch(ctx, root.xYConstructionPlane, "base_outline", 0,
                       splines=[jm_outline(0)])
    base = new_bodies(ctx, ctx.all_profiles(sk0), "bis_t",
                      "biscuit_base")[0]
    pl_fill = ctx.plane_at_z("bis_t", "jam_plane")
    sk1 = fixed_sketch(ctx, pl_fill, "jam_outline", bis,
                       splines=[jm_outline(JM_FILL_INSET)])
    jam = new_bodies(ctx, ctx.all_profiles(sk1), "fill_t", "jam")[0]
    pl_top = ctx.plane_at_z("bis_t + fill_t", "top_plane")
    sk2 = fixed_sketch(ctx, pl_top, "top_outline", bis + fill,
                       splines=[jm_outline(0)])
    top = new_bodies(ctx, ctx.all_profiles(sk2), "bis_t",
                     "biscuit_top")[0]
    print("FH sandwich: %.3f %.3f %.3f" % (base.volume, jam.volume,
                                           top.volume))

    # bevelled rims (before any cut, while each rim is one edge)
    fillet_rims(ctx, base, "edge_fillet", "base_top_bevel", bis)
    fillet_rims(ctx, base, "under_fillet", "base_bed_bevel", 0)
    fillet_rims(ctx, top, "edge_fillet", "top_face_bevel", total)
    fillet_rims(ctx, top, "under_fillet", "top_under_bevel", bis + fill)
    print("FH rims bevelled: %.3f %.3f" % (base.volume, top.volume))

    # heart window through the top, jam plug rising into it
    skh = fixed_sketch(ctx, pl_top, "heart", bis + fill,
                       polys=[jm_heart(*JM_HEART)])
    cut_up(ctx, ctx.all_profiles(skh), "bis_t", [top], "heart_window")
    join_up(ctx, ctx.all_profiles(skh), "bis_t - heart_recess", jam,
            "heart_plug")

    # embossed pattern: rim ring, splat arms and dots
    pl_emb = ctx.plane_at_z("(2 * bis_t + fill_t)", "emboss_plane")
    z_rel = total + ctx.val("relief_h")
    before = top_edge_keys(top, z_rel)
    skr = fixed_sketch(ctx, pl_emb, "rim_ring", total,
                       circles=[(0, 0, JM_RING[0]), (0, 0, JM_RING[1])])
    emboss(ctx, ring_profile(skr), top, "rim_ring")
    soften_new_tops(ctx, top, z_rel, before, JM_TOP_ROUND, "rim_ring_round")
    arms, dots = jm_splat()
    # arm outlines as closed splines so their tops take a fillet
    before = top_edge_keys(top, z_rel)
    sks = fixed_sketch(ctx, pl_emb, "splat_arms", total, splines=arms)
    emboss(ctx, ctx.all_profiles(sks), top, "splat_arms")
    soften_new_tops(ctx, top, z_rel, before, JM_TOP_ROUND,
                    "splat_arms_round")
    # dimples: raised buttons with the top edge rolled over into a dome
    skd = fixed_sketch(ctx, pl_emb, "dimples", total, circles=dots)
    join_up(ctx, ctx.all_profiles(skd), "relief_h", top, "dimples")
    z_dome = total + ctx.val("relief_h")
    dome_edges = adsk.core.ObjectCollection.create()
    for e in top.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
        bb = e.boundingBox
        rad = getattr(e.geometry, "radius", None)
        if (rad is not None and rad < 0.3
                and abs(bb.maxPoint.z - z_dome) < 1e-4
                and abs(bb.minPoint.z - z_dome) < 1e-4):
            dome_edges.add(e)
    if dome_edges.count != len(dots):
        raise RuntimeError("dimple edges %d != %d"
                           % (dome_edges.count, len(dots)))
    v_d = top.volume
    fil = root.features.filletFeatures
    finp = fil.createInput()
    finp.edgeSetInputs.addConstantRadiusEdgeSet(
        dome_edges, cbs("relief_h * 0.9"), False)
    fdome = fil.add(finp)
    fdome.name = "dimple_domes"
    if (fdome.healthState
            != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
            or v_d - top.volume < 1e-5):
        raise RuntimeError("dimple dome fillet failed")
    print("FH emboss ok %.3f" % top.volume)

    # face inlays
    pl_face = ctx.plane_at_z("(2 * bis_t + fill_t) - face_sink - inlay_d",
                            "face_plane")
    zf = total - ctx.val("face_sink") - inlay_cm
    sk_ink = fixed_sketch(
        ctx, pl_face, "face_ink", zf,
        polys=[smile(0, 13.5, 6.0, 1.3)],
        circles=[(7.5, 14.5, 1.2), (-7.5, 14.5, 1.2)])
    inlay(ctx, sk_ink, top, "inlay_d", "ink", sink_expr="face_sink")
    domed_cheeks(ctx, top, [(14.5, 9.0, 2.5), (-14.5, 9.0, 2.5)], total / MM, inlay_cm / MM)
    print("FH face ok")

    jointed_legs(ctx, [top, jam], JM_HIP[0], JM_HIP[1], total / MM)
    feet(ctx, 12, -48)
    print("FH BUILD OK: %d bodies" % root.bRepBodies.count)
