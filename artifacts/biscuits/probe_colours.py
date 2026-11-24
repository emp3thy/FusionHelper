"""Read-only: appearance name of every body in the active document."""
import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    out = {}
    for o in root.occurrences:
        for b in o.component.bRepBodies:
            out[b.name] = b.appearance.name if b.appearance else None
    print("FH_RESULT " + json.dumps(out))
