"""The eight probe scripts as string constants, one per Task 17 test file.

Each body reproduces the recipe recorded in `docs/probe-results.md` (measured
values, findings, error text) using the corrected API forms from
`skills/fusion-design/reference/api-recipes.md` (`sk.sketchCurves.sketchLines`,
not `sk.sketchLines`; `setOneSideExtent` + `DistanceExtentDefinition`, not the
stub-gapped `setDistanceExtent` -- see `docs/fusion-api-notes.md` section 8).

`probe-results.md` records measured *output*, not the exact script bodies for
every probe (P4, P5, P7, P8 in particular): those scripts are reconstructed
from the recipe docs and the shipped Autodesk stubs, then verified live
against this project's own Fusion install before being committed here. Where
the reconstruction is a plausible-but-not-guaranteed match for the original
probe's exact geometry (P8's hole layout), the test asserts the qualitative
finding the doc records, not a byte-for-byte transcription of its error text
-- see `docs/probe-results.md`'s "New finding -- a cut with zero body overlap
fails silently, not with P8's documented error" addendum for the one case
where the reconstruction surfaced a genuine doc-vs-live deviation, not just a
different geometry.

Every script prints exactly one `FH_RESULT {json}` line as its last output.
No script here catches exceptions except P3, whose entire point is
characterising exception text (documented at the try/except site, see R9 in
`docs/fusion-api-notes.md`).

Scripts are plain top-level Python (no `def run(_context):` wrapper): Task 16
measured that `fusion_mcp_execute` runs module-level code directly -- see
`tests/integration/scratch.py`'s templates and `test_smoke.py`, both of which
use this form successfully against the live endpoint.
"""

P1_PARAMETRIC = r"""
import adsk.core, adsk.fusion, json

app = adsk.core.Application.get()
des = adsk.fusion.Design.cast(app.activeProduct)
root = des.rootComponent

up = des.userParameters
up.add('plate_w', adsk.core.ValueInput.createByString('60 mm'), 'mm', 'plate width')
up.add('plate_d', adsk.core.ValueInput.createByString('40 mm'), 'mm', 'plate depth')
up.add('plate_t', adsk.core.ValueInput.createByString('5 mm'), 'mm', 'plate thickness')

sk = root.sketches.add(root.xYConstructionPlane)
lines = sk.sketchCurves.sketchLines
rect = lines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(6, 4, 0))

sk.geometricConstraints.addCoincident(rect.item(0).startSketchPoint, sk.originPoint)
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
w.parameter.expression = 'plate_w'

d = sk.sketchDimensions.addDistanceDimension(
    rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
    adsk.core.Point3D.create(7.5, 2, 0))
d.parameter.expression = 'plate_d'

prof = sk.profiles.item(0)
ext = root.features.extrudeFeatures
inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extent = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString('plate_t'))
inp.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
f = ext.add(inp)
f.name = 'plate_body'

body = f.bodies.item(0)
bb = body.boundingBox
before = (bb.maxPoint.x - bb.minPoint.x,
          bb.maxPoint.y - bb.minPoint.y,
          bb.maxPoint.z - bb.minPoint.z)

des.userParameters.itemByName('plate_w').expression = '80 mm'
des.userParameters.itemByName('plate_t').expression = '8 mm'
adsk.doEvents()

body2 = f.bodies.item(0)
bb2 = body2.boundingBox
after = (bb2.maxPoint.x - bb2.minPoint.x,
         bb2.maxPoint.y - bb2.minPoint.y,
         bb2.maxPoint.z - bb2.minPoint.z)

tl = des.timeline
unhealthy = 0
for i in range(tl.count):
    if tl.item(i).healthState != 0:
        unhealthy += 1

print('FH_RESULT ' + json.dumps({
    'before': before,
    'after': after,
    'unhealthy': unhealthy,
    'timeline_count': tl.count,
}))
"""

