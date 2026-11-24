"""Read-only: timeline health and component layout of the active document."""
import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    tl = des.timeline
    bad = [tl.item(i).name for i in range(tl.count) if tl.item(i).healthState != 0]
    comps = {o.component.name: [b.name for b in o.component.bRepBodies] for o in root.occurrences}
    print("FH_RESULT " + json.dumps({"timeline": tl.count, "unhealthy": bad, "root_bodies": root.bRepBodies.count, "components": comps}))
