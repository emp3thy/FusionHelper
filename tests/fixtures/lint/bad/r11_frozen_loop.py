import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    for _k in range(60):  # EXPECT: R11
        root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
