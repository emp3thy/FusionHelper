"""Read-only: where are the overhangs, and what retains the stator?"""
import math

import adsk.core
import adsk.fusion

LIMIT = -0.7075


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    comp = root
    for i in range(root.occurrences.count):
        if root.occurrences.item(i).component.bRepBodies.count:
            comp = root.occurrences.item(i).component
            break
    mm = 10.0

    for body in comp.bRepBodies:
        if "roller" in body.name and not body.name.endswith("_1"):
            continue
        bad = []
        for f in body.faces:  # fusionhelper: allow R4 — enumeration, not an index pick
            ev = f.evaluator
            pr = ev.parametricRange()
            pts = []
            for t in (0.25, 0.5, 0.75):
                for u in (0.25, 0.5, 0.75):
                    pts.append(adsk.core.Point2D.create(
                        pr.minPoint.x + (pr.maxPoint.x - pr.minPoint.x) * t,
                        pr.minPoint.y + (pr.maxPoint.y - pr.minPoint.y) * u))
            normals = ev.getNormalsAtParameters(pts)[1]
            if not normals:
                continue
            bb = f.boundingBox
            if abs(bb.maxPoint.z) < 1e-4 and abs(bb.minPoint.z) < 1e-4:
                continue
            for n in normals:
                if n.z < LIMIT:
                    cx = (bb.maxPoint.x + bb.minPoint.x) / 2
                    cy = (bb.maxPoint.y + bb.minPoint.y) / 2
                    bad.append((round(math.hypot(cx, cy) * mm, 1),
                                round(bb.minPoint.z * mm, 1),
                                round(f.area * 100, 1)))
                    break
        print("%-14s faces=%3d  steeper_than_45=%2d  (r_mm, z_mm, area_mm2): %s"
              % (body.name, body.faces.count, len(bad),
                 sorted(bad)[:8]))

    # what stops the stator dropping out of the rotor?
    st = comp.bRepBodies.itemByName("or_stator")
    ro = comp.bRepBodies.itemByName("or_rotor")
    ridge_max = 0.0
    for f in st.faces:  # fusionhelper: allow R4 — enumeration, not an index pick
        bb = f.boundingBox
        if bb.minPoint.z > 0.50 and bb.maxPoint.z < 0.82:
            ridge_max = max(ridge_max,
                            max(abs(bb.maxPoint.x), abs(bb.minPoint.x)))
    bore_min = 99.0
    for f in ro.faces:  # fusionhelper: allow R4 — enumeration, not an index pick
        bb = f.boundingBox
        if bb.minPoint.z > 0.20 and bb.maxPoint.z < 1.10:
            rr = max(abs(bb.maxPoint.x), abs(bb.minPoint.x))
            if rr * mm > 5:
                bore_min = min(bore_min, rr)
    print("\nJOURNAL CAPTURE")
    print("  stator post ridge max radius : %.3f mm" % (ridge_max * mm))
    print("  rotor hub minimum bore radius: %.3f mm" % (bore_min * mm))
    print("  interlock = %.3f mm %s"
          % ((ridge_max - bore_min) * mm,
             "-> AXIALLY CAPTURED" if ridge_max > bore_min
             else "-> NOT captured, it would drop out"))
