import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    up = des.userParameters
    up.add('plate_t', adsk.core.ValueInput.createByString('10 mm'), 'mm', 'plate thickness')
    up.add('brk_w', adsk.core.ValueInput.createByString('20 mm'), 'mm', 'bracket width')
    up.add('brk_h', adsk.core.ValueInput.createByString('15 mm'), 'mm', 'bracket height')

    # named construction plane at a parameter-bound offset
    planes = root.constructionPlanes
    pin = planes.createInput()
    pin.setByOffset(root.xYConstructionPlane,
                    adsk.core.ValueInput.createByString('plate_t'))
    lid_plane = planes.add(pin)
    lid_plane.name = 'lid_plane'

    sk = root.sketches.add(lid_plane)
    lines = sk.sketchCurves.sketchLines
    rect = lines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(2, 1.5, 0))

    sk.geometricConstraints.addCoincident(
        rect.item(0).startSketchPoint, sk.originPoint)

    for ln in rect:
        dx = abs(ln.endSketchPoint.geometry.x - ln.startSketchPoint.geometry.x)
        dy = abs(ln.endSketchPoint.geometry.y - ln.startSketchPoint.geometry.y)
        if dx >= dy:
            sk.geometricConstraints.addHorizontal(ln)
        else:
            sk.geometricConstraints.addVertical(ln)

    # two dimensions, each bound on the very next line
    w = sk.sketchDimensions.addDistanceDimension(
        rect.item(0).startSketchPoint, rect.item(0).endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(1, -0.5, 0))
    w.parameter.expression = 'brk_w'

    h = sk.sketchDimensions.addDistanceDimension(
        rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(2.5, 0.75, 0))
    h.parameter.expression = 'brk_h'

    print('bracket sketch fully constrained:', sk.isFullyConstrained)
