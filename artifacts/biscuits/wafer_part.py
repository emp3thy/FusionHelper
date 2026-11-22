

# ============================ pink wafer =================================
# Printed flat, face up. Bodies: wafer_1..4 (pink sheets, the top one
# carrying the lattice and face), wafer_cream_1..3 (white layers),
# ink_*, cheek_*, feet, legs.

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

    # Four pink wafer sheets with three white cream layers between them.
    # The cream is set back groove_d from the edge, so the layer lines
    # read as white grooves round the sides.
    def slab(z_expr, h_expr, name, inset):
        z_cm = depth_cm(ctx, z_expr)
        if z_cm < 1e-9:
            plane = root.xYConstructionPlane
        else:
            plane = ctx.plane_at_z(z_expr, name + "_plane")
        sk = root.sketches.add(plane)
        sk.name = name + "_outline"
        if inset:
            w_e = "(%g mm - 2 * groove_d)" % WF_W
            h_e = "(%g mm - 2 * groove_d)" % WF_H
            shrink = gd
        else:
            w_e = "%g mm" % WF_W
            h_e = "%g mm" % WF_H
            shrink = 0.0
        ctx.bound_rect2(sk, (0, 0, z_cm), hw - shrink, hh - shrink,
                        u_size=w_e, v_size=h_e,
                        u_pos=("0 mm", w_e + " / 2"),
                        v_pos=("0 mm", h_e + " / 2"))
        return new_bodies(ctx, ctx.all_profiles(sk), h_expr, name)[0]

    sheets, creams = [], []
    for k in range(4):
        adsk.doEvents()
        z0 = "0 mm" if k == 0 else "wafer_t * %d / 4 + groove_h / 2" % k
        h = ("wafer_t / 4 - groove_h / 2" if k in (0, 3)
             else "wafer_t / 4 - groove_h")
        sheets.append(slab(z0, h, "wafer_%d" % (k + 1), False))
        if k < 3:
            creams.append(slab("wafer_t * %d / 4 - groove_h / 2" % (k + 1),
                               "groove_h", "wafer_cream_%d" % (k + 1), True))
    wafer = sheets[3]          # the face sheet
    pieces = sheets + creams
    print("FH sheets %.3f cream %.3f" % (sum(b.volume for b in sheets),
                                         sum(b.volume for b in creams)))

    # raised lattice, one sketch per diagonal direction so every ridge
    # is its own profile (crossing strokes in one sketch fill diamonds)
    pl_top = ctx.plane_at_z("wafer_t", "wafer_top_plane")
    for sign, nm in ((1, "lattice_fwd"), (-1, "lattice_back")):
        adsk.doEvents()
        skl = fixed_sketch(ctx, pl_top, nm, t_cm, polys=wf_lattice(sign))
        join_up(ctx, ctx.all_profiles(skl), "relief_h", wafer, nm)
    print("FH lattice %.3f" % wafer.volume)

    # face inlays in the plain band
    pl_face = ctx.plane_at_z("wafer_t - face_sink - inlay_d", "face_plane")
    zf = t_cm - ctx.val("face_sink") - inlay_cm
    sk_ink = fixed_sketch(
        ctx, pl_face, "face_ink", zf,
        polys=[smile(0, 4.0, 4.6, 1.2)],
        circles=[(6.0, 5.0, 1.1), (-6.0, 5.0, 1.1)])
    inlay(ctx, sk_ink, wafer, "inlay_d", "ink", sink_expr="face_sink")
    domed_cheeks(ctx, wafer, [(11.5, 1.5, 2.0), (-11.5, 1.5, 2.0)], t_cm / MM, inlay_cm / MM)
    print("FH face ok")

    _legs, zc, z_end = jointed_legs(ctx, pieces, 8.0, -32.0, t_cm / MM)
    print_brace(ctx, 8.0, -32.0, zc, z_end, -WF_H / 2)
    feet(ctx, 12, -74)
    print("FH BUILD OK: %d bodies" % root.bRepBodies.count)
