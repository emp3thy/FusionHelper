"""Read-only probe: find any face steeper than a 45-degree overhang, and
verify the roller's plate contact + clearances. Proves the two fixes."""
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # nz <= -0.7071 means the face overhangs steeper than 45 degrees
    LIMIT = -0.7071

    for bname in ("sn2_stator", "sn2_rotor", "sn2_roller_1"):
        body = root.bRepBodies.itemByName(bname)
        if body is None:
            print("MISSING", bname)
            continue
        worst = 0.0
        bad = []
        for i in range(body.faces.count):
            f = body.faces.item(i)
            ev = f.evaluator
            prange = ev.parametricRange()
            us = [prange.minPoint.x
                  + (prange.maxPoint.x - prange.minPoint.x) * t
                  for t in (0.15, 0.5, 0.85)]
            vs = [prange.minPoint.y
                  + (prange.maxPoint.y - prange.minPoint.y) * t
                  for t in (0.15, 0.5, 0.85)]
            pts = []
            for u in us:
                for v in vs:
                    pts.append(adsk.core.Point2D.create(u, v))
            # runtime returns [ok, [Vector3D, ...]] as a plain list
            res = ev.getNormalsAtParameters(pts)
            normals = res[1]
            if not normals:
                continue
            bb = f.boundingBox
            on_plate = (abs(bb.maxPoint.z) < 1e-4
                        and abs(bb.minPoint.z) < 1e-4)
            for nrm in normals:
                nz = nrm.z
                if nz < worst:
                    worst = nz
                if nz < LIMIT and not on_plate:
                    bad.append((i, round(nz, 4), f.objectType.split(':')[-1],
                                round(bb.minPoint.z * 10, 2)))
                    break
        print("%s: faces=%d worst_nz=%.4f  ILLEGAL=%d %s"
              % (bname, body.faces.count, worst, len(bad), bad[:6]))

    # roller vs plate and rails
    r1 = root.bRepBodies.itemByName("sn2_roller_1")
    rot = root.bRepBodies.itemByName("sn2_rotor")
    print("roller z-range mm: %.3f .. %.3f"
          % (r1.boundingBox.minPoint.z * 10, r1.boundingBox.maxPoint.z * 10))
    print("roller x-range mm: %.3f .. %.3f"
          % (r1.boundingBox.minPoint.x * 10, r1.boundingBox.maxPoint.x * 10))
    print("rotor  z-range mm: %.3f .. %.3f"
          % (rot.boundingBox.minPoint.z * 10, rot.boundingBox.maxPoint.z * 10))
    dist = app.measureManager.measureMinimumDistance(r1, rot)
    print("roller->rotor min distance mm: %.4f" % (dist.value * 10))
    st = root.bRepBodies.itemByName("sn2_stator")
    d2 = app.measureManager.measureMinimumDistance(st, rot)
    print("stator->rotor min distance mm: %.4f" % (d2.value * 10))
