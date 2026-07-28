import adsk.core
import adsk.fusion


def top_face(body, tol=1e-6):
    """Largest face whose planar normal points along +Z."""
    best = None
    for f in body.faces:
        g = f.geometry
        if not isinstance(g, adsk.core.Plane):
            continue
        n = g.normal
        if n.z > 1 - tol and abs(n.x) < tol and abs(n.y) < tol:
            if best is None or f.area > best.area:
                best = f
    return best


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    up = des.userParameters
    up.add('pick_w', adsk.core.ValueInput.createByString('60 mm'), 'mm', 'pick plate width')
    up.add('pick_d', adsk.core.ValueInput.createByString('40 mm'), 'mm', 'pick plate depth')
    up.add('pick_t', adsk.core.ValueInput.createByString('5 mm'), 'mm', 'pick plate thickness')

    sk = root.sketches.add(root.xYConstructionPlane)
    lines = sk.sketchCurves.sketchLines
    rect = lines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(6, 4, 0))
    sk.geometricConstraints.addCoincident(
        rect.item(0).startSketchPoint, sk.originPoint)
    for ln in rect:
        dx = abs(ln.endSketchPoint.geometry.x - ln.startSketchPoint.geometry.x)
        dy = abs(ln.endSketchPoint.geometry.y - ln.startSketchPoint.geometry.y)
        if dx >= dy:
            sk.geometricConstraints.addHorizontal(ln)
        else:
            sk.geometricConstraints.addVertical(ln)

    w = sk.sketchDimensions.addDistanceDimension(
        rect.item(0).startSketchPoint, rect.item(0).endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(3, -1.5, 0))
    w.parameter.expression = 'pick_w'
    d = sk.sketchDimensions.addDistanceDimension(
        rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(7.5, 2, 0))
    d.parameter.expression = 'pick_d'

    prof = sk.profiles.item(0)
    ext = root.features.extrudeFeatures
    inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('pick_t'))
    inp.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
    f = ext.add(inp)
    f.name = 'pick_body'

    body = None
    for b in f.bodies:
        body = b
        break

    # entityToken capture and round-trip: never keep a BRepFace across a rebuild
    face = top_face(body)
    tok = face.entityToken if face else None       # capture BEFORE the rebuild

    adsk.doEvents()

    found = des.findEntityByToken(tok) if tok else None
    face = found[0] if found else None              # never string-compare tokens
    print('resolved by predicate:', top_face(body) is not None,
          'by token:', face is not None)
