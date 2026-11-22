

# SPIKE (probe, not a part build): which taper angles each custard art
# set accepts as a tapered join. Run in an empty document, then undo.

def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    sk0 = root.sketches.add(root.xYConstructionPlane)
    ctx.bound_rect2(sk0, (0, 0, 0), 2.25, 3.0, u_size="45 mm",
                    v_size="60 mm", u_pos=("0 mm", "22.5 mm"),
                    v_pos=("0 mm", "30 mm"))
    slab = new_bodies(ctx, ctx.all_profiles(sk0), "5 mm", "spike_slab")[0]
    pl = ctx.plane_at_z("5 mm", "spike_plane")
    sets = (("frame", cc_frame(), ()),
            ("corner", cc_big_spirals(), ()),
            ("corner_one", cc_big_spirals()[:1], ()),
            ("top", cc_top_spirals(), ()),
            ("side", cc_side_spirals(), ()),
            ("tendrils", cc_tendrils(), ()),
            ("dots", (), cc_dots()))
    for nm, polys, circles in sets:
        sk = fixed_sketch(ctx, pl, "spk_" + nm, 0.5, polys=polys,
                          circles=circles)
        profs = ring_profile(sk) if nm == "frame" else ctx.all_profiles(sk)
        prism = prof_area(profs) * 0.08
        res = []
        for taper in ("-30 deg", "-20 deg", "-10 deg", "0 deg"):
            adsk.doEvents()
            v0 = slab.volume
            try:
                f = extrude(ctx, profs, ctx.ops.JoinFeatureOperation,
                            "0.8 mm", "spk_%s_%s" % (nm, taper[1:3]),
                            participants=[slab], taper=taper)
            except RuntimeError as ex:
                res.append("%s:FAIL(%s)" % (taper, str(ex)[-40:]))
                continue
            res.append("%s:ok %.2f" % (taper, (slab.volume - v0) / prism))
            f.deleteMe()
        print("FH_RESULT %s -> %s" % (nm, " | ".join(res)))
