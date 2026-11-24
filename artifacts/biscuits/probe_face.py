"""Read-only: describe the small steep faces the overhang sweep found in
the jam body."""
import adsk.core, adsk.fusion, json


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    for b in root.bRepBodies:
        if b.name != "jam":
            continue
        for f in b.faces:
            bb = f.boundingBox
            if not (0.5 < f.area * 100 < 0.9):
                continue
            pof = f.pointOnFace
            n = f.evaluator.getNormalAtPoint(pof)[1]
            print("FH_RESULT " + json.dumps({
                "type": f.geometry.objectType, "area_mm2": round(f.area * 100, 3),
                "pt_mm": [round(pof.x * 10, 2), round(pof.y * 10, 2), round(pof.z * 10, 2)],
                "n": [round(n.x, 3), round(n.y, 3), round(n.z, 3)],
                "bb_min": [round(bb.minPoint.x * 10, 2), round(bb.minPoint.y * 10, 2), round(bb.minPoint.z * 10, 2)],
                "bb_max": [round(bb.maxPoint.x * 10, 2), round(bb.maxPoint.y * 10, 2), round(bb.maxPoint.z * 10, 2)]}))
