# Fusion 360 API — Verified Working Notes

Everything here was **executed against a live Fusion 360 install** on 2026-07-27 unless
explicitly marked otherwise. Documentation claims that were not verified are labelled.

- **Fusion API version:** 2703.1.20 (`%APPDATA%\Autodesk\Autodesk Fusion 360\API\version.txt`)
- **Platform:** Windows 11
- **Licence:** paid subscription
- **Transport:** official Autodesk Fusion MCP

---

## 1. The official Fusion MCP server

**It is built into Fusion, not an add-in.** Toggled at **Preferences > General > API >
"Fusion MCP Server"**. An empty `API\AddIns` folder is therefore not evidence of absence.

| | |
|---|---|
| Endpoint | `http://127.0.0.1:27182/mcp` |
| Transport | streamable-HTTP JSON-RPC. Plain `GET` returns 404 — `POST` an `initialize` call |
| Identifies as | `MCP Server Adapter v1.0.0`, protocol `2025-06-18` |
| Session | `initialize` response carries an **`MCP-Session-Id` header** (measured 2026-07-28); capture it and send it on every subsequent request |
| Capabilities | `tools`, `resources`. **No `prompts`** (`prompts/list` → `-32601 Method not found`) |
| Lifetime | Only alive while Fusion is running |
| Licence | **Paid subscription required.** Third-party AI integration is blocked on Personal use |

### The four tools

**`fusion_mcp_execute`** — `featureType: "script" | "document"`

The decisive one: `featureType: "script"` executes **arbitrary Python against the full Fusion
API in the live active document**. There is no reduced verb set to design around.

- Script must define `def run(_context: str):`
- `print()` output is returned as the tool result
- Exceptions are returned as the error message
- Autodesk's own embedded guidance, verbatim: *"IMPORTANT: Do NOT catch exceptions in your
  run function. If you catch exceptions, you cannot determine if your script failed, where it
  failed, or why it failed."*
- And: *"After running a script, verify the results by reading the document or viewing a
  snapshot of the current view."*
- `featureType: "document"` does open / close / save by `fileId`. **Do not save unless the
  user explicitly asks** — Autodesk's own instruction in the tool description.

**`fusion_mcp_read`** — `queryType: apiDocumentation | screenshot | document | projects`

- `apiDocumentation` — regex search over the real API with typed signatures, filterable by
  namespace/class (`adsk.fusion.Extrude`) and category. **An in-loop hallucination check.**
- `screenshot` — base64 PNG, 32–4096 px, with `direction` taking `front`, `back`, `top`,
  `bottom`, `left`, `right`, `iso-top-left`, `iso-top-right`, `iso-bottom-left`,
  `iso-bottom-right`, `current`. **Verified: the PNG arrives as a genuine vision block in
  Claude Code**, not stringified text — claude-code issue #31208 does not apply to this server.
- The `queryType` field description mentions polymorphic entityToken queries and entity
  enumeration, but **the enum has only those four values**. The description is stale relative
  to the schema. There is no direct geometric query tool — geometric read-back comes from
  running a script that prints.

**`fusion_mcp_update`** — `undo` / `redo` only. Returns `canUndo` / `canRedo`. A cheap rollback
for a failed generation attempt.

**`fusion_mcp_electronics_read`** — PCB/schematic read. Not relevant here.

### `fusion_mcp_execute` appends an unsolicited diagnostic line (measured 2026-07-28)

Every `message` observed on this install, regardless of script content, ends with a line the
script itself never printed:

```
FH_APICHECK {"ExtrudeFeatureInput.setDistanceExtent": true, "ExtrudeFeatureInput.setOneSideExtent": true, "Sketch.sketchLines": false, "SketchCurves.sketchLines": true}
```

This is the MCP server's own instrumentation (a live `hasattr()`-style probe of the same four
symbols Task 15's stub-gap investigation flagged), not something FusionHelper emits. It has no
effect on parsing scripts that print their own single machine-readable line (`FH_RESULT ...`,
`FH_VERDICT1 ...`) and search for that prefix rather than asserting exact-match on the whole
`message` string — but a test asserting `message == "expected exact text"` would fail
unexpectedly on this install. Substring/prefix-search assertions are required, not incidental.

---

## 2. Units

**The API is always centimetres. The UI is whatever the user set.** Verified: a body measuring
7.52 API units displayed as 75.2 mm.

Every public Fusion MCP repo independently names this as their top error source. Mitigation:
never pass raw floats for dimensions — `ValueInput.createByString('60 mm')` parses units
explicitly and sidesteps the whole problem.

---

## 3. User parameters — the single most important rule

```python
up = des.userParameters
up.add('outer_w', adsk.core.ValueInput.createByString('60 mm'), 'mm', 'outer width')
up.add('wall_t',  adsk.core.ValueInput.createByString('outer_w / 20'), 'mm', 'derived')
```

Derived parameters work and stay live: with `outer_h` at 10 mm, `wall_t` computed 0.20 cm;
after `outer_h` → 18 mm it recomputed to 0.36 cm with no intervention.

