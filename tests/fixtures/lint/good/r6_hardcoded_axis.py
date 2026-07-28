import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    sk = root.sketches.add(root.xZConstructionPlane)
    origin_world = sk.sketchToModelSpace(adsk.core.Point3D.create(0, 0, 0))
    seed = adsk.core.Point3D.create(0.1, -0.2, 0)  # literal SEED coords: endorsed
    direction = sk.xDirection  # derived, not literal
    print(origin_world, seed, direction)
