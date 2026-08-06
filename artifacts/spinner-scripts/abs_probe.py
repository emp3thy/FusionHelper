"""Probe: does Fusion accept abs() in a dimension expression, and does it
fix the bound_rect2 centre-0 displacement? Read-only scratch sketch."""
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    pt = adsk.core.Point3D.create
    dims_or = adsk.fusion.DimensionOrientations

    sk = root.sketches.add(root.xYConstructionPlane)
    sk.name = "abs_probe_scratch"
    lines = sk.sketchCurves.sketchLines.addTwoPointRectangle(
        pt(-0.965, 1.5, 0), pt(0.965, 3.3, 0))
    gc = sk.geometricConstraints
    h_line = v_line = None
    for k in range(lines.count):
        ln = lines.item(k)
        s, e = ln.startSketchPoint.geometry, ln.endSketchPoint.geometry
        if abs(e.x - s.x) >= abs(e.y - s.y):
            gc.addHorizontal(ln)
            if h_line is None:
                h_line = ln
        else:
            gc.addVertical(ln)
            if v_line is None:
                v_line = ln
    if h_line is None or v_line is None:
        raise RuntimeError("rect missing axis-aligned line")
    corner = lines.item(0).startSketchPoint
    anchor = pt(2.5, -1.5, 0)
    d = sk.sketchDimensions.addDistanceDimension(
        h_line.startSketchPoint, h_line.endSketchPoint,
        dims_or.HorizontalDimensionOrientation, anchor)
    d.parameter.expression = "19.3 mm"
    d = sk.sketchDimensions.addDistanceDimension(
        v_line.startSketchPoint, v_line.endSketchPoint,
        dims_or.VerticalDimensionOrientation, anchor)
    d.parameter.expression = "18 mm"

    dh = sk.sketchDimensions.addDistanceDimension(
        sk.originPoint, corner, dims_or.HorizontalDimensionOrientation,
        anchor)
    dh.parameter.expression = "abs( 0 mm - (9.65 mm) )"
    print("abs() accepted, value = %.4f cm" % dh.parameter.value)
    dv = sk.sketchDimensions.addDistanceDimension(
        sk.originPoint, corner, dims_or.VerticalDimensionOrientation,
        anchor)
    dv.parameter.expression = "abs( 24 mm - (9 mm) )"

    xs = [lines.item(k).startSketchPoint.geometry.x
          for k in range(lines.count)]
    ys = [lines.item(k).startSketchPoint.geometry.y
          for k in range(lines.count)]
    print("rect x span: %.3f .. %.3f  (want -0.965 .. 0.965)"
          % (min(xs), max(xs)))
    print("rect y span: %.3f .. %.3f  (want 1.500 .. 3.300)"
          % (min(ys), max(ys)))
