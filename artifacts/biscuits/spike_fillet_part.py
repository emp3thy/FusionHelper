

# SPIKE (probe, not a part build): largest rim fillet a crimped spline
# outline accepts, per crimp amplitude. Run in an empty document, undo.

def sp_outline(amp):
    pts = []
    for i in range(192):
        a = 2 * math.pi * i / 192
        r = 29.0 + amp * math.cos(24 * a)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    fil = root.features.filletFeatures
    for amp in (0.7, 0.5, 0.35):
        sk = fixed_sketch(ctx, root.xYConstructionPlane,
                          "spike_%d" % int(amp * 100), 0,
                          splines=[sp_outline(amp)])
        body = new_bodies(ctx, ctx.all_profiles(sk), "6 mm",
                          "spike_body_%d" % int(amp * 100))[0]
        best = None
        for r10 in (20, 17, 15, 13, 12, 11, 10, 9):
            adsk.doEvents()
            coll = adsk.core.ObjectCollection.create()
            for e in body.edges:
                bb = e.boundingBox
                if (abs(bb.maxPoint.z - 0.6) < 1e-4
                        and abs(bb.minPoint.z - 0.6) < 1e-4):
                    coll.add(e)
            inp = fil.createInput()
            inp.edgeSetInputs.addConstantRadiusEdgeSet(
                coll, ctx.cbs("%g mm" % (r10 / 10)), True)
            try:
                f = fil.add(inp)
            except RuntimeError:
                continue
            ok = f.healthState == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
            f.deleteMe()
            if ok:
                best = r10 / 10
                break
        print("FH_RESULT amp %.2f max fillet %s" % (amp, best))
