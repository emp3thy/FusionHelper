import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    print("FH_RESULT " + json.dumps({
        "name": doc.name, "isSaved": doc.isSaved, "isModified": doc.isModified,
        "bodies": root.bRepBodies.count, "sketches": root.sketches.count,
        "timeline": des.timeline.count, "params": des.userParameters.count,
        "designType": des.designType, "units": des.unitsManager.defaultLengthUnits}))
