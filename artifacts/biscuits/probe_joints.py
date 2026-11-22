"""Read-only joint probe for the jam biscuit (temporary BRep only, the
document is not modified). Measures pull-out retention and the 90 degree
swing at hip and knee as overlap volumes in mm3."""
import adsk.core, adsk.fusion, json, math

TIP = 0.5157   # cm: ball centre above its flat tip (4*sqrt(2) - 0.5 mm)


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    tbm = adsk.fusion.TemporaryBRepManager.get()
    by = {b.name: b for b in root.bRepBodies}

    def overlap(moving, fixed, mat):
        total = 0.0
        for f in fixed:
            a = tbm.copy(by[moving]) if isinstance(moving, str) else tbm.copy(moving)
            if mat is not None:
                tbm.transform(a, mat)
            b = tbm.copy(by[f]) if isinstance(f, str) else tbm.copy(f)
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

    def rot(centre, deg):
        m = adsk.core.Matrix3D.create()
        m.setToRotation(math.radians(deg), adsk.core.Vector3D.create(1, 0, 0),
                        adsk.core.Point3D.create(*centre))
        return m

    body = [n for n in by if not n.startswith(("thigh", "shin", "foot"))]
    sb = by["shin_1"].boundingBox
    tb = by["thigh_1"].boundingBox
    cx = (sb.minPoint.x + sb.maxPoint.x) / 2
    cy = (sb.minPoint.y + sb.maxPoint.y) / 2
    HIP = (cx, cy, tb.minPoint.z + TIP)
    KNEE = (cx, cy, sb.minPoint.z + TIP)
    print("FH_RESULT doc bodies %d, hip %s knee %s" % (
        len(by), [round(v * 10, 2) for v in HIP], [round(v * 10, 2) for v in KNEE]))
    out = {}
    out["hip_rest"] = overlap("thigh_1", body, None)
    out["hip_lift_0.2"] = overlap("thigh_1", body, lift(0.02))
    out["hip_lift_1.0"] = overlap("thigh_1", body, lift(0.10))
    out["hip_lift_2.0"] = overlap("thigh_1", body, lift(0.20))
    out["knee_rest"] = overlap("shin_1", ["thigh_1"], None)
    out["knee_lift_1.0"] = overlap("shin_1", ["thigh_1"], lift(0.10))
    out["knee_lift_2.0"] = overlap("shin_1", ["thigh_1"], lift(0.20))
    for deg in (30, 60, 90, 100):
        out["hip_swing_%d" % deg] = overlap("thigh_1", body, rot(HIP, deg))
        out["knee_swing_%d" % deg] = overlap("shin_1", ["thigh_1"], rot(KNEE, deg))
    out["hip_swing_back_-20"] = overlap("thigh_1", body, rot(HIP, -20))
    # tab volume for reference (3 tabs of 1.0 x 2.2 x 0.4 mm)
    out["one_tab_set_mm3"] = round(3 * 1.0 * 2.2 * 0.4, 2)
    print("FH_RESULT " + json.dumps(out))
    # overhang sweep: faces steeper than 45 deg from vertical (normal.z
    # below -0.7075), ignoring faces on the plate
    for b in root.bRepBodies:
        bad = []
        for f in b.faces:
            bb = f.boundingBox
            if bb.maxPoint.z < 1e-4:
                continue
            pof = f.pointOnFace
            nrm = res_n = f.evaluator.getNormalAtPoint(pof)[1]
            # orient outward: step along the normal; if that lands in
            # material the evaluator normal points inward
            tp = adsk.core.Point3D.create(pof.x + nrm.x * 0.002,
                                          pof.y + nrm.y * 0.002,
                                          pof.z + nrm.z * 0.002)
            sign = 1.0
            if b.pointContainment(tp) == adsk.fusion.PointContainment.PointInsidePointContainment:
                sign = -1.0
            nz = sign * res_n.z
            if nz < -0.7075:
                bad.append([round(nz, 3), round(f.area * 100, 2),
                            round(bb.minPoint.z * 10, 2), round(bb.maxPoint.z * 10, 2)])
        if bad:
            print("FH_RESULT overhang %s: %d faces [nz, mm2, zmin, zmax] %s"
                  % (b.name, len(bad), json.dumps(bad[:8])))
