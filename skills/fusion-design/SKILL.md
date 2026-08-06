---
name: fusion-design
description: Use when generating Fusion 360 Python for a part the user describes — enforces parametric discipline (named parameters, datums, no raw coordinates), an offline preflight gate before any script reaches Fusion, and a numeric verification block after it runs.
---

# fusion-design

Claude generates Fusion 360 Python that Fusion executes without error and that is
still wrong — misplaced, dimensionally drifted, or dead on the first parameter
edit — and **Fusion will not tell you**. A bracket 40 mm out of position and
embedded in its plate reports zero errors (probe P5). This skill exists to make
those failures inexpressible or unmissable.

## The ten standing rules

Every rule traces to a measured probe. The gate cites rules by number.

- **R1** Never `ValueInput.createByReal` — `createByString`, always. A genuinely
  non-parametric constant is `createByString('3')`.
- **R2** Every `sketchDimensions.add*` is followed by
  `<dim>.parameter.expression = '<param>'`. An unbound dimension is silently dead.
- **R3** Apply geometric constraints first, check `sketch.isFullyConstrained`,
  then dimension only the residual. Over-constraint raises *before* mutating —
  attempt-and-recover is safe.
- **R4** Never select topology by index (`faces[4]`, `edges.item(2)`). Use a
  geometric predicate or capture `entityToken` and re-resolve. Index picks break
  when face count changes, silently.
- **R5** Never reuse a held BRep object across ANY parameter write — it is dead
  document-wide (`InternalValidationError`). Re-resolve by token.
- **R6** Never hardcode axis vectors or assume the plane table. Derive mapping
  from `sketch.sketchToModelSpace()` at runtime. (XZ inverts: world_z = −sketch_y.
  Diagnosis only: `reference/axis-mapping.md` — never compute placement from it.)
- **R7** Parameter names: multi-character `snake_case` (`outer_w`, `wall_t`).
  Fusion rejects unit symbols, function names AND duplicates with the same
  misleading message.
- **R8** Every generated script ends with the verification stub, appended by
  `fusionhelper.verify.append_to()`, unmodified, last in the file. Not waivable —
  the finding sits past the last line, so there is no line to attach a suppression
  to; regenerate the tail instead.
