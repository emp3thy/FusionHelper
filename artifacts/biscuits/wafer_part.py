

# ============================ pink wafer =================================
# Printed flat, face up. Bodies: wafer (with layer grooves and raised
# lattice), ink_* (eyes, smile), cheek_*, feet, legs.

WF_W, WF_H = 35.0, 75.0
WF_PITCH = 8.0      # lattice line spacing along x, mm
WF_LINE_W = 1.2
WF_PANELS = ((-14.5, 11.0, 14.5, 34.5), (-14.5, -34.5, 14.5, -9.0))


def wf_lattice(sign):
    """Diagonal ridges x + sign*y = c, clipped to both panels."""
    polys = []
    half = WF_LINE_W / 2 * math.sqrt(2)   # half-width measured along x
    for (x0, y0, x1, y1) in WF_PANELS:
        k = -12
        while k <= 12:
            c = k * WF_PITCH + (y0 + y1) / 2 * sign
            big = 200.0
            # strip between x + sign*y = c - half and c + half
            quad = [(c - half - sign * (-big), -big),
                    (c + half - sign * (-big), -big),
                    (c + half - sign * big, big),
                    (c - half - sign * big, big)]
            poly = clip_rect(quad, x0, y0, x1, y1)
            if len(poly) >= 3 and poly_area(poly) > 4.0:
                polys.append(poly)
            k += 1
    return polys


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up, cbs = ctx.up, ctx.cbs

    up.add("wafer_t", cbs("16 mm"), "mm", "wafer thickness")
    up.add("groove_d", cbs("0.8 mm"), "mm", "layer groove depth")
    up.add("groove_h", cbs("1 mm"), "mm", "layer groove height")
    up.add("relief_h", cbs("0.8 mm"), "mm", "lattice ridge height")
    common_params(ctx)
    print("FH params added")

    t_cm = ctx.val("wafer_t")
    inlay_cm = ctx.val("inlay_d")
    gd = ctx.val("groove_d")
    hw, hh = WF_W / 2 * MM, WF_H / 2 * MM

    sk0 = root.sketches.add(root.xYConstructionPlane)
    sk0.name = "wafer_outline"
    ctx.bound_rect2(sk0, (0, 0, 0), hw, hh,
                    u_size="%g mm" % WF_W, v_size="%g mm" % WF_H,
                    u_pos=("0 mm", "%g mm" % (WF_W / 2)),
                    v_pos=("0 mm", "%g mm" % (WF_H / 2)))
    wafer = new_bodies(ctx, ctx.all_profiles(sk0), "wafer_t", "wafer")[0]
    print("FH block %.3f" % wafer.volume)

    # three layer grooves round the perimeter
    for k in (1, 2, 3):
        adsk.doEvents()
        z_expr = "wafer_t * %d / 4 - groove_h / 2" % k
        pl = ctx.plane_at_z(z_expr, "groove_plane_%d" % k)
        zk = depth_cm(ctx, z_expr)
        skg = root.sketches.add(pl)
        skg.name = "groove_ring_%d" % k
        ctx.bound_rect2(skg, (0, 0, zk), hw + 0.3, hh + 0.3,
                        u_size="%g mm" % (WF_W + 6),
                        v_size="%g mm" % (WF_H + 6),
                        u_pos=("0 mm", "%g mm" % (WF_W / 2 + 3)),
                        v_pos=("0 mm", "%g mm" % (WF_H / 2 + 3)))
        in_w = "(%g mm - 2 * groove_d)" % WF_W
        in_h = "(%g mm - 2 * groove_d)" % WF_H
        ctx.bound_rect2(skg, (0, 0, zk), hw - gd, hh - gd,
                        u_size=in_w, v_size=in_h,
                        u_pos=("0 mm", in_w + " / 2"),
                        v_pos=("0 mm", in_h + " / 2"))
        ring = adsk.core.ObjectCollection.create()
        for p in skg.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
            if p.profileLoops.count == 2:
                ring.add(p)
        if ring.count != 1:
            raise RuntimeError("groove ring profiles %d" % ring.count)
        v0 = wafer.volume
        extrude(ctx, ring, ctx.ops.CutFeatureOperation, "groove_h",
                "groove_cut_%d" % k, participants=[wafer])
        if v0 - wafer.volume < 0.05:
            raise RuntimeError("groove %d removed %.4f"
                               % (k, v0 - wafer.volume))
    print("FH grooves %.3f" % wafer.volume)

    # raised lattice, one sketch per diagonal direction so every ridge
    # is its own profile (crossing strokes in one sketch fill diamonds)
    pl_top = ctx.plane_at_z("wafer_t", "wafer_top_plane")
    for sign, nm in ((1, "lattice_fwd"), (-1, "lattice_back")):
        adsk.doEvents()
        skl = fixed_sketch(ctx, pl_top, nm, t_cm, polys=wf_lattice(sign))
        join_up(ctx, ctx.all_profiles(skl), "relief_h", wafer, nm)
    print("FH lattice %.3f" % wafer.volume)

    # face inlays in the plain band
    pl_face = ctx.plane_at_z("wafer_t - inlay_d", "face_plane")
    zf = t_cm - inlay_cm
    sk_ink = fixed_sketch(
        ctx, pl_face, "face_ink", zf,
        polys=[smile(0, 4.0, 4.6, 1.2)],
        circles=[(6.0, 5.0, 1.1), (-6.0, 5.0, 1.1)])
    inlay(ctx, sk_ink, wafer, "inlay_d", "ink")
    sk_chk = fixed_sketch(ctx, pl_face, "face_cheeks", zf,
                          circles=[(11.5, 1.5, 2.0), (-11.5, 1.5, 2.0)])
    inlay(ctx, sk_chk, wafer, "inlay_d", "cheek")
    print("FH face ok")

    jointed_legs(ctx, [wafer], 8.0, -32.0, t_cm / MM)
    feet(ctx, 12, -55)
    print("FH BUILD OK: %d bodies" % root.bRepBodies.count)
