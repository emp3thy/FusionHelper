# FusionHelper — Probe Results

Empirical probes run against a live Autodesk Fusion 360 install via the official
Fusion MCP server, to decide FusionHelper's architecture from measurement rather
than from literature inference.

- **Date:** 2026-07-27
- **Fusion API version:** 2703.1.20
- **MCP endpoint:** `http://127.0.0.1:27182/mcp` (`MCP Server Adapter v1.0.0`, protocol `2025-06-18`)
- **Method:** `fusion_mcp_execute` with `featureType: "script"` — arbitrary Python against the live Fusion API
- **Constraints honoured:** scratch documents only; the user's `claude trophy v5` document was never modified or saved; nothing saved.

---

## P1 — Does a generated script build a genuinely parametric model?

**Verdict: PASS**

Built a plate with three named user parameters (`plate_w`, `plate_d`, `plate_t`), all
created with `ValueInput.createByString`, a constrained sketch, and an extrude whose
extent is bound to `plate_t`.

Then edited the parameters and recomputed:

```
before: bbox=(6.0000, 4.0000, 0.5000)  vol=12.0000
plate_w: "60 mm" -> "80 mm"
plate_t: "5 mm"  -> "8 mm"
after:  bbox=(8.0000, 4.0000, 0.8000)  vol=25.6000
EXPECT: bbox=(8.0000, 4.0000, 0.8000)
width rebuilt correctly:     True
depth unchanged as expected: True
thickness rebuilt correctly: True
timeline features: 2  unhealthy: 0
```

**Findings**

- A generated script produces a real parametric model with a live timeline that
  rebuilds correctly on parameter edit.
- `ValueInput.createByString('plate_t')` binds the extrude extent to the parameter
  and survives the edit.
- **The model rebuilt correctly even though the sketch was never fully constrained.**
  `isFullyConstrained` is therefore a *risk indicator*, not a correctness gate — a
  distinction that matters for how the gate should be reported to the user.
- `addTwoPointRectangle` produced **zero** geometric constraints. The UI silently
  infers horizontal/vertical/perpendicular while drawing; the API infers nothing.
  Four independent lines that merely look like a rectangle.

---

## P2 — Does `isFullyConstrained` work as a gate?

**Verdict: PASS**

Applied constraints incrementally to a fresh rectangle, reading the flag at each step:

```
step0 rect drawn:        fullyConstrained=False  geom=0  dims=0
step1 origin pinned:     fullyConstrained=False  geom=1
step2 H/V applied (2H,2V): fullyConstrained=False  geom=5
step3 width dim:         fullyConstrained=False  dims=1
step4 depth dim:         fullyConstrained=True   dims=2
```

**Findings**

- The flag transitions `False -> True` at exactly the point the last degree of
  freedom is removed. It is a usable, machine-checkable gate.
- DOF arithmetic confirmed: rectangle corners are **shared** sketch points
  (8 endpoint slots resolve to 4 unique points, `sketchPoints.count == 5`
  including the origin), so 8 DOF. Coincident-to-origin removes 2, two horizontal
  plus two vertical constraints remove 4, two dimensions remove 2. Zero remain.

**Working recipe for a fully-constrained rectangle**

1. `sketchLines.addTwoPointRectangle(...)`
2. `geometricConstraints.addCoincident(corner, sketch.originPoint)`
3. `addHorizontal` on both horizontal lines, `addVertical` on both vertical lines
4. Two `addDistanceDimension` calls, each bound via `dim.parameter.expression = '<param>'`

---

## P3 — What is the safe constraint-then-dimension sequence?

**Verdict: PASS**

Deliberately over- and mis-constrained an already fully-constrained sketch.
(Exceptions were caught in this probe only, because characterising the failure *is*
the test.)

| Case | Result |
|---|---|
| Redundant dimension | `RuntimeError: 3 : Already has same dimension on referenced geometry!` |
| Redundant geometric constraint | `RuntimeError: 3 : failed to create offset: Constraint has already been applied to the selected sketch object.` |
| Conflicting constraint (vertical on a horizontal line) | `RuntimeError: 3 : failed to create offset: VCS_SKETCH_SOLVING_FAILED - Failed to solve. Please try revising dimensions or constraints.` |

State after all three failures:

```
fullyConstrained=True
sketch healthState=0  msg=
unhealthy timeline features: 0
```

**Findings**

- **Over-constraint is fail-safe.** All three raise *before* mutating; the sketch was
  left fully constrained and healthy. The generator can attempt-and-recover rather
  than having to predict DOF perfectly in advance.
