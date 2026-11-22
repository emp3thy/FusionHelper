"""Read-only joint probe (temporary BRep only; the document is not
modified). For leg_1: pull-out retention (lift), swing clash from the
printed pose (straight out of the face) round to straight down, and an
overhang sweep of every body. Works before or after `ctl.py group`."""
import adsk.core, adsk.fusion, json, math

TIP = 0.5157   # cm: ball centre above its flat tip (4*sqrt(2) - 0.5 mm)


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    tbm = adsk.fusion.TemporaryBRepManager.get()
    by = {b.name: b for b in root.bRepBodies}
    for o in root.occurrences:
        for b in o.component.bRepBodies:
            by[b.name] = b
    body = [n for n in by if not n.startswith(("leg", "foot", "print_"))]
    lb = by["leg_1"].boundingBox
    # tab sticks out +Y only, so take x from the bbox and y from the rod top
    cx = (lb.minPoint.x + lb.maxPoint.x) / 2
    hip_z = lb.minPoint.z + TIP
    cy = lb.minPoint.y + 0.4          # ball radius 4 mm is the -Y extreme
    hip = (cx, cy, hip_z)

    def overlap(mat):
        total = 0.0
        for f in body:
            a = tbm.copy(by["leg_1"])
            if mat is not None:
                tbm.transform(a, mat)
            b = tbm.copy(by[f])
            try:
                tbm.booleanOperation(a, b, adsk.fusion.BooleanTypes.IntersectionBooleanType)
                total += a.volume
            except RuntimeError:
                pass
        return round(total * 1000, 3)

    def lift(dz):
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(0, 0, dz)
        return m

    def rot(deg):
        m = adsk.core.Matrix3D.create()
        m.setToRotation(math.radians(deg), adsk.core.Vector3D.create(1, 0, 0),
                        adsk.core.Point3D.create(*hip))
        return m

    out = {"hip_mm": [round(v * 10, 2) for v in hip],
           "leg_top_mm": round(lb.maxPoint.z * 10, 2),
           "rest": overlap(None), "lift_0.2": overlap(lift(0.02)),
           "lift_1.0": overlap(lift(0.10)), "lift_2.0": overlap(lift(0.20))}
    for deg in (15, 30, 45, 60, 75, 90, 100):
        out["swing_%d" % deg] = overlap(rot(deg))
    print("FH_RESULT " + json.dumps(out))
    for n, b in by.items():
        bad = []
        for f in b.faces:
            bb = f.boundingBox
            if bb.maxPoint.z < 1e-4:
                continue
            pof = f.pointOnFace
            nrm = f.evaluator.getNormalAtPoint(pof)[1]
            tp = adsk.core.Point3D.create(pof.x + nrm.x * 0.002,
                                          pof.y + nrm.y * 0.002,
                                          pof.z + nrm.z * 0.002)
            sign = -1.0 if b.pointContainment(tp) == adsk.fusion.PointContainment.PointInsidePointContainment else 1.0
            if sign * nrm.z < -0.7075:
                bad.append([round(sign * nrm.z, 3), round(f.area * 100, 2),
                            round(bb.minPoint.z * 10, 2)])
        if bad and n.startswith(("leg", "print_")):
            print("FH_RESULT overhang %s: [nz, mm2, z] %s" % (n, json.dumps(bad[:6])))