P2_ISFULLYCONSTRAINED = r"""
import adsk.core, adsk.fusion, json

app = adsk.core.Application.get()
des = adsk.fusion.Design.cast(app.activeProduct)
root = des.rootComponent

sk = root.sketches.add(root.xYConstructionPlane)
lines = sk.sketchCurves.sketchLines
rect = lines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(6, 4, 0))

sequence = [sk.isFullyConstrained]                                   # step0: rect drawn

sk.geometricConstraints.addCoincident(rect.item(0).startSketchPoint, sk.originPoint)
sequence.append(sk.isFullyConstrained)                                # step1: origin pinned

for ln in rect:
    dx = abs(ln.endSketchPoint.geometry.x - ln.startSketchPoint.geometry.x)
    dy = abs(ln.endSketchPoint.geometry.y - ln.startSketchPoint.geometry.y)
    if dx >= dy:
        sk.geometricConstraints.addHorizontal(ln)
    else:
        sk.geometricConstraints.addVertical(ln)
sequence.append(sk.isFullyConstrained)                                # step2: H/V applied

w = sk.sketchDimensions.addDistanceDimension(
    rect.item(0).startSketchPoint, rect.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
    adsk.core.Point3D.create(3, -1.5, 0))
w.parameter.expression = '60 mm'
sequence.append(sk.isFullyConstrained)                                # step3: width dim

d = sk.sketchDimensions.addDistanceDimension(
    rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
    adsk.core.Point3D.create(7.5, 2, 0))
d.parameter.expression = '40 mm'
sequence.append(sk.isFullyConstrained)                                # step4: depth dim

print('FH_RESULT ' + json.dumps({'sequence': sequence}))
"""

P3_OVERCONSTRAINT = r"""
import adsk.core, adsk.fusion, json

app = adsk.core.Application.get()
des = adsk.fusion.Design.cast(app.activeProduct)
root = des.rootComponent

sk = root.sketches.add(root.xYConstructionPlane)
lines = sk.sketchCurves.sketchLines
rect = lines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(6, 4, 0))

sk.geometricConstraints.addCoincident(rect.item(0).startSketchPoint, sk.originPoint)
h_lines = []
for ln in rect:
    dx = abs(ln.endSketchPoint.geometry.x - ln.startSketchPoint.geometry.x)
    dy = abs(ln.endSketchPoint.geometry.y - ln.startSketchPoint.geometry.y)
    if dx >= dy:
        sk.geometricConstraints.addHorizontal(ln)
        h_lines.append(ln)
    else:
        sk.geometricConstraints.addVertical(ln)

w = sk.sketchDimensions.addDistanceDimension(
    rect.item(0).startSketchPoint, rect.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
    adsk.core.Point3D.create(3, -1.5, 0))
w.parameter.expression = '60 mm'

d = sk.sketchDimensions.addDistanceDimension(
    rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
    adsk.core.Point3D.create(7.5, 2, 0))
d.parameter.expression = '40 mm'

# R9 exception, deliberate: this probe characterises Fusion's over-constraint
# error messages, so it must catch what it deliberately provokes to compare
# their text -- that IS the test. No other script in this suite catches
# exceptions (docs/fusion-api-notes.md "No try/except anywhere in this file").
messages = {}

try:
    sk.sketchDimensions.addDistanceDimension(
        rect.item(0).startSketchPoint, rect.item(0).endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(3, -2.5, 0))
    messages['redundant_dimension'] = None
except RuntimeError as e:
    messages['redundant_dimension'] = str(e)

try:
    sk.geometricConstraints.addHorizontal(h_lines[0])
    messages['redundant_constraint'] = None
except RuntimeError as e:
    messages['redundant_constraint'] = str(e)

try:
    sk.geometricConstraints.addVertical(h_lines[0])
    messages['conflicting_constraint'] = None
except RuntimeError as e:
    messages['conflicting_constraint'] = str(e)

tl = des.timeline
unhealthy = 0
for i in range(tl.count):
    if tl.item(i).healthState != 0:
        unhealthy += 1

print('FH_RESULT ' + json.dumps({
    'messages': messages,
    'fully_constrained_after': sk.isFullyConstrained,
    'sketch_health_state': sk.healthState,
    'unhealthy_timeline_features': unhealthy,
}))
"""