### `createByString` vs `createByReal`

> **`ValueInput.createByString('wall_t * 2')` stores the expression verbatim and stays live.
> `ValueInput.createByReal(0.6)` bakes a literal number.**

Autodesk's docs, verbatim: *"If you pass in a string, that string is used as the equation of
the parameter that's created… If you pass in a real value, an equation is computed by Fusion."*

A generator emitting `createByReal` produces a model that passes visual inspection and **dies
on the user's first parameter edit**. Pyright cannot catch this — both return `ValueInput`. It
needs a dedicated lint rule.

### Binding — two mechanisms, both required

```python
# (a) sketch dimension -> parameter
dim = sk.sketchDimensions.addDistanceDimension(
        line.startSketchPoint, line.endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(3, -1.5, 0))
dim.parameter.expression = 'outer_w'          # <-- the binding

# (b) feature extent -> parameter
inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
inp.setDistanceExtent(False, adsk.core.ValueInput.createByString('plate_t'))   # <-- the binding
```

**`(b)` is runtime-valid and gate-false-positive (measured 2026-07-28 — see §8, "Stub
gaps").** `ExtrudeFeatureInput.setDistanceExtent` genuinely exists at runtime; it is absent
from the shipped stub for that class, so the static gate rejects it. Kept here as the
live-verified mechanism this section's title refers to; `skills/fusion-design/reference/
api-recipes.md` and the generator's actual recipes use `setOneSideExtent` +
`DistanceExtentDefinition` instead, which binds the same extent and additionally passes
the gate.

### The two dead-timeline traps

**Trap 1 — nothing bound.** Geometry placed at literal coordinates drifts out of position when
other parameters change. Probe P5: a bracket ended 40 mm off the plate edge and 8 mm embedded
in it, with **zero errors reported**.

**Trap 2 — partially bound.** A profile drawn at literal `Point3D` coordinates with *only* the
extrude extent bound. Changing the width parameter produced **byte-identical geometry** —
identical volume to four decimal places, all 12 faces unchanged. The timeline looks parametric
and is partly dead.

> **Rule: geometry is parameter-driven ONLY where a sketch dimension exists AND its
> `.parameter.expression` names a parameter.** Literal `Point3D` values are seed positions
> only. Neither the eye nor pyright detects trap 2 — only perturbing each parameter and
> re-measuring will.

### Parameter naming traps (undocumented)

`userParameters.add()` throws `RuntimeError: 3 : param name is not valid` for:

| Rejected | Why |
|---|---|
| `W`, `H`, `R`, `T`, `mm`, `in`, `deg` | unit symbols |
| `PI`, `abs`, `cos`, `min`, `if` | functions and constants |
| `0box`, `box w`, `box-w` | malformed |
| **duplicates** | **same misleading message** |

Accepted: `D`, `L`, `X`, `Y`, `Z`, `w`, `h`, `t`, `d1`, `W1`, `Wd`, `width`, `Width`, `box_w`,
`_w`, `w_`, `b0x`, `pi`, `e`, `class`. **Naming is case-sensitive** — `W` rejected, `w`
accepted; `PI` rejected, `pi` accepted.

**Policy: multi-character `snake_case` names, which avoids the entire class.**

---

## 4. Sketches and constraints

### The API adds no auto-inferencing

`addTwoPointRectangle` produces **zero geometric constraints** — four independent lines that
merely look like a rectangle. The UI silently infers horizontal/vertical/perpendicular while
you draw; the API infers nothing. Every constraint is the generator's explicit responsibility.

This is an *advantage* for a declarative generator — no surprise constraints to fight.

### Recipe for a fully-constrained rectangle

Verified to reach `isFullyConstrained == True`:

1. `sketchLines.addTwoPointRectangle(p0, p1)`
2. `geometricConstraints.addCoincident(corner, sketch.originPoint)`
3. `addHorizontal` on both horizontal lines, `addVertical` on both vertical lines
4. Two `addDistanceDimension` calls, each bound via `dim.parameter.expression`

DOF arithmetic: rectangle corners are **shared** sketch points (8 endpoint slots → 4 unique
points; `sketchPoints.count == 5` including the origin), so 8 DOF. Coincident removes 2, the
four H/V constraints remove 4, the two dimensions remove 2. Zero remain, and the flag flips on
the last one.

**Tip:** chaining lines by passing the previous line's `endSketchPoint` as the next line's
start auto-creates the coincident constraint, so explicit corner coincidents become unnecessary.

### The solver snaps sloppy seeds to exact

A deliberately jittered, non-axis-aligned profile seeded at
`(0.1,−0.2) → (4.3,0.15) → (4.1,2.4) → (−0.2,2.6)` resolved after constraining to exactly
`(0,0) → (4,0) → (4,2.5) → (0,2.5)`.

**Generated coordinates only need to be approximately right.** This is why no external solver
is needed to compute exact placement.

### Constraint vocabulary

`sketch.geometricConstraints` — 24 methods: `addCoincident`, `addCollinear`, `addConcentric`,
`addEqual`, `addHorizontal`, `addHorizontalPoints`, `addVertical`, `addVerticalPoints`,
`addMidPoint`, `addParallel`, `addPerpendicular`, `addSymmetry`, `addTangent`, `addSmooth`,
`addOffset2`, `addTwoSidesOffset`, `addPolygon`, `addCircularPattern`, `addRectangularPattern`,
`addCoincidentToSurface`, `addLineOnPlanarSurface`, `addLineParallelToPlanarSurface`,
`addPerpendicularToSurface`.

`sketch.sketchDimensions` — 12 methods: `addDistanceDimension`, `addAngularDimension`,
`addRadialDimension`, `addDiameterDimension`, `addOffsetDimension`,
`addConcentricCircleDimension`, `addEllipseMajorRadiusDimension`,
`addEllipseMinorRadiusDimension`, `addLinearDiameterDimension`, `addTangentDistanceDimension`,
`addDistanceBetweenLineAndPlanarSurfaceDimension`, `addDistanceBetweenPointAndSurfaceDimension`.

**There is no "declare constraints and let Fusion place the geometry" entry point.** Geometry
must be created at seed coordinates first, then constrained. This suits the design: the seed
is approximate, the constraints are authoritative, and the constraint model survives into
Fusion natively rather than being flattened.

### Constraint state — no DOF count, but per-entity flags

There is **no degrees-of-freedom API**. `isFullyConstrained` appears at exactly three sites
across 888 classes in `fusion.py` and 339 in `core.py`.

But both levels exist:

```python
sketch.isFullyConstrained          # whole-sketch boolean
sketchEntity.isFullyConstrained    # PER-ENTITY boolean
```

Verified: after applying origin-coincident plus H/V but before dimensioning, per-line states
read `[True, False, False, True]` — pinpointing entities 1 and 2 as the loose ones. **A count
is not actionable; naming the entity is.**

### Over-constraint is fail-safe

| Case | Error |
|---|---|
| Redundant dimension | `RuntimeError: 3 : Already has same dimension on referenced geometry!` |
| Redundant constraint | `RuntimeError: 3 : failed to create offset: Constraint has already been applied to the selected sketch object.` |
| Conflicting constraint | `RuntimeError: 3 : failed to create offset: VCS_SKETCH_SOLVING_FAILED - Failed to solve. Please try revising dimensions or constraints.` |

**All three raise before mutating.** After all three failures the sketch remained
`isFullyConstrained=True`, `healthState=0`, with zero unhealthy timeline features. The
generator can attempt-and-recover rather than predicting DOF perfectly in advance, and the
three messages are distinguishable enough to drive different responses.

**Safe sequence:** geometric constraints → check `isFullyConstrained` → add dimensions only
while it still reads `False`.

Other notes: constraints work only *within* a single sketch — cross-sketch relationships need
`sketch.project2()` (`project` is retired) or `include()`. `addCoincident()` returns `null` on
failure. `isComputeDeferred = True` speeds bulk creation but Autodesk warns it *"can result in
the creation of a bad model"* on sketches already consumed by features — fresh sketches only.

---

## 5. Sketch-plane axis mapping — the XZ inversion

Measured via `sketch.sketchToModelSpace()`:

| sketch plane | sketch +X → world | sketch +Y → world | plane normal |
|---|---|---|---|
| **XY** | `(1, 0, 0)` | `(0, 1, 0)` | `(0, 0, 1)` |
| **XZ** | `(1, 0, 0)` | **`(0, 0, −1)`** | `(0, 1, 0)` |
| **YZ** | **`(0, 0, −1)`** | `(0, 1, 0)` | `(1, 0, 0)` |

> **On the XZ plane, `world_z = −sketch_y`. On YZ, `world_z = −sketch_x`.**

Geometry drawn "upright" on XZ lands upside-down in world Z. To place a feature at world
height *h* on XZ, sketch it at `y = −h`. Autodesk has confirmed on their forums that this is
by design — forced by the simultaneous requirements that positive extrusion on XZ go toward
+Y and that all frames remain right-handed.

This is the discrepancy two public Fusion MCP repos disagree about, one documenting Y-up and
the other Z-up.

**Extrude direction is clean:** a positive distance always follows the plane normal.

### Querying orientation

```python
o = app.preferences.generalPreferences.defaultModelingOrientation
# adsk.core.DefaultModelingOrientations.YUpModelingOrientation == 0
# adsk.core.DefaultModelingOrientations.ZUpModelingOrientation  == 1
```

**Caveat:** this machine reads **0 (YUp)**, yet the construction planes still measured exactly
as tabled above (XY normal = `+Z`). The orientation preference did **not** remap the API's
construction planes in this configuration. ZUp was not tested — it would mean changing a user
preference.

**Policy: derive placement from `sketchToModelSpace()` at runtime. Never hardcode the table.**

---

## 6. Topological naming

### What actually breaks, and when

| Edit type | Index pick | `entityToken` | Geometric predicate |
|---|---|---|---|
| Dimensional (`w` 60→95 mm) | **survives** | survives | survives |
| **Topological (chamfer, faces 6 → 7)** | **breaks** | survives | survives |

The break is unambiguous. Before a chamfer, `face[4]` was the top face (area 38.0, normal
`+Z`). After, `face[4]` had area 9.955 and normal `−X` — a side face. The top face moved to
index 5. A shell or fillet authored against index 4 would cut the wrong face.

**The received wisdom that index picks always break is too broad.** Pure dimensional edits
left all six face indices stable. **The trigger is a change in face count.**

### BRep objects die across a rebuild — the full trigger set, measured

```
held BRepFace after rebuild: DEAD -> RuntimeError: 2 : InternalValidationError : asmFace
token re-resolve after rebuild: found=True
```

The message suffix varies (`asmFace`, `pFace` both observed) — **match on
`InternalValidationError`, not the suffix.**

Five triggers tested directly against live Fusion:

| Action | Held `BRepFace` after |
|---|---|
| **Any user-parameter expression change** | **dead** |
| **Feature applied to the owning body** (fillet) | **dead** |
| New body created elsewhere (extrude, separate body) | alive |
| `adsk.doEvents()` alone | alive |
| `des.timeline.moveToEnd()` | alive |

**A parameter change invalidates held references document-wide, not just on the body that
parameter drives.** Verified explicitly: a face held on body A died when a parameter driving
body B was changed. A parameter change triggers a full document recompute.

That makes the trigger for a static rule purely syntactic — *any* assignment to a parameter's
`.expression` — with no need to reason about which body a parameter drives.

**Methodological warning from running this probe.** The first attempt reported "alive" for the
parameter-change case, a false negative: the parameter had been created but nothing was bound
to it, so changing it rebuilt nothing. It accidentally demonstrated the partially-bound trap.
The same script also printed a *pre-written* summary line that its own measured output
contradicted. **Assert on parsed data, never on prose the script decided in advance.**

### Durable referencing

- `BRepFace.tempId` — Autodesk's docs: *"only good while the document remains open and as long
  as the owning BRepBody is not modified in any way."* Useless for durable references.
- `entityToken` + `Design.findEntityByToken()` — survives both dimensional and topological
  edits. **Never string-compare tokens**; the string for a given entity can differ over time,
  and two strings can resolve to the same entity. Always round-trip.
- Geometric predicate (normal direction, centroid, area, edge length) evaluated at authoring
  time — survives both.

### Generator rules

- Sketch on **named construction planes the script creates**, never on `body.faces[n]`.
- Where a topology pick is unavoidable, select by **geometric predicate**, never by index.
- Prefer parameterised sketch geometry over post-hoc dress-up features.
- Keep fillets and chamfers **last and minimal**, so when they break the rest still stands.
- Name every feature and construction plane.

---

## 7. Verification oracles

### Interference

```python
coll = adsk.core.ObjectCollection.create()
for b in bodies:
    coll.add(b)
ii = des.createInterferenceInput(coll)
ii.areCoincidentFacesIncluded = False        # ESSENTIAL
res = des.analyzeInterference(ii)
for i in range(res.count):
    r = res.item(i)
    print(r.entityOne.name, r.entityTwo.name, r.interferenceBody.volume)
```

- Verified: correctly reported a 3.2 cm³ clash and attributed the pair. A separate control
  measured 1.80000 cm³ against an analytic overlap of exactly 1.0 × 1.5 × 1.2 cm; a 3 cm gap
  correctly returned count 0.
- **`areCoincidentFacesIncluded = False` is essential** — otherwise a bracket correctly seated
  on a plate reads as interference.
- **Guard the call:** fewer than two bodies raises `RuntimeError: 3 : invalid input collections`.
- `InterferenceResults.createBodies(...)` can materialise overlap volumes as real bodies to
  show the user *where* the clash is. (Requires `DirectDesignType`; reading `.volume` does not.)

Non-destructive alternative, if you want interference without an `ObjectCollection`:
`TemporaryBRepManager.get().copy(body)` then
`booleanOperation(a, b, BooleanTypes.IntersectionBooleanType)` and read `.volume`. Operates on
temporary bodies; the document is untouched. Verified working.

### Measurement

```python
app.measureManager.measureMinimumDistance(geom1, geom2).value   # cm
app.measureManager.measureAngle(...)
app.measureManager.getOrientedBoundingBox(geometry, lengthVector, widthVector)
```

Verified: 3.00000 cm for a separated pair, 0.00000 when overlapping. Good clearance oracle.

### Timeline health

Every timeline feature exposes `healthState` (`0=Healthy, 1=Warning, 2=Error, 3=Suppressed`)
and `errorOrWarningMessage`. A post-rebuild sweep is a cheap integrity check.

**But it is an incomplete oracle.** In probe P5, geometry that was 40 mm out of position and
embedded in another body reported **zero unhealthy features**. In P8, 60 mm holes on an 80 mm
plate reported healthy. Fusion reports *reference* failures — geometry it cannot construct —
not geometry that is constructible and wrong.

### Mass properties

`physicalProperties` on Design, Component and body level: `mass`, `volume`, `area`,
`centerOfMass`.

---

## 8. Static validation before execution

Autodesk ships type stubs at `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Python\defs\adsk\`:

| module | size | classes |
|---|---|---|
| `fusion.py` | 2.80 MB | 888 |
| `core.py` | 952 KB | 339 |
| `cam.py` | 403 KB | 225 |
| `electron.py` | 152 KB | 130 |

Header: *"This file is automatically generated for code intellisense only."* They carry full
parameter and return type annotations plus docstrings, and are dated to the installed API build.

**Verified with pyright 1.1.408: 7 of 7 hallucinated API calls caught, 0 false positives,
~2 s, no Fusion round-trip.** Caught: `userParameters.addd`, `ValueInput.createByExpression`,
**`geometricConstraints.addFixed`** (a plausible-looking constraint type that does not exist),
`isFullyConstrainedd`, `sketchCurves.sketchPolylines`, an attribute on the wrong receiver, and
the module `adsk.geometry`.

### ⚠ The gate fails OPEN — this is the most important fact in this document

**A malformed `pyrightconfig.json` does not stop pyright. It prints one line to *stderr*,
falls back to default settings, and exits normally.** Under defaults, `extraPaths` is lost and
`reportAttributeAccessIssue` weakens.

Reproduced independently by two agents. The observed consequence: a config with single-backslash
Windows paths (invalid JSON escaping) produced **3 errors instead of 7, and all seven genuine
hallucinations went undetected** — while looking like a clean run.

Consequences, both mandatory:

1. **The config must be generated programmatically** with `json.dump`, never string-templated
   and never hand-maintained.
2. **The gate must run a canary on every invocation** — a known-bad probe it asserts pyright
   flagged. That proves config parse, stub resolution and rule severity together. A `PASS` is
   only meaningful if a known-bad probe simultaneously `FAIL`s.
3. **Three outcomes, not two:** `PASS`, `FAIL`, `GATE_BROKEN`. `GATE_BROKEN` must never be
   reported as a pass.

A gate that can silently stop working is worse than no gate, because it converts "unchecked"
into "checked and clean".

### Required configuration

Two settings are load-bearing:

- **`reportArgumentType: "none"` is not optional.** Fusion enums are plain classes with `int`
  class attributes while parameters are annotated with the enum *class* type, so every enum
  argument raises a false positive and drowns the signal.
- **`include` must name the single staged file, never `["."]`.** Measured: with `["."]`, run in
  a working directory, pyright analysed **4 files and produced 1168 diagnostics** instead of
  1 file and 7. `include` is not overridden by a CLI file argument in all invocation forms, and
  the cost scales with directory size — this makes the gate unusable in a real project.

The working approach is to stage the script into an isolated temp directory (also escaping any
ancestor `pyrightconfig.json` or `pyproject.toml` `[tool.pyright]`) and generate:

```json
{
  "include": ["script.py"],
  "extraPaths": ["<discovered defs path>"],
  "typeCheckingMode": "basic",
  "pythonVersion": "3.14",
  "reportMissingImports": "error",
  "reportAttributeAccessIssue": "error",
  "reportArgumentType": "none",
  "reportSelfClsParameterName": "none"
}
```

`reportSelfClsParameterName: "none"` suppresses noise from Autodesk's stubs declaring
static-looking methods inside classes. With this config: 0 errors on valid code, 7/7 on bad code.

**`pythonVersion` must match Fusion's runtime, which is CPython 3.14** — measured, not assumed
(`sys.executable` is `Fusion360.exe`; `sys.version` reports 3.14.0). An earlier draft pinned 3.12
on the assumption that Fusion shipped it. That is the wrong direction of error: pinning *below*
the runtime makes the gate reject syntax Fusion would happily execute, so a correct script fails
preflight and a repair loop is sent to "fix" working code. Pinning *above* the runtime is the
opposite hazard — it would admit syntax that fails inside Fusion. Match it, or discover it the way
`extraPaths` is discovered.

**Stub sentinel.** After parsing output and before reporting anything, check for
`Import "adsk(\.\w+)? could not be resolved"`. If present, the stub path did not take effect —
report an *environment* error and suppress all other diagnostics, which are noise from an
unresolved import and will send a repair loop chasing phantoms.

### Timing — the real budget is ~2 s, not 0.3 s

Measured wall-clock for a single-file run, warm: **1.6–2.2 s**. The often-quoted 0.3 s is
pyright's self-reported `summary.timeInSec`, which measures analysis only and itself ranges
0.19–1.02 s here. Node process start dominates the difference.

| Stage | Time | Share |
|---|---|---|
| `ast.parse` + all lint rule visitors | ~5 ms | 0.3% |
| Staging (mkdtemp, copy, `json.dump`) | ~2 ms | 0.1% |
| pyright subprocess, wall | 1610–2230 ms | ~99% |

**Publish ≤ 2.5 s.** Against a Fusion round-trip plus a model turn this is noise, but quoting
0.3 s would read as a regression when the real thing ships.

Do **not** try to skip the Python shim by invoking `dist/pyright.js` with node directly — it
resolves a different project root, reports 1168 errors including `"str" is not defined`
(typeshed bootstrap fails), and is *not* faster. Do not re-run `pyright --version` per check
(~900 ms); cache it.

**Cannot catch:** `createByReal` vs `createByString` (both return `ValueInput`), index picks,
hardcoded axes, unbound dimensions. Those need the lint rules.

### Stub gaps (measured 2026-07-28)

The "0 false positives" claim above holds for the SEVEN-hallucination probe set it was
measured against; it is not a blanket guarantee the stub surface is complete. Two live
`hasattr()` checks against a running Fusion session, made while building Task 15's corpus
fixtures:

- **`ExtrudeFeatureInput.setDistanceExtent` → `True` at runtime, absent from the stub for
  that class** (`adsk/fusion.py` declares it only on `HoleFeatureInput`/`HoleFeature`).
  Genuinely valid code; pyright reports `reportAttributeAccessIssue` on it anyway. **This is
  the first confirmed gate false positive in this project.**
- **`Sketch.sketchLines` → `False` at runtime; `SketchCurves.sketchLines` → `True`.** This one
  was not a stub gap — it was a plain transcription error in `api-recipes.md`, and the stub
  was right to reject it.

**Stub-absence is not proof of API-absence.** Before trusting a
`reportAttributeAccessIssue` finding against code that is otherwise documented or was seen
running live, verify with a live `hasattr()` probe (`fusion_mcp_execute`) rather than
assuming the gate is correct by construction — it fails closed on real hallucinations but can
also fail closed on real API surface the stub author didn't transcribe.

**Pyright findings are not waivable through the lint suppression mechanism** (`fusionhelper:
allow <rule>` only recognises the lint rule IDs, R1–R10 — pyright diagnostics are a separate
finding class with no waiver path). A confirmed stub gap therefore forces a code-level
alternative that is both runtime-valid and stub-visible (as `setOneSideExtent` is here), not
a suppression. Whether the gate itself should ever special-case a specific stub gap is a
phase-2 question, not resolved by this note.

---

## 9. Other constraints and gotchas

- **Custom Features are effectively off-limits.** Autodesk's docs: *"This re-compute
  functionality is currently limited to one specific case… should not be used for any other
  cases and will likely fail."* Emit plain native features.
- **Main-thread only.** The MCP handles this; a self-built bridge must marshal via `CustomEvent`.
- **`adsk.doEvents()` on long builds.** One report of 30 components / 200 bodies taking >15
  hours without it. **It is *not* required as a rebuild barrier** — see below.

### Recompute is synchronous on expression assignment

Measured directly:

```
volume before change:              9.000000
volume immediately, NO doEvents:  13.500000   changed=True
volume after doEvents():          13.500000   changed=True
volume after computeAll():        13.500000   further change=False
```

Assigning `param.expression` recomputes the model **before the next statement executes**.
`doEvents()` adds nothing, and `Design.computeAll()` (which does exist) adds nothing further.

This matters for any verification that perturbs a parameter and re-measures: there is no risk
of reading a stale value and wrongly concluding a parameter drives nothing. Keep the
`doEvents()` call anyway — it costs nothing and keeps the UI responsive during a long sweep —
but do not rely on it being what makes the rebuild happen.

**Consecutive expression writes coalesce correctly**, including the interleaved case:

```
two writes, one doEvents:     boxQ2 9.0000 -> 15.0000   boxQ3 9.0000 -> 15.0000   both took effect
restore w2 AND perturb w3 with no settle between:
  boxQ2 restored to baseline exactly:  True  (9.0000)
  boxQ3 moved to its new value:        True  (21.0000)
```

So a parameter sweep that restores parameter *i* and perturbs parameter *i+1* before a single
settle is **safe**. It is not, however, *cheaper* in rebuilds — see below.

### The rebuild is eager, on the write itself

An earlier draft of this document concluded that interleaving made the sweep "N+1 rebuilds
rather than 2N". **That was wrong**, and the error is worth recording because it is an easy one:
"safe to interleave" was conflated with "cheaper to interleave".

The discriminating measurement, on a 6-parameter model with fillets so a rebuild is not trivially
cheap:

```
mean WRITE time (no doEvents, no read):  76.0 ms   per-write: 103, 105, 87, 80, 44, 38
mean READ time (settled model):           0.7 ms

ISOLATED    (2N writes, 2N settles): 1507 ms
INTERLEAVED (2N writes, N+1 settles): 1263 ms
ratio: 1.19
```

A bare `p.expression = ...` costs ~76 ms with nothing else on the line. That *is* the rebuild —
it happens on the assignment, not on the settle and not on the next read (which is 0.7 ms). Since
restore-then-perturb is two writes either way, grouping them under one `doEvents()` cannot remove
a rebuild.

**The sweep is 2N rebuilds and N+1 settles.** Interleaving saves ~19%, which is the `doEvents()`
overhead alone. Worth taking, but it is not a halving.

The reason the earlier reading was seductive: OQ1's test read the volume immediately after the
write with no settle, and saw the new value. A lazy-on-read implementation would produce exactly
the same observation, so that test could not separate the two hypotheses. Only timing the bare
write can.
- **A design must be open** before `fusion_mcp_execute` works.
- **Large sketches freeze the UI.** Named causes: duplicate entities, stacked patterns/mirrors
  in one sketch. Prefer several small sketches to one huge one.
- **STEP import arrives as a `BaseFeature`** — *"a non-parametric island within a parametric
  part… its content never changes as the result of a recompute."* Enabling history afterwards
  does not parameterise it. STEP is an output format, not a handoff format.
- **F3D/F3Z preserve everything but are proprietary** — no third-party writer exists.
- **As-built joints are much easier than geometric joints** — they mate components where they
  already sit, so if occurrences are already correctly placed they are near-free. Geometric
  joints need face references and inherit topological-naming risk.
- One unreproducible `RuntimeError: 3 : invalid expression` occurred in a document polluted
  with ~21 accumulated probe parameters, and did not recur in a clean document. Cause
  unidentified. Practical guard: distinct `snake_case` names, don't accumulate junk parameters.

### Personal licence (not supported in v1, recorded for portability)

| | Personal | Paid |
|---|---|---|
| Scripts / add-ins | Yes | Yes |
| Official Fusion MCP | **No** | Yes |
| STEP export | Yes | Yes |
| Active editable documents | **10** | Unlimited |

Degradation path: identical generated script, delivered by a self-authored watcher add-in
(auto-starts via `runOnStartup` in the manifest, polls a queue folder, marshals onto the main
thread via `CustomEvent`, writes a JSON log). Confirmed working on Personal by an existing
open-source project. The generator is unaffected — same script, different transport.

---

## 10. Recommended verification block

Appended to every generated script. All five verified working and returning via `print()`:

1. `sketch.isFullyConstrained` per sketch; on failure iterate `SketchEntity.isFullyConstrained`
   to name the loose entities.
2. Perturb each user parameter, `adsk.doEvents()`, re-measure bbox and volume, restore.
   **The only check that catches the partially-bound dead-timeline case.**
3. Sweep `timeline.item(i).healthState` and `errorOrWarningMessage`.
4. `analyzeInterference` across body pairs with `areCoincidentFacesIncluded = False`.
5. `measureMinimumDistance` for declared clearances.

Plus the offline pyright gate before the script is ever sent.

---

## 11. Multi-document enumeration (Task 16, measured 2026-07-28)

Backs the scratch-document lifecycle in `docs/detailed-design.md` ("Scratch document
lifecycle"). `tests/integration/scratch.py` creates and cleans up scratch documents this way.

```python
doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
des = adsk.fusion.Design.cast(app.activeProduct)   # the new doc becomes active immediately
des.attributes.add('fusionhelper', 'scratch', tag)
```

Enumerating **every** open document and reading a tag without disturbing which one is active:

```python
for i in range(app.documents.count):
    doc = app.documents.item(i)
    prod = doc.products.itemByProductType('DesignProductType')   # works on a non-active doc
    des = adsk.fusion.Design.cast(prod)
    attr = des.attributes.itemByName('fusionhelper', 'scratch')   # None if untagged
```

`doc.close(False)` closes without saving. Verified against a session with one saved document
open (`isSaved == True`) and one freshly created scratch document: enumerating both, tagging
only the scratch one, and calling `close(False)` on it left the saved document completely
untouched (still open, still `isSaved == True`, no tag) and removed the scratch document from
`app.documents`. `doc.isSaved` is checked before any attribute access in the cleanup sweep, so
a saved document is never even inspected for a tag, let alone closed.

## 11. Live-calibration findings (measured 2026-07-28, trophy-duplicate exercise)

- **Failed `fusion_mcp_execute` calls roll back atomically.** A script exception
  reverts everything the script did — `userParameters.add`, `deleteMe`, feature
  adds. One transaction per call, aborted on error. A crashed attempt therefore
  leaves the document unchanged (timeline marker position excepted).
- **`fusion_mcp_update` takes `{"featureType": "undo"|"redo"}`** — required enum;
  an `operation` key is rejected with "Missing required property 'featureType'".
- **`healthState` 4 = rolled back** (feature beyond the timeline marker). Absent
  from the documented 0–3 range; a document can ship with a deliberately
  rolled-back tail.
- **`timeline.moveToEnd()` activates a rolled-back tail** — it changes the user's
  model state silently. Record and restore `timeline.markerPosition` around any
  history edit. New features insert AT the marker, which is also how a feature
  is replaced in place: `feature.timelineObject.rollTo(True)`, delete, re-add.
- **`addTwoDistancesChamferEdgeSet(edges, d1, d2, isFlipped, isTangentChain)`** —
  five arguments; with both flags False, `d1` is the vertical (face-one) distance
  and `d2` the horizontal. Chamfering a top rim whose horizontal cut would
  intersect a body joined ON that face fails with
  `ASM_BL_UNFIN_SHEET — could not be created at the requested size`; chamfer the
  bare box BEFORE the join (roll the marker back), as the union then covers the
  overlap region.
- **Verify liveness budget**: `fh_verify` samples parameters when the 20 s default
  `liveness_budget_s` runs out (`mode: "sampled"`, `untested` listed). Raise it
  via `FH_OPTS` to cover a large table; 22 params completed in ~4 s once warm.

## 12. Donut-exercise findings (measured 2026-07-28)

- **Enum-typed property SETTERS false-positive in the gate** (second stub-gap
  class): e.g. `CombineFeatureInput.operation` is annotated
  `value: FeatureOperations` while members are ints, and
  `reportArgumentType: "none"` covers call arguments only — assignment surfaces
  as `reportAttributeAccessIssue`. Sanctioned escape: a scoped
  `# pyright: ignore[reportAttributeAccessIssue]` on that line with a reason.
- **`fusion_mcp_execute` REUSES the module namespace across calls** — stale
  globals from earlier scripts leak (`FH_ATTEMPT` from a previous script
  appeared in a later verdict). Always define `FH_ATTEMPT`/`FH_OPTS`/
  `INTERFERENCE_ALLOWED` explicitly in every stub-carrying script.
- **Combine-JOIN of disjoint bodies silently no-ops** — live confirmation of
  detailed-design open question 5 (`boolean.no_op` has no message). A single
  multi-lump body cannot be produced that way.
- **`setByAngle` construction planes have plane-local sketch axes**: seeds via
  `modelToSketchSpace` are not enough — Horizontal/Vertical DIMENSION
  orientations must also be assigned by probing which sketch axis a world
  direction maps to (map a second probe point and compare deltas), else the
  solver relocates geometry to satisfy dims on the wrong axes.
- `fh_verify`'s edit canary now honours `interference_allowed` (declared-intent
  overlaps no longer inflate the before/after clash counts).
