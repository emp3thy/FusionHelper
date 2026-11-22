"""Read-only: measured foot socket diameters in the active document
(bodies at root or inside components)."""
import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    bodies = [b for b in root.bRepBodies]
    for o in root.occurrences:
        bodies += [b for b in o.component.bRepBodies]
    out = {}
    for b in bodies:
        if not b.name.startswith("foot_"):
            continue
        out[b.name] = sorted({round(f.geometry.radius * 20, 3) for f in b.faces
                              if f.geometry.objectType == adsk.core.Cylinder.classType()})
    print("FH_RESULT cylinder diameters mm " + json.dumps(out))
