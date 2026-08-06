"""Read-only: confirm the V-way actually captures the roller."""
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    mm = 10.0
    roll = rot = None
    for b in root.bRepBodies:
        if "roller" in b.name and roll is None:
            roll = b
        if b.name == "sn3_rotor":
            rot = b
    if roll is None or rot is None:
        raise RuntimeError("rev C bodies not found in the active doc")
    bb = roll.boundingBox
    print("roller z: %.2f .. %.2f mm" % (bb.minPoint.z * mm,
                                         bb.maxPoint.z * mm))
    d = app.measureManager.measureMinimumDistance(roll, rot)
    print("roller -> rotor min gap: %.4f mm" % (d.value * mm))

    # narrowest point of the roller = the V-groove waist
    cen = roll.physicalProperties.centerOfMass
    best = 99.0
    for f in roll.faces:  # fusionhelper: allow R4 — enumeration, not an index pick
        g = f.geometry
        r = getattr(g, "radius", None)
        if r is not None and r * mm < best * mm:
            best = r
    print("roller waist radius (V-groove apex): %.3f mm" % (best * mm))
    print("roller centre at y = %.2f mm" % (cen.y * mm))

    # overhang audit on the two changed bodies
    for body in (roll, rot):
        bad = 0
        for f in body.faces:  # fusionhelper: allow R4 — enumeration, not an index pick
            ev = f.evaluator
            pr = ev.parametricRange()
            pts = []
            for t in (0.2, 0.5, 0.8):
                for u in (0.2, 0.5, 0.8):
                    pts.append(adsk.core.Point2D.create(
                        pr.minPoint.x + (pr.maxPoint.x - pr.minPoint.x) * t,
                        pr.minPoint.y + (pr.maxPoint.y - pr.minPoint.y) * u))
            res = ev.getNormalsAtParameters(pts)
            fb = f.boundingBox
            if abs(fb.maxPoint.z) < 1e-4 and abs(fb.minPoint.z) < 1e-4:
                continue
            for nrm in res[1]:
                if nrm.z < -0.7075:
                    bad += 1
                    break
        print("%-12s faces=%3d steeper_than_45=%d" % (body.name,
                                                      body.faces.count, bad))