- The three failure modes carry **distinguishable messages**, so they can drive a
  remediation table (redundant vs conflicting need different responses).
- Safe sequence: apply geometric constraints first, check `isFullyConstrained`, then
  add dimensions only while it still reads `False`.

---

## P4 — Do index-picked faces break where named/durable references survive?

**Verdict: PASS**

Two edits against the same block, tracking a captured reference to the top face.

**Edit A — dimensional only** (`w` 60→95 mm, `t` 10→25 mm):

```
faces whose index now points at a DIFFERENT orientation: 0
entityToken round-trip after rebuild: found=True ... still the TOP face=True
```

**Edit B — topological** (added a chamfer; face count 6 → 7):

```
captured face[4]: area=38.0   normal=(0.0,0.0,1.0)   <- the TOP face
face[4] now:      area=9.955  normal=(-1.0,0.0,0.0)
INDEX PICK still points at the same face orientation: False
ENTITY TOKEN resolves after topology change: True ... still TOP=True
GEOMETRIC PREDICATE finds top face at index 5 (was 4)
```

| Edit type | Index pick | `entityToken` | Geometric predicate |
|---|---|---|---|
| Dimensional | survives | survives | survives |
| **Topological (face count changes)** | **breaks** | survives | survives |

**Findings**

- The common claim that index picks always break on parameter change is **too broad**.
  Pure dimensional edits left all six face indices stable.
- The actual trigger is a **change in face count**. After the chamfer, `face[4]`
  silently became a different face with a different orientation — a shell or fillet
  authored against it would cut the wrong face.
- `entityToken` survived both edit classes and resolved via
  `Design.findEntityByToken()` to the correct face.
- Selection by geometric predicate (normal direction) survived both and correctly
  tracked the top face from index 4 to index 5.

**Generator rule:** never select topology by index. Use `entityToken` for references
that must persist, or re-derive by geometric predicate at authoring time. The risk is
proportional to how much a feature changes face count, not to parameter edits as such.

---

## P5 — Datums + parameters vs raw coordinates

**Verdict: PASS** — the decisive probe.

The same bracket was built twice on the same plate, in one document:

- **BracketA — raw coordinates.** Placement plane offset by `ValueInput.createByReal(1.0)`,
  sketch rectangle at literal coordinates, extrude depth `createByReal(2.0)`. No
  constraints, nothing bound to a parameter. This is what an LLM produces naturally:
  it computes where things go from the current values and writes the numbers down.
- **BracketB — named datum + parameter-bound dimensions.** Placement plane offset by
  `ValueInput.createByString('plate_t')`, fully-constrained sketch, every dimension
  bound to an expression (`plate_w`, `brk_w`, `plate_d - brk_w`), extrude bound to `brk_h`.

At build time both were **identical and correct** — both seated on the plate top at
`z=1.00`, both flush with its right edge at `x=10.00`.

Then `plate_w` 100→140 mm and `plate_t` 10→18 mm:

```
Plate    x=[0.00,14.00] z=[0.00,1.80]   (right edge x=14.00, top z=1.80)
BracketA x=[8.00,10.00] z=[1.00,3.00]   <- raw coordinates
BracketB x=[12.00,14.00] z=[1.80,3.80]  <- datum + params

alignment to plate RIGHT EDGE:  BracketA off by 40.0 mm   BracketB off by 0.0 mm
seating on plate TOP FACE:      BracketA off by 8.0 mm    BracketB off by 0.0 mm

timeline features=8  UNHEALTHY=0
```

**Findings**

- The raw-coordinate bracket ended **40 mm off the edge and 8 mm sunk into the plate** —
  embedded in the material it was supposed to sit on.
- The datum bracket was off by **0.0 mm on both axes**.
- **Fusion reported zero errors.** No feature failed, nothing warned. The defect is
  entirely silent and would survive a visual check from an unlucky angle.
- This is the core justification for the discipline layer: it is not that raw
  coordinates are harder to get right, it is that when they go wrong *nothing tells you*.

---

## P7 — Does `analyzeInterference` report clash volume?

**Verdict: PASS**

Run against the P5 model immediately after the parameter edit, where BracketA had
become embedded in the plate:

```
interference result count: 1
CLASH: Plate vs Body2  volume=3.2000 cm3
```

**Findings**

- `Design.createInterferenceInput(collection)` → `Design.analyzeInterference(input)`
  works on the live model and correctly attributed the clashing pair.