P4_DURABLE_REFERENCES = r"""
import adsk.core, adsk.fusion, json

app = adsk.core.Application.get()
des = adsk.fusion.Design.cast(app.activeProduct)
root = des.rootComponent

up = des.userParameters
up.add('blk_w', adsk.core.ValueInput.createByString('60 mm'), 'mm', 'block width')
up.add('blk_d', adsk.core.ValueInput.createByString('40 mm'), 'mm', 'block depth')
up.add('blk_h', adsk.core.ValueInput.createByString('25 mm'), 'mm', 'block height')

sk = root.sketches.add(root.xYConstructionPlane)
lines = sk.sketchCurves.sketchLines
rect = lines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(6, 4, 0))
sk.geometricConstraints.addCoincident(rect.item(0).startSketchPoint, sk.originPoint)
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
w.parameter.expression = 'blk_w'
d = sk.sketchDimensions.addDistanceDimension(
    rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
    adsk.core.Point3D.create(7.5, 2, 0))
d.parameter.expression = 'blk_d'

prof = sk.profiles.item(0)
ext = root.features.extrudeFeatures
inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extent = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString('blk_h'))
inp.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
f = ext.add(inp)
f.name = 'block_body'
body = root.bRepBodies.item(0)


def top_face(b, tol=1e-6):
    # Largest planar face whose normal points along +Z (api-recipes.md).
    best = None
    for face in b.faces:
        g = face.geometry
        if not isinstance(g, adsk.core.Plane):
            continue
        n = g.normal
        if n.z > 1 - tol and abs(n.x) < tol and abs(n.y) < tol:
            if best is None or face.area > best.area:
                best = face
    return best


def index_of(b, target_face):
    for i in range(b.faces.count):
        if b.faces.item(i) == target_face:
            return i
    return -1


def is_top(face_geom, tol=1e-6):
    return (isinstance(face_geom, adsk.core.Plane)
            and face_geom.normal.z > 1 - tol
            and abs(face_geom.normal.x) < tol
            and abs(face_geom.normal.y) < tol)


face_count_before = body.faces.count
top_before = top_face(body)
top_index_before = index_of(body, top_before)
top_token = top_before.entityToken           # capture BEFORE the rebuild

# Topological edit: chamfer one top edge, forcing face count 6 -> 7. A
# dimensional-only edit would leave every index stable (docs/probe-results.md
# P4); the chamfer is what breaks the index pick.
top_edge = None
for e in top_before.edges:
    top_edge = e
    break

edges_coll = adsk.core.ObjectCollection.create()
edges_coll.add(top_edge)
chamfers = root.features.chamferFeatures
ch_input = chamfers.createInput2()
ch_input.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
    edges_coll, adsk.core.ValueInput.createByString('2 mm'), True)
chamfers.add(ch_input)

body_after = root.bRepBodies.item(0)         # re-fetched: held BRepFace/body
                                              # references can die across a
                                              # rebuild (fusion-api-notes.md 6)
face_count_after = body_after.faces.count

index_face_after = body_after.faces.item(top_index_before)
index_face_still_top = is_top(index_face_after.geometry)

token_resolved = des.findEntityByToken(top_token)
token_face = token_resolved[0] if token_resolved else None
token_still_top = is_top(token_face.geometry) if token_face is not None else False

top_after = top_face(body_after)
top_index_after = index_of(body_after, top_after) if top_after else -1
predicate_found_new_index = (top_after is not None and top_index_after != top_index_before)

print('FH_RESULT ' + json.dumps({
    'face_count_before': face_count_before,
    'face_count_after': face_count_after,
    'top_index_before': top_index_before,
    'index_face_still_top_after': index_face_still_top,
    'entity_token_resolved': token_face is not None,
    'entity_token_still_top': token_still_top,
    'top_index_after': top_index_after,
    'predicate_found_new_index': predicate_found_new_index,
}))
"""