- **R9** Never catch exceptions in generated scripts. The traceback is the
  diagnostic (Autodesk's own guidance).
- **R10** Never save the document on your own judgement. Two sanctioned
  exceptions, both user-driven: (a) at session start, if the active document
  is UNSAVED and carries user-authored geometry, refuse to execute anything
  until the user has saved once — an unsaved kit is one crash from gone;
  (b) with the user's standing consent for the document, checkpoint-save
  (`document.save("checkpoint: <milestone>")`) ONLY after a green verdict.
  Fusion cloud docs are fully versioned — every save is a new version and
  old versions restore from the Data Panel, which is what makes (b) safe.

Waivers (`# fusionhelper: allow ...`) apply to the checked rules
(R1 R2 R4 R5 R6 R7 R9 R10 R11). R3 is a runtime rule — nothing fires, so
waiving it reports "unused suppression". R8 is not waivable by design.
Checkpoint saves are the sanctioned R10 waiver: state the user's consent in
the reason.

## Workflow (phase 1)

1. **Parameter table first.** Named `snake_case` user parameters before any
   geometry; derived values as expressions (`wall_t = outer_w / 20`). One value,
   stated once, referenced thereafter.
2. **Named datums.** Construction planes at parameter-bound offsets, named.
   Layout major masses against datums; fillets/chamfers last and minimal.
3. **Generate** the script per `reference/api-recipes.md` (read the section you
   need at the moment of use — do not carry the whole file).
4. **Append the stub:** `python -c "from pathlib import Path; from fusionhelper import verify; p=Path('box.py'); p.write_text(verify.append_to(p.read_text(encoding='utf-8')), encoding='utf-8')"`
   — and ensure the block is installed once per machine:
   `python -c "from fusionhelper import verify; print(verify.install_block())"`.
   Buildkit-importing scripts skip this step — the bundler owns the stub; see
   the Buildkit workflow section below.
5. **Gate:** `python -m fusionhelper.preflight box.py`
   - exit 0 PASS → send to Fusion
   - exit 1 FAIL → fix the script (findings cite rule numbers). A pyright attribute error on a
     call you have verified live may be a **STUB GAP**, not a hallucination — check
     `reference/api-recipes.md` (the `setDistanceExtent` precedent) before editing; lint
     suppressions do not apply to pyright findings — the sanctioned per-line escape for a
     verified stub gap is `# pyright: ignore[<rule>]` with a reason comment. Enum-typed
     property SETTERS (e.g. `CombineFeatureInput.operation`) are a known stub-gap class.
   - exit 3 GATE_BROKEN / environment → fix the machine. **Do not edit the script.**
     Same class at execute time: an expired Autodesk login answers `initialize` with
     JSON-RPC `-32001` and later calls fail as bare HTTP 400 — sign back into Fusion;
     never edit the script for an environment failure.
6. **Execute** via the official Fusion MCP (`fusion_mcp_execute`,
   `featureType: "script"`). The stub prints one `FH_VERDICT1 {...}` JSON line.
7. **Verify:** parse the verdict — AND the `FH_CHECK1 {...}` lines above it: the
   verdict carries only check statuses and hint codes; the per-finding detail
   (which sketch, which entities, which parameter) is in the `FH_CHECK1` lines.
   `pass` → render screenshots *for the user* (renders are for the human —
   numeric read-back is the oracle, not your eyes). Anything else → repair loop.
   Verify options go in module globals: `FH_OPTS = {...}` before `run`, keys:
   `force_liveness` (run liveness even after a cheap-check failure — essential in
   a pre-existing document, see `reference/hazards.md`), `only_params` (scope liveness to YOUR
   parameters), `liveness_budget_s` (default 20 s samples large tables — raise it
   to cover every parameter), `liveness: False`, `canary`, `max_bodies`.
8. **Repair loop.** Budgets: preflight fixes 3 (offline, separate); runtime with
   a taxonomy code 3; unclassified runtime 2; verification failures 2; hard cap
   **5 `fusion_mcp_execute` calls per request**. Abort early when: identical failure signature twice;
   an A→B→A recurrence appears; error count fails to strictly decrease twice;
   a repair introduces a new error code without clearing the old one (counts as no progress).
   Third attempt is always a from-scratch regeneration, never a patch.
   `model.not_restored`, `model.inert`, `edit.introduces_clash`, or a timeline error state → undo
   (`fusion_mcp_update`) and regenerate.
9. **When giving up:** say what is wrong in plain language, show the attempt
   history, state the document's condition, ask one specific question, and
   attach a render.
10. **Record telemetry** (final act, pass or give-up):
    `python -m fusionhelper.telemetry record --script <file> --verdict pass|fail|abandoned --executes <n> --preflight-attempts <n> --rules-fired R2,R4`
    — one line per part request. `python -m fusionhelper.telemetry summary`
    prints the green-on-first-execute rate this skill is judged by.

## Buildkit workflow

- Buildkit workflow: author scripts import `from fusionhelper.buildkit
  import *` and contain no stub; `python -m fusionhelper.bundle` expands
  the kit and appends the stub; preflight/lint gate the BUNDLED artifact
  and the artifact is what is sent. After editing an author script:
  re-bundle, grep the artifact for the edited symbol, then launch.

## Script hygiene (measured)

`fusion_mcp_execute` REUSES the Python namespace across calls: stale globals
from earlier scripts leak into later ones. Define `FH_ATTEMPT`, `FH_OPTS`,
and `INTERFERENCE_ALLOWED` explicitly in every stub-carrying script. On
`setByAngle` datum planes, derive DIMENSION orientations the same way as
seeds: probe a second mapped point to learn which sketch axis is which —
H/V dims assigned to the wrong plane-local axes relocate geometry silently.

More measured rules:
- `filletFeatures.add()` can return success while the fillet errors in the
  timeline — never trust add() alone, check timeline health. Fillet radii
  are bounded by the SHORTEST edge in the chain (scalloped rims bound at
  ~0.8 mm; measured fails at 1.0/1.18/1.43 mm and as a compounding second
  pass).
- Delete parameters together with their features — an orphaned parameter
  is correctly flagged by liveness as `param.dead`.
- Derive embed depths from the THINNEST layer penetrated, not from the
  embedded object's size: a d/4 rod embed cannot fit a shell thinner than
  ~3d/4. Thickness-proof seat: `centre = layer_base + t/2 + d/2`.
- Patch, gate, launch are three separate commands (measured 2026-08-01) —
  chaining them in one shell line let a stale relaunch hide a patch
  assertion failure. Grep for a symbol the patch introduced before
  launching anything. Match patch old-strings against CAPTURED on-disk
  text, not memory (`cat -A` the exact block); strip debug instrumentation
  the moment its diagnosis is done — it poisons later text matches.
- Verify geometry with measured signatures, not renders — screenshots
  cannot show occluded features. Use a per-body volume signature (edge
  covers heavier than interior covers by exactly N notch-volumes) or an
  exhaustive position-vs-bbox clearance sweep.
- Overlay subsystems get an overlap check at design time: features placed
  sensibly in isolation collided on 6 of 8 rows when overlaid. Ten lines
  of analytic footprint math at layout time beats a rebuild; when both
  collide, relocate the cheap feature (holes), not the structural one.
- Never gate through a pipe — `preflight | head` masks the gate's exit
  code (pipeline exit = last command). Check the exit code explicitly.
- Sketch circles: create jittered. Coincident-coordinate circles trigger
  silent alignment inference and later over-constrain
  (`VCS_SKETCH_OVER_CONSTRAINTS`). Offset each circle +0.1-0.3 mm,
  incremented, and let driving dims snap it home. Rectangles are immune.
- Patterns: cut/feature patterns need `AdjustPatternCompute` (default dies
  with `PATTERN_FEATURES_NO_PASTE_INT_EDGES`); body patterns reject it.
  Direction sign is unreliable — try flipped distances until validated.
  Validate cut patterns by FACE-COUNT delta, never `body.volume` (measured
  24% off on small holes); floor at ~4 faces per expected instance.
- Chunk structural operations: a ~250-component-op mega-execute froze the
  UI for an hour; the same work as ~20-op executes with `adsk.doEvents()`
  between batches ran invisibly (also restores atomic-rollback
  granularity). R11 (warn): any loop that mutates the document (`add` /
  `deleteMe` / `moveToComponent` / `addExistingComponent` / ...) calls
  `adsk.doEvents()` per iteration — on a 500+ entity sketch loop that
  itself becomes the bottleneck, so batch to roughly every 20 entities.
  Mechanism and cadence detail: `reference/hazards.md` under "Heavy
  documents".
- A distance dimension is UNSIGNED — never let its expression evaluate
  negative; Fusion snaps geometry to the positive distance, sliding the
  feature sideways by twice the half-size (measured: `buildkit.bound_rect2`
  emitted `0 mm - (9.65 mm)` and landed a full width off). Fixed in kit v2
  by wrapping corner expressions in `abs( … )`. Probe first if you emit a
  computed expression that could go negative.
- Preserve the SIGN when rewriting a committed extent — `blind_cut` encodes
  cut direction as a negative distance (`-( expr )`); a positive rewrite
  flips the cut into air (`No target body`). Read `ext.distance.expression`,
  detect a leading `-`, re-wrap.
- Liveness steps EVERY root parameter at once — a clearance stack of
  literals survives one-at-a-time probing but clashes under the combined
  step. Derive the stack (`14 mm - floor - ceiling - 0.5 mm`); where
  downstream geometry is fixed art, pin the far face (`11 mm - base_t`)
  instead of parameterising the height.
- A revolve/extrude cut profile truncated at a parametric surface leaves an
  uncut ring when that parameter grows — overshoot the nominal surface.
- Check a volume delta on every feature — a JOIN whose start extent leaves
  a gap to its target adds zero volume and returns success silently.
- `isFixed` on a curve does NOT fix its points — fixed-art sketches must
  sweep `sketch.sketchPoints` too, or verify reports `sketch.unconstrained`.
- Grouping bodies into a component: collect them into a Python list first
  (`moveToComponent` mutates `root.bRepBodies`, live iteration drops
  bodies), then compare the sorted name set and total volume before/after.
- Auditing overhangs is scriptable: sample face normals via
  `face.evaluator.getNormalsAtParameters(<list of Point2D>)` and flag any
  `normal.z < -0.7075` (steeper than a 45° overhang), skipping faces on
  z=0. Renders cannot show this; the sweep found every one.

## When something is off, read the hazard file

Symptom-triggered lore lives in `reference/hazards.md` — read the section
your symptom names, not the whole file:
- pre-existing document (constraints fail you didn't cause, prior_failure,
  someone else's timeline, healthState 4) → "Working in an existing document"
- teardown / rebuild / duplicate " (N)" bodies → "Checkpoint versioning"
- client timeout, orphaned request, busy-vs-frozen, instanced-heavy cost,
  geometry gone dark (light bulbs) → "Heavy documents"
- `param.dead` on a parameter you believe is live → "Editing a committed model"

## Honest limits

Every check verifies the model against what was *declared*. A green verdict
means: built correctly, stays editable, matches the stated numbers. It does NOT
mean "this is the part you wanted" — that judgement belongs to the human, from
the renders. Say it that way. See `reference/limits.md`.