- `InterferenceInput.areCoincidentFacesIncluded = False` is essential — otherwise
  legitimately touching faces (a bracket correctly seated on a plate) read as
  interference.
- The interference oracle caught exactly the defect the timeline was silent about.
  **Numeric verification detected what the application's own error reporting did not.**
- `createInterferenceInput` raises `RuntimeError: 3 : invalid input collections` when
  given fewer than two bodies — guard the call.

---

## P6 — Does a named parameter table prevent repeated literals?

**Verdict: PASS**

Four holes created in one sketch, every diameter dimension bound to the single
parameter `hole_d`:

```
hole0 expression="hole_d" value=8.00 mm
hole1 expression="hole_d" value=8.00 mm
hole2 expression="hole_d" value=8.00 mm
hole3 expression="hole_d" value=8.00 mm
--- single edit: hole_d 8mm -> 13mm ---
hole0 now 13.00 mm   hole1 now 13.00 mm   hole2 now 13.00 mm   hole3 now 13.00 mm
all four followed one edit: True
```

**Findings**

- One edit propagated to all four features. There is no opportunity for drift because
  the value is stated once and referenced, never restated.
- Contrast with the real-world failure observed in the user's own `claude trophy v5`
  document: parameters `d18`, `d19`, `d20`, `d21` each independently holding `"15 mm"` —
  one design intent expressed four times, so editing one does not move the others.
- "Parameters holding a bare literal: 5 of 12" is the expected shape, not a failure:
  the four **root** parameters legitimately hold literals; everything downstream
  references them by name.

---

## P8 — Does a parameter sweep surface errored features?

**Verdict: PASS, with an important limitation**

Each parameter was driven to an extreme, the timeline scanned for unhealthy features,
then the baseline restored.

| Configuration | Result |
|---|---|
| `hole_d = 30 mm` | healthy |
| `hole_d = 60 mm` (holes exceed sensible spacing on an 80 mm plate) | healthy |
| `plate_t = 0.4 mm` | healthy |
| `plate_w = 30 mm` (plate narrower than the hole pattern) | **ERRORED** — `HoleCuts`: *"The extrusion profile falls outside the boundary of the selected body… 2 Reference Failures"* |

**Findings**

- The sweep does surface latent defects invisible at nominal values, and the error
  message is specific enough to act on (it names the feature and the cause).
- **Only 1 of 4 extreme configurations was caught.** Fusion tolerated 60 mm holes on an
  80 mm plate and a 0.4 mm plate thickness without complaint.
- Therefore: a parameter sweep detects **reference failures** — geometry that can no
  longer be constructed. It does **not** detect geometry that is constructible but
  absurd. Those need separate assertions (minimum wall thickness, edge distance,
  clearance) checked against declared intent.
- This is the same lesson as P5 from a different direction: Fusion's own health
  reporting is an incomplete oracle, and independent numeric checks are required.

---

## Status — all probes complete

| Probe | Verdict | Key result |
|---|---|---|
| P1 parametric rebuild | **PASS** | Generated scripts produce genuinely parametric models |
| P2 `isFullyConstrained` gate | **PASS** | Flips `False`→`True` exactly when the last DOF is removed |
| P3 safe constraint sequence | **PASS** | Over-constraint is fail-safe; three distinguishable errors |
| P4 durable vs index references | **PASS** | Index picks break on *topology* change, not dimensional change |
| P5 datums vs raw coordinates | **PASS** | 40 mm / 8 mm drift vs 0.0 mm — and Fusion reported no error |
| P6 parameter table | **PASS** | One edit propagated to all four features |
| P7 `analyzeInterference` | **PASS** | 3.2 cm³ clash correctly detected and attributed |
| P8 parameter sweep | **PASS** | Catches reference failures, not absurd-but-constructible geometry |

## What this means for the design

1. **The discipline layer is validated empirically, not by analogy.** P5 is the whole
   argument: identical output at build time, 40 mm divergence after one edit, and no
   error raised either way.
2. **Silent failure is the dominant risk.** In P5 and in three of four P8 sweeps, Fusion
   built wrong or nonsensical geometry and reported perfect health. Any verification
   that relies on Fusion's own error reporting is insufficient by construction.
3. **The numeric oracles work and are cheap.** `isFullyConstrained`, `analyzeInterference`,
   and bounding-box assertions each caught something the timeline did not.
4. **Generator rules now have evidence behind them:** never `createByReal`; never select
   topology by index; bind every dimension to a named parameter; apply geometric
   constraints before dimensions and check the gate between them.