P5_DATUMS_VS_RAW = r"""
import adsk.core, adsk.fusion, json

app = adsk.core.Application.get()
des = adsk.fusion.Design.cast(app.activeProduct)
root = des.rootComponent

up = des.userParameters
up.add('plate_w', adsk.core.ValueInput.createByString('100 mm'), 'mm', 'plate width')
up.add('plate_d', adsk.core.ValueInput.createByString('60 mm'), 'mm', 'plate depth')
up.add('plate_t', adsk.core.ValueInput.createByString('10 mm'), 'mm', 'plate thickness')
up.add('brk_w', adsk.core.ValueInput.createByString('20 mm'), 'mm', 'bracket footprint')
up.add('brk_h', adsk.core.ValueInput.createByString('20 mm'), 'mm', 'bracket height')

# --- Plate ---
plate_sk = root.sketches.add(root.xYConstructionPlane)
plate_rect = plate_sk.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(10, 6, 0))
plate_sk.geometricConstraints.addCoincident(
    plate_rect.item(0).startSketchPoint, plate_sk.originPoint)
for ln in plate_rect:
    dx = abs(ln.endSketchPoint.geometry.x - ln.startSketchPoint.geometry.x)
    dy = abs(ln.endSketchPoint.geometry.y - ln.startSketchPoint.geometry.y)
    if dx >= dy:
        plate_sk.geometricConstraints.addHorizontal(ln)
    else:
        plate_sk.geometricConstraints.addVertical(ln)
pw = plate_sk.sketchDimensions.addDistanceDimension(
    plate_rect.item(0).startSketchPoint, plate_rect.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
    adsk.core.Point3D.create(5, -1, 0))
pw.parameter.expression = 'plate_w'
pd = plate_sk.sketchDimensions.addDistanceDimension(
    plate_rect.item(1).startSketchPoint, plate_rect.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
    adsk.core.Point3D.create(11, 3, 0))
pd.parameter.expression = 'plate_d'

plate_prof = plate_sk.profiles.item(0)
plate_ext_in = root.features.extrudeFeatures.createInput(
    plate_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
plate_ext_in.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('plate_t')),
    adsk.fusion.ExtentDirections.PositiveExtentDirection)
plate_feat = root.features.extrudeFeatures.add(plate_ext_in)
plate_feat.name = 'plate_body'

# --- BracketA: raw coordinates -- nothing bound to any plate parameter ---
planes = root.constructionPlanes
pinA = planes.createInput()
pinA.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(1.0))
planeA = planes.add(pinA)
planeA.name = 'bracketA_plane'

skA = root.sketches.add(planeA)
rectA = skA.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(8, 0, 0), adsk.core.Point3D.create(10, 2, 0))
# deliberately no constraints, no dimensions: the literal seed IS the geometry
# -- this is what an LLM produces naturally without the discipline layer.

profA = skA.profiles.item(0)
extInA = root.features.extrudeFeatures.createInput(
    profA, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInA.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(2.0)),
    adsk.fusion.ExtentDirections.PositiveExtentDirection)
featA = root.features.extrudeFeatures.add(extInA)
featA.name = 'bracketA_body'

# --- BracketB: named datum + parameter-bound dimensions, fully constrained ---
pinB = planes.createInput()
pinB.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByString('plate_t'))
planeB = planes.add(pinB)
planeB.name = 'bracketB_plane'

skB = root.sketches.add(planeB)
rectB = skB.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(8, 0, 0), adsk.core.Point3D.create(10, 2, 0))
for ln in rectB:
    dx = abs(ln.endSketchPoint.geometry.x - ln.startSketchPoint.geometry.x)
    dy = abs(ln.endSketchPoint.geometry.y - ln.startSketchPoint.geometry.y)
    if dx >= dy:
        skB.geometricConstraints.addHorizontal(ln)
    else:
        skB.geometricConstraints.addVertical(ln)

xdim = skB.sketchDimensions.addDistanceDimension(
    skB.originPoint, rectB.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
    adsk.core.Point3D.create(9, -1, 0))
xdim.parameter.expression = 'plate_w'

wdim = skB.sketchDimensions.addDistanceDimension(
    rectB.item(0).startSketchPoint, rectB.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
    adsk.core.Point3D.create(9, -2, 0))
wdim.parameter.expression = 'brk_w'

ydim = skB.sketchDimensions.addDistanceDimension(
    skB.originPoint, rectB.item(0).startSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
    adsk.core.Point3D.create(11, 1, 0))
ydim.parameter.expression = 'plate_d - brk_w'

ddim = skB.sketchDimensions.addDistanceDimension(
    rectB.item(1).startSketchPoint, rectB.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
    adsk.core.Point3D.create(12, 1, 0))
ddim.parameter.expression = 'brk_w'

profB = skB.profiles.item(0)
extInB = root.features.extrudeFeatures.createInput(
    profB, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInB.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('brk_h')),
    adsk.fusion.ExtentDirections.PositiveExtentDirection)
featB = root.features.extrudeFeatures.add(extInB)
featB.name = 'bracketB_body'

# --- the edit that exposes the difference ---
des.userParameters.itemByName('plate_w').expression = '140 mm'
des.userParameters.itemByName('plate_t').expression = '18 mm'
adsk.doEvents()

plate_body = plate_feat.bodies.item(0)       # re-fetched, not the pre-edit var
bodyA = featA.bodies.item(0)
bodyB = featB.bodies.item(0)

plate_bb = plate_body.boundingBox
a_bb = bodyA.boundingBox
b_bb = bodyB.boundingBox

plate_right_x = plate_bb.maxPoint.x
plate_top_z = plate_bb.maxPoint.z

a_offset_x = abs(plate_right_x - a_bb.maxPoint.x) * 10   # cm -> mm
a_offset_z = abs(plate_top_z - a_bb.minPoint.z) * 10
b_offset_x = abs(plate_right_x - b_bb.maxPoint.x) * 10
b_offset_z = abs(plate_top_z - b_bb.minPoint.z) * 10

tl = des.timeline
unhealthy = 0
for i in range(tl.count):
    if tl.item(i).healthState != 0:
        unhealthy += 1

print('FH_RESULT ' + json.dumps({
    'bracketA_offset_x_mm': a_offset_x,
    'bracketA_offset_z_mm': a_offset_z,
    'bracketB_offset_x_mm': b_offset_x,
    'bracketB_offset_z_mm': b_offset_z,
    'unhealthy': unhealthy,
    'timeline_count': tl.count,
}))
"""

