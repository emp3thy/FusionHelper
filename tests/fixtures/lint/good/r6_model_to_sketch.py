import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    sk = root.sketches.add(root.xZConstructionPlane)
    seed = sk.modelToSketchSpace(adsk.core.Point3D.create(1.0, 0, 2.0))
    print(seed.x, seed.y)