5. **An external constraint solver was not needed for any of this.** Every result above
   came from Fusion's own solver plus disciplined script generation — consistent with the
   research finding that the cheap structural intervention outperforms the expensive one.

---

# Addendum — independent second run

A parallel set of experiments was run in separate scratch documents. Findings below were
re-verified directly rather than accepted as reported.

## Reconciled conflict: do index picks reorder?

The second run reported that it **could not** reproduce an index-reordering failure —
face count stayed constant at 12 across its rebuilds, and it concluded "avoid index picks"
was prudent rather than proven.

This does not contradict P4; it confirms the same boundary from the other side. That run
only performed **dimensional** edits, which P4 also found safe. P4 forced a **topology**
change (a chamfer, face count 6 → 7) and the index pick broke immediately: `face[4]` went
from the top face (area 38.0, normal `+Z`) to a side face (area 9.955, normal `−X`).

**Resolution: index picks survive dimensional edits and break when face count changes.**
Both runs agree once the edit class is distinguished. The rule stands, with a precise trigger.

## New finding — per-entity constraint diagnostics

There is **no degrees-of-freedom API** in Fusion (searched across 888 classes in
`fusion.py` and 339 in `core.py`; `isFullyConstrained` appears at exactly three sites).
But `SketchEntity.isFullyConstrained` exists alongside the sketch-level flag, and gives
per-entity resolution. Verified:

```
per-line states (unconstrained rect): [False, False, False, False]
per-line states (after H/V+origin):   [True, False, False, True]
LOOSE ENTITIES pinpointed by index: [1, 2]
```

This matters for the design: a count is not actionable, but naming the specific loose
entities is. It removes the main reason to mirror the constraint system into an external
solver purely to obtain diagnostics.

## New finding — sketch-plane axis inversion, measured

Via `sketch.sketchToModelSpace()` on this install:

| sketch plane | sketch +X → world | sketch +Y → world |
|---|---|---|
| XY | `(1, 0, 0)` | `(0, 1, 0)` |
| **XZ** | `(1, 0, 0)` | **`(0, 0, −1)`** |
| **YZ** | **`(0, 0, −1)`** | `(0, 1, 0)` |

**Rule: on the XZ plane `world_z = −sketch_y`; on YZ `world_z = −sketch_x`.** Geometry drawn
"upright" on XZ lands inverted in world Z. This is the discrepancy two public Fusion MCP
repos disagreed about — now measured directly.

`app.preferences.generalPreferences.defaultModelingOrientation` reads **0 (YUp)** on this
machine, yet the construction planes still measured as tabled above. The preference did not
remap the API planes in this configuration. ZUp was not tested (it would mean changing a
user preference). **Generator policy: derive placement from `sketchToModelSpace()` at
runtime rather than hardcoding this table.**

## New finding — BRep objects die across a rebuild

```
held BRepFace after rebuild: DEAD -> RuntimeError: 2 : InternalValidationError : asmFace
token re-resolve after rebuild: found=True
```

A `BRepFace` held in a Python variable is invalid after a parameter change. (The second run
saw the same class of error with a slightly different suffix — `pFace` — so the message
text varies; match on `InternalValidationError`, not the suffix.) Capture `entityToken`
before the rebuild and re-resolve with `Design.findEntityByToken()` afterwards.

## New finding — the dead-timeline trap, distinct from P5

The second run reproduced a failure P1 and P5 did not cover: a profile drawn with literal
`Point3D` coordinates where **only the extrude extent** was bound to a parameter. Changing
the width parameter produced *zero* change — identical volume to four decimal places, all
12 faces byte-identical.

So there are two separate ways to get a dead model, and they need different rules:

1. **Nothing bound** (P5's BracketA) — geometry drifts out of position on edit.
2. **Partially bound** — the model looks parametric, some parameters work, and the
   unbound dimensions silently do nothing.

**Rule: geometry is parameter-driven only where a sketch dimension exists *and* its
`.parameter.expression` names a parameter.** Literal `Point3D` values are seed positions
only. Neither eye nor pyright can detect the partial case — only perturbing each parameter
and re-measuring will.

## New finding — the solver snaps sloppy seeds to exact

A deliberately jittered, non-axis-aligned profile seeded at
`(0.1,−0.2) → (4.3,0.15) → (4.1,2.4) → (−0.2,2.6)` resolved after constraining to exactly
`(0,0) → (4,0) → (4,2.5) → (0,2.5)`.

This directly supports the seed-then-constrain architecture: **the generator's coordinates
only need to be approximately right.** Fusion's solver places the geometry exactly. Small
arithmetic error in the generated seed is harmless, which removes much of the motivation
for computing exact coordinates externally.

## New finding — parameter naming traps

`userParameters.add()` throws `RuntimeError: 3 : param name is not valid` for unit symbols
(`W`, `H`, `R`, `T`, `mm`, `in`, `deg`), function and constant names (`PI`, `abs`, `cos`,
`min`, `if`), malformed names (`0box`, `box w`, `box-w`) — **and for duplicates, with the
same misleading message**. Naming is case-sensitive: `W` is rejected while `w` is accepted;
`PI` rejected, `pi` accepted.

**Generator policy: multi-character `snake_case` names (`outer_w`, `wall_t`), which avoids
the entire class.** Also avoid accumulating junk parameters — one unreproducible
`RuntimeError: 3 : invalid expression` occurred in a document polluted with ~21 probe
parameters and did not recur in a clean document. Cause unidentified.

## New finding — a cut with zero body overlap fails silently, not with P8's documented error

Measured 2026-07-28, while building Task 17's regression test for P8: a sketch-circle profile
cut with `ExtrudeFeatures.createInput(..., CutFeatureOperation)` and a fixed
`DistanceExtentDefinition` does **not** reproduce P8's documented `"extrusion profile falls
outside the boundary of the selected body… N Reference Failures"` error when the profile has
zero overlap with the target body. It silently no-ops instead — boolean subtraction of nothing
from a body — leaving the timeline healthy and the plate unmodified. No exception, no
`healthState` change, no message.

To reproduce a genuine reference failure when a hole's position leaves the target body, the
regression test uses Fusion's dedicated Hole feature instead (`root.features.holeFeatures`,
`createSimpleInput` + `setPositionBySketchPoints` + `setAllExtent`), which explicitly validates
hole placement against the target body at build time and does raise a reference failure
(`healthState=1`, message containing `"Reference Failures"`) when a hole falls off the edge.
See `tests/integration/probe_scripts.py`'s `P8_PARAMETER_SWEEP` for the working recipe.

**This is not a transcription error being corrected — it is new evidence for the document's own
thesis.** P5 and P8's original findings are both about Fusion's health reporting being an
incomplete oracle; this adds a second, sharper instance: not just "some invalid geometry passes
silently" but "the *same conceptual operation* (a cut) can either raise a reference failure or
silently no-op depending on which of two APIs constructs it," with no message distinguishing the
two outcomes from the caller's side. `detailed-design.md`'s open question 5 — *"`boolean.no_op`
has no message and must be detected by post-condition (pre/post volume), which requires an
`emit` assertion"* — predicted exactly this failure mode before it was measured.

**Generator implication:** a boolean/cut operation's success cannot be inferred from the absence
of a timeline error. Where a cut's completeness matters (e.g. "this hole must actually remove
material"), assert a post-condition — pre/post volume or face-count change — not just
`healthState`.

## Recommended verification block for generated scripts

Every item below is verified working and returns to the agent via `print()`:

1. `sketch.isFullyConstrained` per sketch; on failure iterate `SketchEntity.isFullyConstrained`
   to name the loose entities
2. perturb each user parameter and re-measure bbox/volume — **the only thing that catches the
   partially-bound dead-timeline case**
3. sweep `timeline.item(i).healthState` and `errorOrWarningMessage`
4. `analyzeInterference` across body pairs with `areCoincidentFacesIncluded = False`
5. `measureMinimumDistance` for declared clearances

Plus the offline pyright gate against Autodesk's shipped stubs before the script is ever sent
to Fusion (7/7 hallucinated-API defects caught, 0 false positives, ~2 s).

> **Two corrections established after this document was first written — see
> [`fusion-api-notes.md`](fusion-api-notes.md) §8.**
>
> - **Timing: ~2 s, not ~0.3 s.** Measured wall-clock is 1.6–2.2 s; the 0.3 s figure was
>   pyright's self-reported analysis time and excludes node process start.
> - **The gate fails OPEN.** A malformed `pyrightconfig.json` makes pyright fall back to
>   defaults and exit *normally* — 3 errors instead of 7, all seven genuine hallucinations
>   undetected, while looking like a clean run. The config must be generated programmatically,
>   and every invocation must run a canary proving the gate is live. `"include": ["."]` is a
>   live bug (4 files / 1168 diagnostics instead of 1 / 7); stage into an isolated temp dir.
