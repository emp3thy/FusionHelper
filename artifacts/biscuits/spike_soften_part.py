

# SPIKE (probe, not a part build): can the tops of the custard relief be
# filleted? Compares polyline strokes with smooth spline strokes. Run in
# an empty document, then undo.

def run(_context: str):
    global CC_SMOOTH
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    ctx.up.add("relief_h", ctx.cbs("0.8 mm"), "mm", "spike")
    ctx.up.add("emboss_taper", ctx.cbs("20 deg"), "deg", "spike")
    fil = root.features.filletFeatures
    healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
    for smooth in (False, True):
        CC_SMOOTH = smooth
        tag = "spl" if smooth else "pol"
        y0 = 7.0 if smooth else 0.0      # second slab sits beside the first
        sk0 = root.sketches.add(root.xYConstructionPlane)
        ctx.bound_rect2(sk0, (0, y0, 0), 2.25, 3.0, u_size="45 mm",
                        v_size="60 mm", u_pos=("0 mm", "22.5 mm"),
                        v_pos=("%g mm" % (y0 * 10), "30 mm"))
        slab = new_bodies(ctx, ctx.all_profiles(sk0), "5 mm",
                          "spike_slab_" + tag)[0]
        pl = ctx.plane_at_z("5 mm", "spike_plane_" + tag)
        ctx._resolved.pop("emboss_sign", None)
        sets = (("frame", cc_frame(), ()),
                ("corner", cc_big_spirals(), ()),
                ("top", cc_top_spirals(), ()),
                ("side", cc_side_spirals(), ()),
                ("tendrils", cc_tendrils(), ()),
                ("dots", (), cc_dots()))
        for nm, polys, circles in sets:
            adsk.doEvents()
            polys = [[(x, y + y0 * 10) for x, y in q] for q in polys]
            circles = [(x, y + y0 * 10, r) for x, y, r in circles]
            use_spl = smooth and nm not in ("frame", "dots")
            sk = fixed_sketch(ctx, pl, "spk_%s_%s" % (tag, nm), 0.5,
                              polys=() if use_spl else polys,
                              splines=polys if use_spl else (),
                              circles=circles)
            profs = ring_profile(sk) if nm == "frame" else ctx.all_profiles(sk)
            try:
                emboss(ctx, profs, slab, "spk_%s_%s" % (tag, nm))
            except RuntimeError as ex:
                print("FH_RESULT %s %s: EMBOSS FAIL %s" % (tag, nm, str(ex)[-60:]))
                continue
            res = []
            for r in ("0.3 mm", "0.2 mm", "0.12 mm"):
                adsk.doEvents()
                coll = adsk.core.ObjectCollection.create()
                for e in slab.edges:
                    bb = e.boundingBox
                    if (abs(bb.maxPoint.z - 0.58) < 1e-4
                            and abs(bb.minPoint.z - 0.58) < 1e-4):
                        coll.add(e)
                inp = fil.createInput()
                inp.edgeSetInputs.addConstantRadiusEdgeSet(coll, ctx.cbs(r), True)
                try:
                    f = fil.add(inp)
                except RuntimeError as ex:
                    res.append("%s FAIL" % r)
                    continue
                if f.healthState == healthy:
                    res.append("%s ok (%d edges)" % (r, coll.count))
                    break
                res.append("%s unhealthy" % r)
                f.deleteMe()
            print("FH_RESULT %s %s: %s" % (tag, nm, " | ".join(res)))
            # clean slab for the next set: drop this set's fillet + emboss
            if res and "ok" in res[-1]:
                fil.item(fil.count - 1).deleteMe()
            ctx.extrudes.item(ctx.extrudes.count - 1).deleteMe()
