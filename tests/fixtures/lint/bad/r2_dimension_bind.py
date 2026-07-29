import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    sk = des.rootComponent.sketches.item(0)
    p0 = sk.sketchPoints.item(0)
    p1 = sk.sketchPoints.item(1)
    anchor = adsk.core.Point3D.create(3, -1.5, 0)
    orient = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    d1 = sk.sketchDimensions.addDistanceDimension(  # EXPECT: R2  # noqa: F841
        p0, p1, orient, anchor
    )
    d2 = sk.sketchDimensions.addDistanceDimension(p0, p1, orient, anchor)
    d2.parameter.expression = "outer_w"
    sk.sketchDimensions.addDistanceDimension(p0, p1, orient, anchor)  # EXPECT: R2
