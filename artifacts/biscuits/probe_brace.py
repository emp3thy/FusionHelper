"""Read-only: does the print brace touch each leg part, and does it
introduce overhangs steeper than 45 degrees?"""
import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    by = {b.name: b for b in root.bRepBodies}
    for o in root.occurrences:
        for b in o.component.bRepBodies:
            by[b.name] = b
    br = by["print_brace"]
    out = {}
    for n in sorted(by):
        if n.startswith(("thigh", "shin", "leg")):
            out["gap_mm_" + n] = round(app.measureManager.measureMinimumDistance(br, by[n]).value * 10, 4)
    others = [n for n in by if not n.startswith(("thigh", "shin", "leg", "print_", "foot"))]
    out["gap_mm_to_biscuit"] = round(min(app.measureManager.measureMinimumDistance(br, by[n]).value for n in others) * 10, 3)
    bad = []
    for f in br.faces:
        bb = f.boundingBox
        if bb.maxPoint.z < 1e-4:
            continue
        pof = f.pointOnFace
        nrm = f.evaluator.getNormalAtPoint(pof)[1]
        tp = adsk.core.Point3D.create(pof.x + nrm.x * 0.002, pof.y + nrm.y * 0.002, pof.z + nrm.z * 0.002)
        sign = -1.0 if br.pointContainment(tp) == adsk.fusion.PointContainment.PointInsidePointContainment else 1.0
        if sign * nrm.z < -0.7075:
            bad.append([round(sign * nrm.z, 3), round(f.area * 100, 2)])
    out["brace_faces"] = br.faces.count
    out["brace_overhang_faces"] = bad
    print("FH_RESULT " + json.dumps(out))
