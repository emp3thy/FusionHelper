import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    up = adsk.core.Vector3D.create(0.0, 0.0, 1.0)  # EXPECT: R6
    sk = root.sketches.add(root.xZConstructionPlane)  # EXPECT: R6
    print(up, sk)
