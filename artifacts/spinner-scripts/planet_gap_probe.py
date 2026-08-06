"""Read-only: what is under a planet's first layer, and by how much."""
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    mm = 10.0

    names = [b.name for b in root.bRepBodies]
    print("bodies:", names)
    pl = rot = st = None
    for b in root.bRepBodies:
        if pl is None and "planet" in b.name:
            pl = b
        if b.name == "hw_rotor":
            rot = b
        if b.name == "hw_stator":
            st = b
    if pl is None or rot is None or st is None:
        raise RuntimeError("Haywire bodies not found in the active doc")
    for b in (pl, rot, st):
        bb = b.boundingBox
        print("%-12s z %.2f .. %.2f mm" % (b.name, bb.minPoint.z * mm,
                                           bb.maxPoint.z * mm))

    d1 = app.measureManager.measureMinimumDistance(pl, rot)
    d2 = app.measureManager.measureMinimumDistance(pl, st)
    print("planet -> rotor  min gap: %.4f mm" % (d1.value * mm))
    print("planet -> stator min gap: %.4f mm" % (d2.value * mm))

    # planet's lowest faces, and its radial footprint
    zmin = pl.boundingBox.minPoint.z
    low_area = 0.0
    for i in range(pl.faces.count):
        f = pl.faces.item(i)
        bb = f.boundingBox
        if (abs(bb.maxPoint.z - bb.minPoint.z) < 1e-4
                and abs(bb.minPoint.z - zmin) < 1e-4):
            low_area += f.area
    print("planet first-layer (downward) area: %.1f mm2 at z %.2f mm"
          % (low_area * 100, zmin * mm))

    # what is under it: sweep radii across the planet footprint
    cen = pl.physicalProperties.centerOfMass
    r_st = (cen.x ** 2 + cen.y ** 2) ** 0.5
    print("planet centre at r %.2f mm" % (r_st * mm))
    for body, nm in ((rot, "rotor"), (st, "stator")):
        top = -1e9
        for i in range(body.faces.count):
            f = body.faces.item(i)
            bb = f.boundingBox
            if bb.maxPoint.z >= zmin - 1e-9:
                continue
            # only faces whose xy footprint can sit under the planet
            rr = max(abs(bb.minPoint.x), abs(bb.maxPoint.x))
            if rr * mm < 5:
                continue
            top = max(top, bb.maxPoint.z)
        print("  highest %s surface below the planet: z %.2f mm -> gap %.2f mm"
              % (nm, top * mm, (zmin - top) * mm))
