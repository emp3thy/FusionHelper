"""Read-only: state of every open document (no activation)."""
import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    out = []
    for i in range(app.documents.count):
        d = app.documents.item(i)
        des = adsk.fusion.Design.cast(d.products.itemByProductType("DesignProductType"))
        root = des.rootComponent
        names = [b.name for b in root.bRepBodies]
        for o in root.occurrences:
            names += [o.component.name + "/" + b.name for b in o.component.bRepBodies]
        params = [des.userParameters.item(k).name for k in range(des.userParameters.count)]
        out.append({"i": i, "active": d == app.activeDocument, "timeline": des.timeline.count,
                    "root_bodies": root.bRepBodies.count, "occ": root.occurrences.count,
                    "n_bodies": len(names), "sample": names[:3], "has_face_sink": "face_sink" in params,
                    "n_params": len(params)})
    print("FH_RESULT " + json.dumps(out))
