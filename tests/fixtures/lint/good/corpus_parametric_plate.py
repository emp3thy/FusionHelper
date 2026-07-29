import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    up = des.userParameters
    up.add('plate_w', adsk.core.ValueInput.createByString('60 mm'), 'mm', 'outer width')
    up.add('plate_d', adsk.core.ValueInput.createByString('40 mm'), 'mm', 'outer depth')
    up.add('plate_t', adsk.core.ValueInput.createByString('5 mm'), 'mm', 'plate thickness')

    sk = root.sketches.add(root.xYConstructionPlane)
    lines = sk.sketchCurves.sketchLines
    rect = lines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(6, 4, 0))          # seed only; approximately right is enough

    # 1. pin one corner to the origin
    sk.geometricConstraints.addCoincident(
        rect.item(0).startSketchPoint, sk.originPoint)

    # 2. horizontal / vertical on each line, decided by its own geometry, not by position
    for ln in rect:
        dx = abs(ln.endSketchPoint.geometry.x - ln.startSketchPoint.geometry.x)
        dy = abs(ln.endSketchPoint.geometry.y - ln.startSketchPoint.geometry.y)
        if dx >= dy:
            sk.geometricConstraints.addHorizontal(ln)
        else:
            sk.geometricConstraints.addVertical(ln)

    print('after constraints:', sk.isFullyConstrained)

    # 3. two dimensions, each bound
    w = sk.sketchDimensions.addDistanceDimension(
        rect.item(0).startSketchPoint, rect.item(0).endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(3, -1.5, 0))
    w.parameter.expression = 'plate_w'

    d = sk.sketchDimensions.addDistanceDimension(
        rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(7.5, 2, 0))
    d.parameter.expression = 'plate_d'

    print('fully constrained:', sk.isFullyConstrained)

    prof = sk.profiles.item(0)
    ext = root.features.extrudeFeatures
    inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('plate_t'))
    inp.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
    f = ext.add(inp)
    f.name = 'plate_body'
    print('done')
