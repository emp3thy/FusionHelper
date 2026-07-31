import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    for k in range(60):
        root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        adsk.doEvents()
