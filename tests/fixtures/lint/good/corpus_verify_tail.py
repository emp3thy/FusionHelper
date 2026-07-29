import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    up = des.userParameters
    up.add('tail_w', adsk.core.ValueInput.createByString('60 mm'), 'mm', 'outer width')
    up.add('tail_d', adsk.core.ValueInput.createByString('40 mm'), 'mm', 'outer depth')
    up.add('tail_t', adsk.core.ValueInput.createByString('5 mm'), 'mm', 'plate thickness')

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
    w.parameter.expression = 'tail_w'

    d = sk.sketchDimensions.addDistanceDimension(
        rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(7.5, 2, 0))
    d.parameter.expression = 'tail_d'

    prof = sk.profiles.item(0)
    ext = root.features.extrudeFeatures
    inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('tail_t'))
    inp.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
    f = ext.add(inp)
    f.name = 'tail_body'
    print('done')


# fusionhelper: verification stub v1
def _fh_verify_entry():
    import os, json, traceback
    home = os.environ.get('FUSIONHELPER_HOME') or os.path.join(
        os.environ.get('LOCALAPPDATA', ''), 'FusionHelper')

    def _bail(code, msg):
        return 'FH_VERDICT1 ' + json.dumps(
            {'v': 1, 'status': 'error', 'code': code, 'msg': msg, 'home': home},
            separators=(',', ':'))

    try:
        with open(os.path.join(home, 'fh_verify.py'), encoding='utf-8') as f:
            src = f.read()
    except Exception as e:
        return _bail('verify.block_missing', str(e))
    ns: dict = {'__name__': 'fh_verify'}   # annotated: else pyright infers dict[str, str]
    try:
        exec(compile(src, 'fh_verify.py', 'exec'), ns)
        g = globals()
        return ns['fh_verify'](
            clearances=g.get('CLEARANCES'),
            face_specs=g.get('FACE_SPECS'),
            datum_heights_cm=g.get('DATUM_HEIGHTS_CM'),
            digest=g.get('DIGEST'),
            interference_allowed=g.get('INTERFERENCE_ALLOWED'),
            expect_dead=g.get('EXPECT_DEAD'),
            refs=g.get('FH_REFS', {}),
            attempt=g.get('FH_ATTEMPT', 1),
            **g.get('FH_OPTS', {}))
    except Exception:
        return _bail('verify.internal', traceback.format_exc()[-600:])


def _fh_wrap(inner):
    def _wrapped(_context: str):
        inner(_context)                 # NOT wrapped: build exceptions must escape
        print(_fh_verify_entry())
    return _wrapped


run = _fh_wrap(run)
