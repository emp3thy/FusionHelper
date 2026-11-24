"""Read-only: root component id of every open document (is it a usable
per-document identity?)."""
import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    out = []
    for i in range(app.documents.count):
        d = app.documents.item(i)
        des = adsk.fusion.Design.cast(d.products.itemByProductType("DesignProductType"))
        out.append([des.rootComponent.id, des.rootComponent.name, des.rootComponent.occurrences.count])
    act = adsk.fusion.Design.cast(app.activeProduct)
    print("FH_RESULT " + json.dumps({"docs": out, "active": act.rootComponent.id}))
