import adsk.core
import adsk.fusion


def bind_all(dims, exprs):
    for d, e in zip(dims, exprs, strict=False):
        d.parameter.expression = e


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    sk = des.rootComponent.sketches.item(0)
    p0 = sk.sketchPoints.item(0)
    p1 = sk.sketchPoints.item(1)
    anchor = adsk.core.Point3D.create(3, -1.5, 0)
    orient = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    d1 = sk.sketchDimensions.addDistanceDimension(p0, p1, orient, anchor)
    d1.parameter.expression = "outer_w"
    d2 = sk.sketchDimensions.addDistanceDimension(p0, p1, orient, anchor)
    bind_all([d2], ["outer_d"])
