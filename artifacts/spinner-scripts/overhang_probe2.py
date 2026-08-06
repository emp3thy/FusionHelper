"""Read-only probe: faces steeper than a 45-degree overhang, plus roller
plate contact and clearances."""
import adsk.core
import adsk.fusion

LIMIT = -0.7075   # 45 deg is -0.70711; allow float noise


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    bodies = []
    names = []
    for b in root.bRepBodies:  # fusionhelper: allow R4 — enumeration, not an index pick
        bodies.append(b)
        names.append(b.name)
    print("bodies:", names)

    for body in bodies:
        bname = body.name
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
            res = ev.getNormalsAtParameters(pts)
            normals = res[1]
            if not normals:
                continue
            bb = f.boundingBox
            if abs(bb.maxPoint.z) < 1e-4 and abs(bb.minPoint.z) < 1e-4:
                continue                      # sits on the build plate
            for nrm in normals:
                if nrm.z < LIMIT:
                    bad.append((round(nrm.z, 4),
                                round(bb.minPoint.z * 10, 2),
                                round(bb.maxPoint.x * 10
                                      - bb.minPoint.x * 10, 2)))
                    break
        print("%-14s faces=%3d  steeper_than_45=%d  %s"
              % (bname, body.faces.count, len(bad), bad[:8]))

    r1 = root.bRepBodies.itemByName("sn2_roller_1")
    if r1 is None:
        for nm in names:
            if "roller" in nm:
                r1 = root.bRepBodies.itemByName(nm)
                break
    rot = root.bRepBodies.itemByName("sn2_rotor")
    st = root.bRepBodies.itemByName("sn2_stator")
    print("roller z mm: %.3f .. %.3f (0.000 = on the build plate)"
          % (r1.boundingBox.minPoint.z * 10,
             r1.boundingBox.maxPoint.z * 10))
    d1 = app.measureManager.measureMinimumDistance(r1, rot)
    print("roller -> rotor  min gap mm: %.4f" % (d1.value * 10))
    d2 = app.measureManager.measureMinimumDistance(st, rot)
    print("stator -> rotor  min gap mm: %.4f" % (d2.value * 10))
