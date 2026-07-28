# Fusion API recipes

Verified working code, one construct per section. Read the section you need; do not read
the file end to end.

Everything here was executed against a live Fusion 360 install (API 2703.1.20) unless a
section is explicitly marked **Not directly probed**. Each recipe names the standing rule
it satisfies.

## Contents

- [Script skeleton](#script-skeleton)
- [Units](#units)
- [User parameters, including derived](#user-parameters-including-derived)
- [Binding a sketch dimension to a parameter](#binding-a-sketch-dimension-to-a-parameter)
- [Binding a feature extent to a parameter](#binding-a-feature-extent-to-a-parameter)
- [Fully-constrained rectangle, and the DOF arithmetic](#fully-constrained-rectangle-and-the-dof-arithmetic)
- [Naming the loose entities in an under-constrained sketch](#naming-the-loose-entities-in-an-under-constrained-sketch)
- [Chained lines for an arbitrary closed profile](#chained-lines-for-an-arbitrary-closed-profile)
- [Named construction plane at a parameter-bound offset](#named-construction-plane-at-a-parameter-bound-offset)
- [Deriving placement from the sketch plane at runtime](#deriving-placement-from-the-sketch-plane-at-runtime)
- [entityToken capture and round-trip](#entitytoken-capture-and-round-trip)
- [Selecting a face by geometric predicate](#selecting-a-face-by-geometric-predicate)
- [Interference](#interference)
- [Interference without touching the document](#interference-without-touching-the-document)
- [Minimum distance and mass properties](#minimum-distance-and-mass-properties)
- [Bounding box](#bounding-box)
- [Timeline health sweep](#timeline-health-sweep)
- [After a parameter change](#after-a-parameter-change)
- [Constraint and dimension vocabulary](#constraint-and-dimension-vocabulary)
- [Things that do not work](#things-that-do-not-work)

---

## Script skeleton

```python
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    # ... build ...
    print('done')
```

`fusion_mcp_execute` with `featureType: "script"` requires `def run(_context: str):`.
`print()` output comes back as the tool result; exceptions come back as the error message.

No `try` / `except` anywhere in this file (**R9**). Autodesk's own guidance: if you catch
exceptions you cannot determine that the script failed, where, or why. The traceback is
the diagnostic the repair loop runs on.

A design must already be open before the script runs.

## Units

**The API is always centimetres. The UI is whatever the user set.** A body measuring
7.52 API units displayed as 75.2 mm.

Never pass a raw float for a dimension. `createByString('60 mm')` parses the unit
explicitly and the question never arises (**R1**).

## User parameters, including derived

```python
up = des.userParameters
up.add('outer_w', adsk.core.ValueInput.createByString('60 mm'),      'mm', 'outer width')
up.add('outer_h', adsk.core.ValueInput.createByString('18 mm'),      'mm', 'outer height')
up.add('wall_t',  adsk.core.ValueInput.createByString('outer_h / 5'), 'mm', 'derived')
```

`createByString` stores the expression verbatim and it stays live: with `outer_h` at
10 mm, `wall_t` computed 0.20 cm; after `outer_h` → 18 mm it recomputed to 0.36 cm with no
intervention. `createByReal` bakes a literal instead (**R1**).

Names are multi-character `snake_case` (**R7**). `userParameters.add()` raises
`RuntimeError: 3 : param name is not valid` for unit symbols, function and constant names,
malformed names, **and for duplicates, with the same message**. Naming is case-sensitive.

Root parameters legitimately hold literals; everything downstream references them by name.
Four independent parameters each holding `"15 mm"` is the failure this rule prevents — one
design intent expressed four times, so editing one does not move the others.

## Binding a sketch dimension to a parameter

```python
dim = sk.sketchDimensions.addDistanceDimension(
    line.startSketchPoint, line.endSketchPoint,
    adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
    adsk.core.Point3D.create(3, -1.5, 0))
dim.parameter.expression = 'outer_w'          # <- the binding, on the very next line
```

The second line is the whole point (**R2**). Without it the dimension holds whatever value
the seed geometry happened to have, and the parameter it should follow does nothing.

The `Point3D` is only where the dimension annotation is drawn. It is not a dimension.

Expressions work, not just bare names: `'plate_d - brk_w'` was verified as a dimension
expression and stayed live across an edit.

## Binding a feature extent to a parameter

```python
ext = root.features.extrudeFeatures
inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extent = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString('plate_t'))
inp.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
f = ext.add(inp)
f.name = 'plate_body'
```

**`ExtrudeFeatureInput.setDistanceExtent` is a stub gap, not a hallucination.** The earlier
form of this recipe (`inp.setDistanceExtent(False, ValueInput...)`) ran live in Fusion
without error, and a live `hasattr()` probe against a real `ExtrudeFeatureInput` confirmed
the method genuinely exists at runtime (measured 2026-07-28). It is simply absent from the
shipped `.pyi` stub for that class — `adsk/fusion.py` (API 2703.1.20) declares
`setDistanceExtent` only on `HoleFeatureInput`/`HoleFeature`, not on `ExtrudeFeatureInput` —
so pyright's static gate false-positives on otherwise-correct code. This is the first
confirmed gate false positive found in this project; do not "fix" a `setDistanceExtent`
finding by assuming the call is wrong.

The recipe below uses `setOneSideExtent` plus a `DistanceExtentDefinition` instead — not
because `setDistanceExtent` is invalid, but because `setOneSideExtent` is **both**
runtime-valid **and** stub-visible, so it is gate-clean. Until the stub gap is closed
(or the gate is taught to tolerate it — a phase-2 question, since pyright findings are not
waivable through the lint suppression mechanism), prefer the form that satisfies both the
runtime and the gate over the one that only satisfies the runtime.

Binding the extent is necessary and **not sufficient** (**R2**). A profile drawn at literal
`Point3D` coordinates with only the extent bound produced *byte-identical* geometry when
the width parameter changed — identical volume to four decimal places, all 12 faces
unchanged. Both mechanisms are required: bound sketch dimensions **and** bound extents.

Extrude direction is clean: a positive distance always follows the plane normal.

## Fully-constrained rectangle, and the DOF arithmetic

The verified sequence. `isFullyConstrained` flips `False` → `True` on the last dimension.

`Sketch` has no `sketchLines` property, at runtime or in the stub — a live `hasattr()`
probe against a real `Sketch` returned `False` (measured 2026-07-28), and
`SketchCurves.sketchLines` returned `True`. Unlike the `setDistanceExtent` case above,
this is not a stub gap: the one-line-shorter form (`sk.sketchLines`) was a plain
transcription error in this doc, corrected below to the property that actually exists
(`sk.sketchCurves.sketchLines`).

```python
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

# 3. gate: dimensions only while this still reads False  (R3)
print('after constraints:', sk.isFullyConstrained)

# 4. two dimensions, each bound  (R2)
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

print('fully constrained:', sk.isFullyConstrained)   # True
```

Measured transitions:

```
step0 rect drawn:          fullyConstrained=False  geom=0  dims=0
step1 origin pinned:       fullyConstrained=False  geom=1
step2 H/V applied (2H,2V): fullyConstrained=False  geom=5
step3 width dim:           fullyConstrained=False  dims=1
step4 depth dim:           fullyConstrained=True   dims=2
```

**The DOF arithmetic, so this generalises.** Each unique sketch point carries 2 DOF.
A rectangle's corners are *shared* points — 8 endpoint slots resolve to 4 unique points
(`sketchPoints.count == 5` including the origin) — so 8 DOF, not 16. Coincident-to-origin
removes 2. Two horizontals and two verticals remove 4. Two distance dimensions remove 2.
Zero remain, and the flag flips on the last one.

For any profile: count unique points, double it, subtract what each constraint removes, and
expect the flag to flip exactly when you reach zero. If it flips early you have applied a
constraint you did not intend; if it never flips, something is loose — see the next recipe.

**`addTwoPointRectangle` creates zero geometric constraints.** Four independent lines that
merely look like a rectangle. The UI infers horizontal/vertical while you draw; the API
infers nothing. Every constraint is yours to add.

**On indexing `rect`:** this is a collection returned by the call that just created these
entities in this script, not solved body topology. **R4** forbids indexing `body.faces[n]`
and `body.edges[n]`, whose meaning changes when face count changes. It does not forbid
using the return value of the call you just made. The geometry test above is still
preferable because it does not depend on the collection's ordering.

**Over-constraint is fail-safe.** All three over-constraint cases raise *before* mutating;
after all three the sketch was still `isFullyConstrained=True`, `healthState=0`, zero
unhealthy timeline features. Attempt-and-recover is safe; predicting DOF perfectly in
advance is not required.

## Naming the loose entities in an under-constrained sketch

There is no degrees-of-freedom API — `isFullyConstrained` appears at exactly three sites
across 888 classes in `fusion.py` and 339 in `core.py`. But the per-entity flag exists:

```python
for i, ln in enumerate(sk.sketchCurves.sketchLines):
    if not ln.isFullyConstrained:
        print('loose entity', i)
```

Measured: `[False, False, False, False]` on a raw rectangle;
`[True, False, False, True]` after origin-coincident plus H/V, pinpointing entities 1 and 2.

A count is not actionable. Naming the entity is. The full version of this check lives in
the verification block — see `verification.md`.

## Chained lines for an arbitrary closed profile

**Not directly probed.** Documented in the API notes as a working tip; confirm the
resulting constraint count before relying on it.

```python
lines = sk.sketchCurves.sketchLines
l1 = lines.addByTwoPoints(p0, p1)
l2 = lines.addByTwoPoints(l1.endSketchPoint, p2)   # start = previous end -> auto-coincident
l3 = lines.addByTwoPoints(l2.endSketchPoint, p3)
l4 = lines.addByTwoPoints(l3.endSketchPoint, l1.startSketchPoint)   # closes the loop
```

Passing the previous line's `endSketchPoint` as the next line's start auto-creates the
coincident constraint, so explicit corner coincidents become unnecessary. The remaining
work is the same as the rectangle: geometric constraints, check the gate, then bound
dimensions (**R2**, **R3**).

Seed coordinates only need to be approximately right. A deliberately jittered,
non-axis-aligned profile seeded at `(0.1, −0.2) → (4.3, 0.15) → (4.1, 2.4) → (−0.2, 2.6)`
resolved after constraining to exactly `(0, 0) → (4, 0) → (4, 2.5) → (0, 2.5)`. The solver
does the placement; small arithmetic error in the seed is harmless.

## Named construction plane at a parameter-bound offset

```python
planes = root.constructionPlanes
pin = planes.createInput()
pin.setByOffset(root.xYConstructionPlane,
                adsk.core.ValueInput.createByString('plate_t'))   # R1
lid_plane = planes.add(pin)
lid_plane.name = 'lid_plane'                                      # Not directly probed
sk = root.sketches.add(lid_plane)
```

The offset binding is what was measured. A bracket placed on a plane offset by
`createByString('plate_t')`, with every dimension bound, stayed **0.0 mm** off both the
plate's right edge and its top face after `plate_w` 100→140 mm and `plate_t` 10→18 mm. The
same bracket built at literal coordinates ended 40 mm off the edge and 8 mm sunk into the
plate — with **zero errors reported** by Fusion.

Sketch on named construction planes the script creates, never on `body.faces[n]` (**R4**).

Assigning `.name` was not itself probed, but naming every feature and construction plane is
the generator rule that makes the timeline legible and the references stable.

## Deriving placement from the sketch plane at runtime

```python
m = sk.sketchToModelSpace()          # Matrix3D: sketch space -> world
```

Read the mapping from this at runtime and derive the placement from it (**R6**). Do not
hardcode a plane-to-axis table. See `axis-mapping.md` — but read it only when *diagnosing*
an inversion, never to compute a placement.

## entityToken capture and round-trip

```python
tok = face.entityToken                 # capture BEFORE the rebuild
# ... parameter change ...
adsk.doEvents()
found = des.findEntityByToken(tok)     # returns a collection; take the first
face = found[0] if found else None
```

Measured across two edit classes:

| Edit type | Index pick | `entityToken` | Geometric predicate |
|---|---|---|---|
| Dimensional (`w` 60→95 mm) | survives | survives | survives |
| **Topological (chamfer, faces 6 → 7)** | **breaks** | survives | survives |

A `BRepFace` held in a Python variable is dead after a rebuild:
`RuntimeError: 2 : InternalValidationError : asmFace`. The suffix varies (`asmFace` and
`pFace` both observed) — **match on `InternalValidationError`, not the suffix** (**R5**).

**Never string-compare tokens.** The string for a given entity can differ over time, and two
different strings can resolve to the same entity. Always round-trip through
`findEntityByToken`.

`BRepFace.tempId` is not durable — Autodesk: *"only good while the document remains open and
as long as the owning BRepBody is not modified in any way."*

**Not directly probed:** the exact return shape of `findEntityByToken`. The probe recorded
`found=True`, not the container type. Confirm with `fusion_mcp_read`,
`queryType: apiDocumentation` before depending on it.

## Selecting a face by geometric predicate

```python
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
```

The predicate survived both edit classes and correctly tracked the top face from index 4 to
index 5 after a chamfer. Over the same edit, `face[4]` went from area 38.0 / normal
`(0,0,1)` to area 9.955 / normal `(−1,0,0)` — a side face. A shell or fillet authored
against index 4 would have cut the wrong face, silently (**R4**).

The trigger is a **change in face count**, not parameter edits as such. Pure dimensional
edits left all six face indices stable. Risk is therefore proportional to how much a feature
changes face count — which is why fillets and chamfers go last and minimally.

Usable predicates, all read directly in the probes: normal direction, area, centroid, edge
length.

**Not directly probed:** the `f.geometry` / `adsk.core.Plane` accessor path above. The probe
printed each face's area and normal, so both are readable; the exact accessor is worth
confirming via `apiDocumentation`.

## Interference

```python
coll = adsk.core.ObjectCollection.create()
for b in root.bRepBodies:
    coll.add(b)

if coll.count < 2:
    print('interference: skipped, fewer than two bodies')      # guard: see below
else:
    ii = des.createInterferenceInput(coll)
    ii.areCoincidentFacesIncluded = False                      # ESSENTIAL
    res = des.analyzeInterference(ii)
    print('interference count:', res.count)
    for i in range(res.count):
        r = res.item(i)
        print('CLASH:', r.entityOne.name, 'vs', r.entityTwo.name,
              'volume=%.4f cm3' % r.interferenceBody.volume)
```

Verified: reported a 3.2 cm³ clash and attributed the pair correctly. A control measured
1.80000 cm³ against an analytic overlap of exactly 1.0 × 1.5 × 1.2 cm; a 3 cm gap correctly
returned count 0.

**`areCoincidentFacesIncluded = False` is essential.** Without it, a bracket correctly
seated on a plate reads as interference.

**Guard the call.** `createInterferenceInput` raises
`RuntimeError: 3 : invalid input collections` with fewer than two bodies.

This is the check that caught what the timeline was silent about. In the same model, with a
bracket 8 mm embedded in the plate, `timeline features=8 UNHEALTHY=0`.

`InterferenceResults.createBodies(...)` can materialise the overlap volumes as real bodies to
show the user *where* the clash is. It requires `DirectDesignType`; reading `.volume` does
not.

## Interference without touching the document

```python
tbm = adsk.fusion.TemporaryBRepManager.get()
a = tbm.copy(body_a)
b = tbm.copy(body_b)
tbm.booleanOperation(a, b, adsk.fusion.BooleanTypes.IntersectionBooleanType)
print('overlap volume:', a.volume)
```

Verified working. Operates on temporary bodies; the document is untouched and no
`ObjectCollection` is needed. Useful when you want an overlap number without any chance of
mutating the user's model.

## Minimum distance and mass properties

```python
print(app.measureManager.measureMinimumDistance(geom1, geom2).value)   # cm
print(app.measureManager.measureAngle(geom1, geom2).value)
```

Verified: 3.00000 cm for a separated pair, 0.00000 when overlapping. This is the clearance
oracle, checked against clearances declared in the declaration block.

```python
print(body.volume)                       # cm3, used throughout the probes
pp = body.physicalProperties             # .mass  .volume  .area  .centerOfMass
```

`body.volume` was read directly in the probes. The `physicalProperties` members are listed
in the API notes at Design, Component and body level but were **not individually probed**.

`getOrientedBoundingBox(geometry, lengthVector, widthVector)` also exists on
`measureManager`; **not directly probed**.

## Bounding box

```python
bb = body.boundingBox
print('bbox=(%.4f, %.4f, %.4f)' % (
    bb.maxPoint.x - bb.minPoint.x,
    bb.maxPoint.y - bb.minPoint.y,
    bb.maxPoint.z - bb.minPoint.z))
```

Bounding-box read-back is what every probe used to prove a rebuild was correct, e.g.
`before: bbox=(6.0000, 4.0000, 0.5000) vol=12.0000` → after a parameter edit
`bbox=(8.0000, 4.0000, 0.8000) vol=25.6000`, matching the expectation exactly.

## Timeline health sweep

```python
tl = des.timeline
unhealthy = 0
for i in range(tl.count):
    it = tl.item(i)
    if it.healthState != 0:                        # 0=Healthy 1=Warning 2=Error 3=Suppressed
        unhealthy += 1
        print('UNHEALTHY:', it.name, it.healthState, it.errorOrWarningMessage)
print('timeline features:', tl.count, 'unhealthy:', unhealthy)
```

Cheap and worth running, and it produces specific messages when it fires — a parameter sweep
that pushed a plate narrower than its hole pattern reported
`HoleCuts: "The extrusion profile falls outside the boundary of the selected body… 2
Reference Failures"`.

**But it is an incomplete oracle, and this matters more than the check does.** It reports
*reference* failures — geometry Fusion cannot construct — not geometry that is constructible
and wrong. Geometry 40 mm out of position and embedded in another body reported zero
unhealthy features. 60 mm holes on an 80 mm plate reported healthy. Never treat a healthy
timeline as a pass. See `limits.md`.

## After a parameter change

```python
p = des.userParameters.itemByName('plate_w')
p.expression = '80 mm'
adsk.doEvents()                  # let the rebuild complete before re-measuring
# ... re-measure bbox / volume ...
p.expression = '60 mm'           # restore
adsk.doEvents()
```

`adsk.doEvents()` is needed after a parameter change before re-measuring, and on long builds
generally — one report of 30 components / 200 bodies taking over 15 hours without it.

Perturbing each parameter and re-measuring is **the only check that catches the
partially-bound case**, where the model looks parametric and some dimensions silently do
nothing. The full check belongs to the verification block — see `verification.md`.

## Constraint and dimension vocabulary

`sketch.geometricConstraints` — 24 methods: `addCoincident`, `addCollinear`, `addConcentric`,
`addEqual`, `addHorizontal`, `addHorizontalPoints`, `addVertical`, `addVerticalPoints`,
`addMidPoint`, `addParallel`, `addPerpendicular`, `addSymmetry`, `addTangent`, `addSmooth`,
`addOffset2`, `addTwoSidesOffset`, `addPolygon`, `addCircularPattern`,
`addRectangularPattern`, `addCoincidentToSurface`, `addLineOnPlanarSurface`,
`addLineParallelToPlanarSurface`, `addPerpendicularToSurface`.

`sketch.sketchDimensions` — 12 methods: `addDistanceDimension`, `addAngularDimension`,
`addRadialDimension`, `addDiameterDimension`, `addOffsetDimension`,
`addConcentricCircleDimension`, `addEllipseMajorRadiusDimension`,
`addEllipseMinorRadiusDimension`, `addLinearDiameterDimension`,
`addTangentDistanceDimension`, `addDistanceBetweenLineAndPlanarSurfaceDimension`,
`addDistanceBetweenPointAndSurfaceDimension`.

`addCoincident()` returns `null` on failure rather than raising.

Constraints work only **within** a single sketch. Cross-sketch relationships need
`sketch.project2()` (`project` is retired) or `include()`. **Not directly probed.**

## Things that do not work

- **`geometricConstraints.addFixed` does not exist.** It is plausible-looking and the
  pre-flight catches it. Check unfamiliar calls against `fusion_mcp_read`,
  `queryType: apiDocumentation` before writing them.
- **There is no "declare constraints and let Fusion place the geometry" entry point.**
  Geometry must be created at seed coordinates first, then constrained. The seed is
  approximate; the constraints are authoritative.
- **Custom Features are effectively off-limits.** Autodesk: *"This re-compute functionality
  is currently limited to one specific case… should not be used for any other cases and will
  likely fail."* Emit plain native features.
- **`isComputeDeferred = True`** speeds bulk creation but Autodesk warns it *"can result in
  the creation of a bad model"* on sketches already consumed by features. Fresh sketches
  only. **Not directly probed.**
- **Large sketches freeze the UI** — duplicate entities and stacked patterns or mirrors in
  one sketch are the named causes. Prefer several small sketches to one huge one.
- **STEP import arrives as a `BaseFeature`** — a non-parametric island whose content never
  changes on recompute. Enabling history afterwards does not parameterise it. STEP is an
  output format, not a handoff format.
- One unreproducible `RuntimeError: 3 : invalid expression` occurred in a document polluted
  with roughly 21 accumulated probe parameters and did not recur in a clean document. Cause
  unidentified. Practical guard: distinct `snake_case` names, and do not accumulate junk
  parameters (**R7**).
