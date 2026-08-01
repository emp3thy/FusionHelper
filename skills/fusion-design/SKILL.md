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
   a pre-existing document, see below), `only_params` (scope liveness to YOUR
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
- **A feature add can succeed while the feature lands in error state** —
  `filletFeatures.add()` returned normally with the fillet erroring in the
  timeline. Never trust add() success alone; the timeline health check is
  what catches it. Fillet radii are bounded by the SHORTEST edge in the
  chain (scalloped rims bound at ~0.8 mm by lens-emergence slivers;
  measured fails at 1.0/1.18/1.43 mm and as a compounding second pass).
- **Delete parameters together with their features** — an orphaned
  parameter (feature removed, param left in the table) is correctly
  flagged by liveness as `param.dead`.
- **Derive embed depths from the THINNEST layer penetrated, not from the
  embedded object's size**: a d/4 rod embed cannot fit a shell thinner
  than ~3d/4. The thickness-proof seat is centre = layer_base + t/2 + d/2
  (dips t/2 into the layer, stays t/2 clear of what's beneath, any t).
- **Patch, gate, launch — three separate commands** (measured 2026-08-01):
  a string-replace patch that asserted on a whitespace mismatch still
  relaunched the pipeline because the relaunch was chained in the same
  shell line — a full run of known-stale code. After any scripted edit,
  grep for a symbol the patch introduced before launching anything.
- **Match patch old-strings against CAPTURED on-disk text**, not memory:
  two patch failures came from assumed continuation indentation and a
  stale debug print left in a helper (`cat -A` the exact block first).
  Corollary: strip debug instrumentation the moment its diagnosis is done
  — it poisons every later text match against that function.
- **Verify geometry with measured signatures, not renders.** Screenshots
  cannot show occluded features (interior skirt notches are invisible
  from the front — a "confirming" shot proves nothing). Cheap analytic
  probes are conclusive and scriptable: a per-body volume signature
  (edge covers heavier than interior covers by exactly N notch-volumes)
  or an exhaustive position-vs-bbox clearance sweep. Prefer these as the
  evidence you report.
- **Overlay subsystems get an overlap check at design time**: features
  placed sensibly in isolation (service holes; mounting plates) collided
  on 6 of 8 rows when overlaid. Ten lines of analytic footprint math at
  layout time beats a rebuild. When both collide, relocate the cheap
  feature (holes) rather than weaken the structural one (windowing
  plates).

## Working in an existing document (calibrated live, 2026-07-28)

The five checks sweep the WHOLE document, so a user's pre-existing unconstrained
sketches fail your build's verdict and skip liveness with `prior_failure`. In an
existing document: expect `constraints: fail` from entities you did not create,
read the `FH_CHECK1` sketch names to separate yours from theirs, and re-verify
with `FH_OPTS = {"force_liveness": True, "only_params": [<your params>]}`.

Timeline hazards in someone else's document:
- `healthState 4` = a feature the USER rolled back (deliberate state, not damage).
- **Never call `timeline.moveToEnd()` blindly** — it rolls past and ACTIVATES the
  user's rolled-back tail, changing their model. Record `timeline.markerPosition`
  before any history edit and restore it (marker position is NOT part of the
  script transaction, and verify does not yet detect a moved marker).
- New features insert AT the marker, and `feature.timelineObject.rollTo(True)`
  plus delete/re-add replaces a feature in place — the right way to fix a
  committed-but-wrong feature without rebuilding.

Recovery semantics (measured): a FAILED `fusion_mcp_execute` rolls back
atomically — its parameter adds, deletes, and features all revert, so a crashed
attempt leaves the document as it was. Undo of COMMITTED calls goes through
`fusion_mcp_update` with `{"featureType": "undo"}`. Read-only survey/probe
scripts (gate them with `--no-stub`) do not count against the 5-execute repair
cap — the cap governs build/repair attempts.

Waivers (`# fusionhelper: allow ...`) apply only to the checked lint rules
(R1 R2 R4 R5 R6 R7); waiving R3/R9/R10 always reports "unused suppression"
because nothing fires for them — they are runtime/convention rules.

## Checkpoint versioning (the reset story)

Scripts build from a BASELINE, not from an empty file: v1 = the user's
hand-made parts and nothing else; later checkpoints layer verified script
output on top (v2 = v1 + sub-assembly, v3 = v2 + main build, each saved
only on a green verdict, with consent — see R10). This changes what
"regenerate from zero" costs:

- Architecture change / teardown: NEVER surgically delete generated bodies
  in a live heavy document (measured: ~20-30 s per `deleteMe` in a
  361-feature / 11k-occurrence doc — a wall teardown cost ~40 min).
  Restore the baseline version from the Data Panel and re-run the scripts.
- Never re-run a build script on a document that already contains its
  output — name collisions produce silently coincident " (N)"-suffixed
  duplicate bodies that renders and the current attempt's interference
  check cannot see. Version-restore makes this scenario impossible.
- Parameter-level changes never need a rebuild at all: edit the parameter.

## Heavy documents and transport discipline (measured 2026-07-31)

- **A dead client is NOT a rolled-back script.** A client that times out or
  is killed mid-`fusion_mcp_execute` may leave Fusion to finish and COMMIT
  the script — or abort partway with no rollback. Measured leaks: stepped
  parameters left as `( 5 mm ) + 0.25 mm`, duplicate body sets, and
  half-applied reorganizations. After ANY client timeout: probe before
  re-running (double-build hazard), audit parameter expressions for step
  wrappers, and audit body counts for " (N)" suffixes and unexpected root
  bodies.
- **Orphaned requests still run.** Requests queued by killed clients
  execute in order when Fusion frees up. Never stack retries while Fusion
  is busy; poll with a single patient probe. Distinguish busy from frozen
  from outside: process CPU + `Responding` (a script on the UI thread
  shows a white window while working).
- **Chunk structural operations.** Scripts run on Fusion's UI thread. One
  mega-execute (~250 component ops) froze the UI for an hour; the same
  work as ~20-op executes with `adsk.doEvents()` between batches ran
  invisibly. Chunking also restores atomic-rollback granularity and makes
  client timeouts irrelevant.
- **Instanced-component count dominates every cost.** 60 instances of a
  180-part component (≈11k leaf occurrences) took each verify liveness
  step to ~6 min (snapshot mass-properties) and each body delete to ~30 s.
  Exclude visual-only instanced components from verification with
  `FH_OPTS = {"snapshot_exclude": ["<component name prefix>", ...]}`, and
  scope `only_params` to what the step can actually exercise.
- **Never gate through a pipe.** `preflight | head` masks the gate's exit
  code (pipeline exit = last command) — a FAILED gate let an ungated
  script execute. Check the gate's exit code explicitly, then run.
- **Sketch circles: create jittered.** Circles created at coincident
  coordinates trigger silent alignment inference; the later origin dim
  then over-constrains (`VCS_SKETCH_OVER_CONSTRAINTS`). Create each circle
  at a small unique offset (+0.1-0.3 mm, incremented per circle) and let
  the driving dims snap it home. Rectangles are immune.
- **Patterns: trust nothing, validate topology.** Cut/feature patterns
  need `AdjustPatternCompute` (default dies with
  `PATTERN_FEATURES_NO_PASTE_INT_EDGES`); body patterns reject it.
  Direction sign is unreliable — try flipped distances until validated.
  Validate cut patterns by FACE-COUNT delta on the participants, never by
  `body.volume` (a low-accuracy estimate, measured 24% off on small
  holes); floor at ~4 faces per expected instance, not the seed's count.
- **Loops must breathe (R11, warn).** Any loop that mutates the document
  (add / deleteMe / moveToComponent / addExistingComponent / ...) calls
  `adsk.doEvents()` per iteration — scripts run on the UI thread and an
  unbroken loop freezes the window for its whole duration. The verify
  block breathes on its own (between checks, per liveness step, every 25
  snapshot bodies). Liveness on instanced-heavy documents remains
  budget-limited regardless: each parameter step forces a full document
  recompute that `snapshot_exclude` cannot avoid — expect `sampled` mode
  and say so in the report.
- **After body moves/deletes, check the light bulbs.** Fusion spontaneously
  switches off component/occurrence `isLightBulbOn` after heavy
  reorganizations — geometry looks deleted but is only dark.

## Honest limits

Every check verifies the model against what was *declared*. A green verdict
means: built correctly, stays editable, matches the stated numbers. It does NOT
mean "this is the part you wanted" — that judgement belongs to the human, from
the renders. Say it that way. See `reference/limits.md`.
