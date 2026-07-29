import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    sk = des.rootComponent.sketches.item(0)
    dim = sk.sketchDimensions.item(0)
    dim.parameter.expression = "outer_w"  # R2's mandated binding — receiver is `parameter`