P6_PARAMETER_TABLE = r"""
import adsk.core, adsk.fusion, json

app = adsk.core.Application.get()
des = adsk.fusion.Design.cast(app.activeProduct)
root = des.rootComponent

up = des.userParameters
up.add('hole_d', adsk.core.ValueInput.createByString('8 mm'), 'mm', 'hole diameter')

sk = root.sketches.add(root.xYConstructionPlane)
centers = [(1, 1), (5, 1), (1, 3), (5, 3)]
dims = []
for cx, cy in centers:
    circ = sk.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(cx, cy, 0), 0.4)
    dim = sk.sketchDimensions.addDiameterDimension(
        circ, adsk.core.Point3D.create(cx + 0.6, cy, 0))
    dim.parameter.expression = 'hole_d'
    dims.append(dim)

before_mm = [d.parameter.value * 10 for d in dims]   # cm -> mm

des.userParameters.itemByName('hole_d').expression = '13 mm'
adsk.doEvents()

after_mm = [d.parameter.value * 10 for d in dims]

print('FH_RESULT ' + json.dumps({'before_mm': before_mm, 'after_mm': after_mm}))
"""

P7_INTERFERENCE = r"""
import adsk.core, adsk.fusion, json

app = adsk.core.Application.get()
des = adsk.fusion.Design.cast(app.activeProduct)
root = des.rootComponent

# Same plate + raw-coordinate bracket as P5's BracketA: the interference is
# measured on the model P5 characterises as silently wrong (docs/probe-results.md
# "Run against the P5 model immediately after the parameter edit").
up = des.userParameters
up.add('plate_w', adsk.core.ValueInput.createByString('100 mm'), 'mm', 'plate width')
up.add('plate_d', adsk.core.ValueInput.createByString('60 mm'), 'mm', 'plate depth')
up.add('plate_t', adsk.core.ValueInput.createByString('10 mm'), 'mm', 'plate thickness')

plate_sk = root.sketches.add(root.xYConstructionPlane)
plate_rect = plate_sk.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(10, 6, 0))
plate_sk.geometricConstraints.addCoincident(
    plate_rect.item(0).startSketchPoint, plate_sk.originPoint)
for ln in plate_rect:
    dx = abs(ln.endSketchPoint.geometry.x - ln.startSketchPoint.geometry.x)
    dy = abs(ln.endSketchPoint.geometry.y - ln.startSketchPoint.geometry.y)
    if dx >= dy:
        plate_sk.geometricConstraints.addHorizontal(ln)
    else:
        plate_sk.geometricConstraints.addVertical(ln)
pw = plate_sk.sketchDimensions.addDistanceDimension(
    plate_rect.item(0).startSketchPoint, plate_rect.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
    adsk.core.Point3D.create(5, -1, 0))
pw.parameter.expression = 'plate_w'
pd = plate_sk.sketchDimensions.addDistanceDimension(
    plate_rect.item(1).startSketchPoint, plate_rect.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
    adsk.core.Point3D.create(11, 3, 0))
pd.parameter.expression = 'plate_d'

plate_prof = plate_sk.profiles.item(0)
plate_ext_in = root.features.extrudeFeatures.createInput(
    plate_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
plate_ext_in.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('plate_t')),
    adsk.fusion.ExtentDirections.PositiveExtentDirection)
plate_feat = root.features.extrudeFeatures.add(plate_ext_in)
plate_feat.name = 'plate_body'

planes = root.constructionPlanes
pinA = planes.createInput()
pinA.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(1.0))
planeA = planes.add(pinA)
planeA.name = 'bracketA_plane'

skA = root.sketches.add(planeA)
rectA = skA.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(8, 0, 0), adsk.core.Point3D.create(10, 2, 0))
profA = skA.profiles.item(0)
extInA = root.features.extrudeFeatures.createInput(
    profA, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInA.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(2.0)),
    adsk.fusion.ExtentDirections.PositiveExtentDirection)
featA = root.features.extrudeFeatures.add(extInA)
featA.name = 'bracketA_body'

des.userParameters.itemByName('plate_w').expression = '140 mm'
des.userParameters.itemByName('plate_t').expression = '18 mm'
adsk.doEvents()

coll = adsk.core.ObjectCollection.create()
for b in root.bRepBodies:
    coll.add(b)

result = {'count': 0, 'clashes': []}
if coll.count >= 2:
    ii = des.createInterferenceInput(coll)
    ii.areCoincidentFacesIncluded = False        # ESSENTIAL -- api-recipes.md
    res = des.analyzeInterference(ii)
    result['count'] = res.count
    for i in range(res.count):
        r = res.item(i)
        result['clashes'].append({
            'a': r.entityOne.name,
            'b': r.entityTwo.name,
            'volume_cm3': r.interferenceBody.volume,
        })

print('FH_RESULT ' + json.dumps(result))
"""