- **Circular-patterning a CUT feature around a curved body fails** with
  `NO_TARGET_BODY / PATTERN_FEATURES_NO_PASTE_INT_EDGES` — under both the
  default and `AdjustPatternCompute` options (measured). Workaround: extrude the
  cutter as a NEW-BODY tool, pattern the BODY, then one `combineFeatures` cut of
  all tool bodies (`isKeepToolBodies = False`).
- **`param.dead` can mean a silently MISSING FEATURE**: a mis-bound tool sketch
  (hardcoded diameter expression in a reused helper) built a bite that never
  touched the target — constraints/timeline/interference all passed while the
  intended feature was absent; only liveness flagged the two dead parameters.
- **`MoveFeatures` has no classic `createInput(entities, matrix)`** — use
  `createInput2(entities)` + `defineAsFreeMove(Matrix3D)`. A baked free-move
  (e.g. random yaw about a local normal) survives the edit canary but its
  rotation origin goes ~1 mm stale under a resize — acceptable for aesthetic
  scatter, never for load-bearing placement.
- **Client timeouts vs long builds**: a 260-feature build + verify exceeded the
  harness's old 120 s HTTP timeout while Fusion COMPLETED the script — after a
  client-side timeout, probe document state before re-running (double-build
  hazard). Timeout now 600 s.
- **`FH_OPTS max_bodies`** (default 60) silently skips interference on
  sprinkle-count models — raise it explicitly; and declare body-pair contact
  that is design INTENT (`INTERFERENCE_ALLOWED`, e.g. sprinkle-on-sprinkle
  stacking) rather than easing placement to dodge the check.
- **Expired Autodesk login** (measured 2026-07-29): `initialize` returns 200
  with JSON-RPC error `-32001 "Authentication required: User is not logged
  in"`, and subsequent `tools/call` requests fail as bare HTTP 400. Diagnose
  with a bare initialize; remedy is signing back into Fusion. The harness now
  raises the real cause at initialize.
- **`filletFeatures.add()` can succeed while the feature lands in ERROR
  healthState** (measured 2026-07-28) — no exception; only a timeline health
  sweep catches it. Constant-radius fillets are bounded by the shortest edge in
  the chain: a scalloped drape rim capped out at ~0.8 mm (1.0/1.18/1.43 mm and
  a compounding second pass all failed).
- **Embed depths derive from the thinnest penetrated layer**: seating a rod
  d/4 into a 1 mm shell put its underside 0.65 mm into the body beneath
  (interference caught it). Thickness-proof seat: centre = base + t/2 + d/2.
