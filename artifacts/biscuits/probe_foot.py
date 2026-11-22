"""Read-only: measured foot socket diameter in the active document."""
import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    out = {}
    for o in des.rootComponent.occurrences:
        for b in o.component.bRepBodies:
            if not b.name.startswith("foot_"):
                continue
            radii = sorted({round(f.geometry.radius * 20, 3) for f in b.faces
                            if f.geometry.objectType == adsk.core.Cylinder.classType()})
            out[b.name] = radii
    print("FH_RESULT cylinder diameters mm " + json.dumps(out))