P8_PARAMETER_SWEEP = r"""
import adsk.core, adsk.fusion, json

app = adsk.core.Application.get()
des = adsk.fusion.Design.cast(app.activeProduct)
root = des.rootComponent

up = des.userParameters
up.add('plate_w', adsk.core.ValueInput.createByString('80 mm'), 'mm', 'plate width')
up.add('plate_d', adsk.core.ValueInput.createByString('50 mm'), 'mm', 'plate depth')
up.add('plate_t', adsk.core.ValueInput.createByString('5 mm'), 'mm', 'plate thickness')
up.add('hole_d', adsk.core.ValueInput.createByString('8 mm'), 'mm', 'hole diameter')

plate_sk = root.sketches.add(root.xYConstructionPlane)
plate_rect = plate_sk.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(8, 5, 0))
plate_sk.geometricConstraints.addCoincident(
    plate_rect.item(0).startSketchPoint, plate_sk.originPoint)
for ln in plate_rect:
    dx = abs(ln.endSketchPoint.geometry.x - ln.startSketchPoint.geometry.x)
    dy = abs(ln.endSketchPoint.geometry.y - ln.startSketchPoint.geometry.y)
    if dx >= dy:
        plate_sk.geometricConstraints.addHorizontal(ln)
    else:
        plate_sk.geometricConstraints.addVertical(ln)
pw = plate_sk.sketchDimensions.addDistanceDimension(
    plate_rect.item(0).startSketchPoint, plate_rect.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
    adsk.core.Point3D.create(4, -1, 0))
pw.parameter.expression = 'plate_w'
pd = plate_sk.sketchDimensions.addDistanceDimension(
    plate_rect.item(1).startSketchPoint, plate_rect.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
    adsk.core.Point3D.create(9, 2.5, 0))
pd.parameter.expression = 'plate_d'

plate_prof = plate_sk.profiles.item(0)
plate_ext_in = root.features.extrudeFeatures.createInput(
    plate_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
plate_ext_in.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('plate_t')),
    adsk.fusion.ExtentDirections.PositiveExtentDirection)
plate_feat = root.features.extrudeFeatures.add(plate_ext_in)
plate_feat.name = 'plate_body'


def top_face(b, tol=1e-6):
    best = None
    for face in b.faces:
        g = face.geometry
        if not isinstance(g, adsk.core.Plane):
            continue
        n = g.normal
        if n.z > 1 - tol and abs(n.x) < tol and abs(n.y) < tol:
            if best is None or face.area > best.area:
                best = face
    return best


plate_body = plate_feat.bodies.item(0)
top = top_face(plate_body)

# Two holes near the left edge (x=2cm), two near the right edge (x=6cm) of
# the nominal 8cm-wide plate. Positioned as sketch points on the plate's own
# top face (a raw construction plane produced "InternalValidationError:
# logicalSelection" from HoleFeatures.add -- the hole tool needs an actual
# target-body face, not just a coincident plane).
#
# Deliberately holeFeatures, not a sketch-circle + CutFeatureOperation
# extrude: the latter silently no-ops (no exception, no reference failure)
# when its profile has zero overlap with the target body, instead of
# raising the reference failure this probe documents. See
# docs/probe-results.md's "New finding -- a cut with zero body overlap
# fails silently, not with P8's documented error" (measured 2026-07-28).
hole_sk = root.sketches.add(top)
centers = [(2, 1.5), (2, 3.5), (6, 1.5), (6, 3.5)]
pts = adsk.core.ObjectCollection.create()
for cx, cy in centers:
    p = hole_sk.sketchPoints.add(adsk.core.Point3D.create(cx, cy, 0))
    pts.add(p)

hole_input = root.features.holeFeatures.createSimpleInput(
    adsk.core.ValueInput.createByString('hole_d'))
hole_input.setPositionBySketchPoints(pts)
hole_input.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
hole_feat = root.features.holeFeatures.add(hole_input)
hole_feat.name = 'HoleCuts'


def sweep_unhealthy():
    tl = des.timeline
    bad = []
    for i in range(tl.count):
        it = tl.item(i)
        if it.healthState != 0:
            bad.append({'name': it.name, 'state': it.healthState, 'msg': it.errorOrWarningMessage})
    return bad


configs = {}

p_hole_d = des.userParameters.itemByName('hole_d')
p_plate_t = des.userParameters.itemByName('plate_t')
p_plate_w = des.userParameters.itemByName('plate_w')

p_hole_d.expression = '30 mm'
adsk.doEvents()
configs['hole_d_30mm'] = sweep_unhealthy()
p_hole_d.expression = '8 mm'
adsk.doEvents()

p_hole_d.expression = '60 mm'
adsk.doEvents()
configs['hole_d_60mm'] = sweep_unhealthy()
p_hole_d.expression = '8 mm'
adsk.doEvents()

p_plate_t.expression = '0.4 mm'
adsk.doEvents()
configs['plate_t_0.4mm'] = sweep_unhealthy()
p_plate_t.expression = '5 mm'
adsk.doEvents()

p_plate_w.expression = '30 mm'
adsk.doEvents()
configs['plate_w_30mm'] = sweep_unhealthy()
p_plate_w.expression = '80 mm'
adsk.doEvents()

print('FH_RESULT ' + json.dumps(configs))
"""
